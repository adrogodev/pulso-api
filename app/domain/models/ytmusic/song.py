from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Song(BaseModel):
    """A playable item: a song, a music video or an album track."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    track_number: Optional[int] = None
    is_explicit: Optional[bool] = None

    artists: List["Artist"] = Field(default_factory=list)
    album: Optional["Album"] = None

    stream_url: Optional[str] = None
