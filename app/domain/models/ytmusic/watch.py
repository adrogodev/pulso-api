from typing import List, Optional

from pydantic import BaseModel, Field


class WatchPlaylist(BaseModel):
    """Up-next queue (radio) generated from a video."""

    video_id: str
    playlist_id: Optional[str] = None
    lyrics_id: Optional[str] = None
    related_id: Optional[str] = None
    tracks: List["Song"] = Field(default_factory=list)


class Lyrics(BaseModel):
    video_id: str
    text: str
    source: Optional[str] = None


class SearchSuggestions(BaseModel):
    query: str
    suggestions: List[str] = Field(default_factory=list)
