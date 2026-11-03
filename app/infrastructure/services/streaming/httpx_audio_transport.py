from typing import AsyncIterator, Dict, Optional

import httpx

from app.domain.contracts.streaming import AudioTransport, UpstreamAudio
from app.domain.errors import UpstreamTimeoutError, UpstreamUnavailableError
from app.domain.models.stream import StreamSource


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


class HttpxUpstreamAudio(UpstreamAudio):
    def __init__(self, response: httpx.Response):
        self._response = response
        self.status_code = response.status_code
        self.headers: Dict[str, str] = {k.lower(): v for k, v in response.headers.items()}

    async def iter_bytes(self, chunk_size: int) -> AsyncIterator[bytes]:
        try:
            async for chunk in self._response.aiter_raw(chunk_size):
                yield chunk
        except httpx.HTTPError as e:
            raise UpstreamUnavailableError("Upstream audio connection failed") from e

    async def close(self) -> None:
        await self._response.aclose()


class HttpxAudioTransport(AudioTransport):
    """Opens googlevideo responses as streams on a shared, pooled httpx client."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def open(self, source: StreamSource, range_header: Optional[str]) -> UpstreamAudio:
        headers = dict(source.http_headers)
        # identity keeps byte offsets meaningful for Range requests
        headers["Accept-Encoding"] = "identity"
        if range_header:
            headers["Range"] = range_header
        request = self._client.build_request("GET", source.url, headers=headers)
        try:
            response = await self._client.send(request, stream=True)
        except httpx.TimeoutException as e:
            raise UpstreamTimeoutError("Upstream audio did not answer in time") from e
        except httpx.HTTPError as e:
            raise UpstreamUnavailableError("Could not connect to the upstream audio") from e
        return HttpxUpstreamAudio(response)
