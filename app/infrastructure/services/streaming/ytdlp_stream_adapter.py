import contextlib
import logging
import os
import tempfile
import time
from typing import Any, Callable, Dict, Iterator, Optional
from urllib.parse import parse_qs, urlparse

import anyio

from app.domain.contracts.streaming import AudioStreamProvider
from app.domain.errors import (
    ContentRestrictedError,
    DomainError,
    NotFoundError,
    PrivateContentError,
    StreamConfigurationError,
    UpstreamBlockedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.domain.models.stream import StreamSource

logger = logging.getLogger("pulso.ytdlp")

WATCH_URL = "https://www.youtube.com/watch?v="

_MIME_BY_EXT = {"m4a": "audio/mp4", "mp4": "audio/mp4", "webm": "audio/webm", "opus": "audio/ogg", "mp3": "audio/mpeg"}


def map_ytdlp_error(error: Exception) -> DomainError:
    """Translate yt-dlp failures (usually DownloadError wrapping an ExtractorError) into domain errors."""
    cause = getattr(error, "exc_info", None)
    cause_name = type(cause[1]).__name__ if cause and cause[1] else ""
    msg = str(error).lower()

    if cause_name == "GeoRestrictedError" or "not available in your country" in msg or "geo restrict" in msg:
        return ContentRestrictedError("This video is not available in the server's region", code="GEO_RESTRICTED")
    if "private video" in msg:
        return PrivateContentError("This video is private")
    if "confirm your age" in msg or "age-restricted" in msg or "age restricted" in msg:
        return ContentRestrictedError("This video is age restricted", code="AGE_RESTRICTED")
    if "not a bot" in msg or "sign in to confirm" in msg:
        return UpstreamBlockedError("YouTube is asking this server to sign in (bot check)")
    if "http error 429" in msg or "too many requests" in msg:
        return UpstreamBlockedError("YouTube is rate limiting this server", code="UPSTREAM_RATE_LIMITED")
    if "requested format is not available" in msg:
        return NotFoundError("No audio format available for this video", code="AUDIO_FORMAT_UNAVAILABLE")
    if any(s in msg for s in ("video unavailable", "is unavailable", "not available", "has been removed", "does not exist", "incomplete youtube id")):
        return NotFoundError("Video not found or unavailable", code="VIDEO_NOT_FOUND")
    if "timed out" in msg:
        return UpstreamTimeoutError("YouTube did not answer in time")
    return UpstreamUnavailableError("Could not resolve the audio stream")


class _YtDlpLogger:
    """Keeps yt-dlp's own output at DEBUG: the adapter already logs one WARNING per failed extraction."""

    def debug(self, msg: str) -> None:
        logger.debug(msg)

    info = warning = error = debug


def _default_ydl_factory() -> Callable[[Dict[str, Any]], Any]:
    import yt_dlp

    return yt_dlp.YoutubeDL


def _js_runtimes(runtime: str) -> Dict[str, Dict[str, str]]:
    if not runtime:
        return {}
    config: Dict[str, str] = {}
    if runtime == "deno":
        try:
            import deno  # binary shipped by the yt-dlp[deno] extra

            config["path"] = deno.find_deno_bin()
        except Exception:
            pass  # fall back to a deno found on PATH
    return {runtime: config}


def _parse_extractor_args(value: str) -> Dict[str, Dict[str, list]]:
    """Parses `IE:key=v1,v2;key2=v` groups (yt-dlp --extractor-args syntax) separated by spaces."""
    import yt_dlp

    argv = []
    for group in value.split():
        if ":" not in group:
            raise ValueError(f"YTDLP_EXTRACTOR_ARGS: expected 'extractor:key=value', got {group!r}")
        argv += ["--extractor-args", group]
    try:
        return yt_dlp.parse_options(argv).ydl_opts["extractor_args"]
    except (SystemExit, Exception) as e:
        raise ValueError(f"YTDLP_EXTRACTOR_ARGS is invalid: {value!r}") from e


def _read_cookies(path: str) -> bytes:
    if os.path.isdir(path):
        # Docker creates a directory when the bind-mounted file is missing on the host
        raise ValueError(f"YTDLP_COOKIES_FILE is a directory, not a file (is the mount source missing?): {path}")
    if not os.path.exists(path):
        raise ValueError(f"YTDLP_COOKIES_FILE does not exist: {path}")
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError as e:
        raise ValueError(f"YTDLP_COOKIES_FILE cannot be read ({e.strerror}): {path}") from e


@contextlib.contextmanager
def _cookies_copy(content: bytes) -> Iterator[str]:
    """yt-dlp rewrites its cookie file in place, which fails on a read-only secret mount and races between
    concurrent extractions, so every extraction gets its own private copy."""
    fd, path = tempfile.mkstemp(prefix="ytdlp-cookies-", suffix=".txt")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        yield path
    finally:
        with contextlib.suppress(OSError):
            os.remove(path)


class YtDlpStreamAdapter(AudioStreamProvider):
    """Resolves audio URLs with yt-dlp (as a library) in a bounded thread pool, without downloading."""

    def __init__(
        self,
        format_selector: str,
        max_concurrency: int,
        fallback_ttl_seconds: int,
        js_runtime: str = "deno",
        ydl_factory: Optional[Callable[[Dict[str, Any]], Any]] = None,
        cookies_file: str = "",
        proxy: str = "",
        extractor_args: str = "",
    ):
        self._limiter = anyio.CapacityLimiter(max_concurrency)
        self._fallback_ttl = fallback_ttl_seconds
        self._ydl_factory = ydl_factory or _default_ydl_factory()
        self._params: Dict[str, Any] = {
            "format": format_selector,
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "js_runtimes": _js_runtimes(js_runtime),
            "logger": _YtDlpLogger(),
        }
        # Datacenter IPs hit YouTube's "confirm you're not a bot" check; these options get past it.
        # A bad setting is logged at startup and answered as a clear 503 instead of crashing requests.
        self._config_error: Optional[StreamConfigurationError] = None
        self._cookies: Optional[bytes] = None
        if cookies_file:
            try:
                self._cookies = _read_cookies(cookies_file)
            except ValueError as e:
                self._fail_config(e, "COOKIES_UNAVAILABLE", "The YouTube cookies file configured on the server cannot be read")
        if proxy:
            self._params["proxy"] = proxy
        if extractor_args.strip():
            try:
                self._params["extractor_args"] = _parse_extractor_args(extractor_args)
            except ValueError as e:
                self._fail_config(e, "STREAM_MISCONFIGURED", "The server's yt-dlp settings are invalid")

    def _fail_config(self, cause: ValueError, code: str, message: str) -> None:
        logger.error("%s; audio streaming is disabled until it is fixed", cause)
        if self._config_error is None:
            self._config_error = StreamConfigurationError(message, code=code)

    async def resolve(self, video_id: str) -> StreamSource:
        if self._config_error is not None:
            raise StreamConfigurationError(self._config_error.message, code=self._config_error.code)
        started = time.perf_counter()
        info = await anyio.to_thread.run_sync(self._extract, video_id, limiter=self._limiter)
        logger.info("resolved %s in %.0f ms", video_id, (time.perf_counter() - started) * 1000)
        return self._to_source(video_id, info)

    def _extract(self, video_id: str) -> Dict[str, Any]:
        try:
            with contextlib.ExitStack() as stack:
                params = dict(self._params)
                if self._cookies is not None:
                    params["cookiefile"] = stack.enter_context(_cookies_copy(self._cookies))
                with self._ydl_factory(params) as ydl:
                    return ydl.extract_info(WATCH_URL + video_id, download=False)
        except DomainError:
            raise
        except Exception as e:
            mapped = map_ytdlp_error(e)
            logger.warning("yt-dlp failed for %s: %s -> %s", video_id, e, mapped.code)
            raise mapped from e

    def _to_source(self, video_id: str, info: Dict[str, Any]) -> StreamSource:
        url = info.get("url")
        if not url:
            raise NotFoundError("No audio format available for this video", code="AUDIO_FORMAT_UNAVAILABLE")
        ext = info.get("ext")
        return StreamSource(
            video_id=video_id,
            url=url,
            format_id=str(info.get("format_id") or "unknown"),
            mime_type=_MIME_BY_EXT.get(ext or "", f"audio/{ext}" if ext else "application/octet-stream"),
            ext=ext,
            codec=info.get("acodec"),
            bitrate_kbps=info.get("abr") or info.get("tbr"),
            duration_seconds=int(info["duration"]) if info.get("duration") else None,
            filesize=info.get("filesize") or info.get("filesize_approx"),
            expires_at=self._expiry(url),
            http_headers={k: str(v) for k, v in (info.get("http_headers") or {}).items()},
        )

    def _expiry(self, url: str) -> int:
        """googlevideo URLs carry their absolute expiry as the `expire` query parameter."""
        values = parse_qs(urlparse(url).query).get("expire")
        if values and values[0].isdigit():
            return int(values[0])
        return int(time.time()) + self._fallback_ttl
