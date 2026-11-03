import logging
import time
from typing import Any, Callable, Dict, Optional
from urllib.parse import parse_qs, urlparse

import anyio

from app.domain.contracts.streaming import AudioStreamProvider
from app.domain.errors import (
    ContentRestrictedError,
    DomainError,
    NotFoundError,
    PrivateContentError,
    UpstreamBlockedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.domain.models.stream import StreamSource

logger = logging.getLogger("rythmx.ytdlp")

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
    if any(s in msg for s in ("video unavailable", "not available", "has been removed", "does not exist", "incomplete youtube id")):
        return NotFoundError("Video not found or unavailable", code="VIDEO_NOT_FOUND")
    if "timed out" in msg:
        return UpstreamTimeoutError("YouTube did not answer in time")
    return UpstreamUnavailableError("Could not resolve the audio stream")


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


class YtDlpStreamAdapter(AudioStreamProvider):
    """Resolves audio URLs with yt-dlp (as a library) in a bounded thread pool, without downloading."""

    def __init__(
        self,
        format_selector: str,
        max_concurrency: int,
        fallback_ttl_seconds: int,
        js_runtime: str = "deno",
        ydl_factory: Optional[Callable[[Dict[str, Any]], Any]] = None,
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
        }

    async def resolve(self, video_id: str) -> StreamSource:
        started = time.perf_counter()
        info = await anyio.to_thread.run_sync(self._extract, video_id, limiter=self._limiter)
        logger.info("resolved %s in %.0f ms", video_id, (time.perf_counter() - started) * 1000)
        return self._to_source(video_id, info)

    def _extract(self, video_id: str) -> Dict[str, Any]:
        try:
            with self._ydl_factory(dict(self._params)) as ydl:
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
