import logging
import re
from typing import AsyncIterator, Dict, Optional, Tuple

import httpx

from app.domain.contracts.streaming import AudioTransport, UpstreamAudio
from app.domain.errors import UpstreamTimeoutError, UpstreamUnavailableError
from app.domain.models.stream import StreamSource

logger = logging.getLogger("rythmx.stream")

_SINGLE_RANGE_RE = re.compile(r"^bytes=(\d+)-(\d*)$")
_CONTENT_RANGE_RE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


def build_http_client(
    *,
    http2: bool,
    connect_timeout: float,
    read_timeout: float,
    max_connections: int,
    max_keepalive: int,
    keepalive_expiry: float,
    transport: Optional[httpx.AsyncBaseTransport] = None,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        http2=http2,
        follow_redirects=True,
        timeout=httpx.Timeout(connect=connect_timeout, read=read_timeout, write=10.0, pool=5.0),
        limits=httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive,
            keepalive_expiry=keepalive_expiry,
        ),
        transport=transport,
    )


def parse_single_range(range_header: Optional[str]) -> Optional[Tuple[int, Optional[int]]]:
    """Returns (start, end|None) for `bytes=start-[end]`, (0, None) without a header, None otherwise."""
    if not range_header:
        return 0, None
    match = _SINGLE_RANGE_RE.match(range_header.strip())
    if not match:
        return None
    return int(match[1]), int(match[2]) if match[2] else None


class WindowedUpstreamAudio(UpstreamAudio):
    """Upstream audio read as consecutive bounded Range windows.

    googlevideo throttles any range larger than ~10 MB to roughly playback speed and eventually
    drops the connection, so a large client range is served by stitching windows together. The
    client sees one response whose status and headers describe the whole requested span.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: Dict[str, str],
        first: httpx.Response,
        requested: Optional[Tuple[int, Optional[int]]],
        client_sent_range: bool,
        window: int,
    ):
        self._client = client
        self._url = url
        self._request_headers = headers
        self._current = first
        self._window = window
        self._next: Optional[int] = None
        self._last: Optional[int] = None

        self.status_code = first.status_code
        self.headers: Dict[str, str] = {k.lower(): v for k, v in first.headers.items()}

        match = _CONTENT_RANGE_RE.match(self.headers.get("content-range", ""))
        if first.status_code != 206 or not match or requested is None:
            return
        got_start, got_end, total = int(match[1]), int(match[2]), int(match[3])
        wanted_end = min(requested[1] if requested[1] is not None else total - 1, total - 1)
        if got_end < wanted_end:
            self._next, self._last = got_end + 1, wanted_end

        if not client_sent_range and got_start == 0:
            self.status_code = 200
            self.headers.pop("content-range")
            self.headers["content-length"] = str(total)
        else:
            self.headers["content-range"] = f"bytes {got_start}-{wanted_end}/{total}"
            self.headers["content-length"] = str(wanted_end - got_start + 1)

    async def _relay(self, chunk_size: int) -> AsyncIterator[bytes]:
        try:
            async for chunk in self._current.aiter_raw(chunk_size):
                yield chunk
        except httpx.HTTPError as e:
            # Headers are already sent: end the body early; the client sees a short read and
            # resumes with a Range request.
            logger.warning("upstream dropped mid-stream: %r", e)
            self._next = None

    async def iter_bytes(self, chunk_size: int) -> AsyncIterator[bytes]:
        async for chunk in self._relay(chunk_size):
            yield chunk
        while self._next is not None and self._last is not None and self._next <= self._last:
            start, stop = self._next, min(self._last, self._next + self._window - 1)
            await self._current.aclose()
            headers = {**self._request_headers, "Range": f"bytes={start}-{stop}"}
            try:
                self._current = await self._client.send(
                    self._client.build_request("GET", self._url, headers=headers), stream=True
                )
            except httpx.HTTPError as e:
                logger.warning("upstream window %s-%s failed: %r", start, stop, e)
                return
            got = _CONTENT_RANGE_RE.match(self._current.headers.get("content-range", ""))
            if self._current.status_code != 206 or not got or int(got[1]) != start:
                logger.warning("upstream window %s-%s answered %s", start, stop, self._current.status_code)
                return
            self._next = stop + 1
            async for chunk in self._relay(chunk_size):
                yield chunk

    async def close(self) -> None:
        await self._current.aclose()


class HttpxAudioTransport(AudioTransport):
    """Opens googlevideo responses as streams on a shared, pooled httpx client."""

    def __init__(self, client: httpx.AsyncClient, window_bytes: int):
        self._client = client
        self._window = window_bytes

    async def open(self, source: StreamSource, range_header: Optional[str]) -> UpstreamAudio:
        headers = dict(source.http_headers)
        # identity keeps byte offsets meaningful for Range requests
        headers["Accept-Encoding"] = "identity"

        requested = parse_single_range(range_header)
        if requested is None:
            # suffix or multi-range: forward as-is, without windowing
            first_range = range_header
        else:
            start, end = requested
            window_end = start + self._window - 1
            first_range = f"bytes={start}-{min(end, window_end) if end is not None else window_end}"

        request = self._client.build_request("GET", source.url, headers={**headers, "Range": first_range})
        try:
            response = await self._client.send(request, stream=True)
        except httpx.TimeoutException as e:
            raise UpstreamTimeoutError("Upstream audio did not answer in time") from e
        except httpx.HTTPError as e:
            raise UpstreamUnavailableError("Could not connect to the upstream audio") from e
        return WindowedUpstreamAudio(
            self._client, source.url, headers, response, requested, bool(range_header), self._window
        )
