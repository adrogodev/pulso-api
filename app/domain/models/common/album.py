from typing import List, Optional
from pydantic import BaseModel
from app.domain.models.common.artist import Artist
from app.domain.models.common.track import Track

class Album(BaseModel):
    title: Optional[str]
    year: Optional[str]
    description: Optional[str]
    thumbnails: None | str
    artists: List[Artist] = []
    track_count: Optional[int]
    duration: Optional[str]
    duration_seconds: Optional[int]
    audio_playlist_id: Optional[str]
    tracks: List[Track] = []