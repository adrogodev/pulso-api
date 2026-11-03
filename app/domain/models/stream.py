import re
import time
from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.domain.errors import InvalidInputError

VIDEO_ID_PATTERN = r"^[A-Za-z0-9_-]{11}$"
_VIDEO_ID_RE = re.compile(VIDEO_ID_PATTERN)


def ensure_video_id(video_id: str) -> str:
    """YouTube video ids are 11 url-safe characters; anything else never reaches yt-dlp."""
    if not _VIDEO_ID_RE.match(video_id):
        raise InvalidInputError("Invalid video id", code="INVALID_VIDEO_ID")
    return video_id


class StreamSource(BaseModel):
    """A resolved, time-limited audio URL for a video."""

    video_id: str
    url: str
    format_id: str
    mime_type: str
    ext: Optional[str] = None
    codec: Optional[str] = None
    bitrate_kbps: Optional[float] = None
    duration_seconds: Optional[int] = None
    filesize: Optional[int] = None
    expires_at: int
    http_headers: Dict[str, str] = Field(default_factory=dict)

    def seconds_to_expiry(self, now: float | None = None) -> float:
        return self.expires_at - (now if now is not None else time.time())


class StreamInfo(BaseModel):
    """Public stream metadata (never exposes the upstream URL)."""

    video_id: str
    format_id: str
    mime_type: str
    ext: Optional[str] = None
    codec: Optional[str] = None
    bitrate_kbps: Optional[float] = None
    duration_seconds: Optional[int] = None
    filesize: Optional[int] = None
    expires_at: int
    stream_url: str

    @classmethod
    def from_source(cls, source: StreamSource, stream_url: str) -> "StreamInfo":
        return cls(**source.model_dump(exclude={"url", "http_headers"}), stream_url=stream_url)
