from typing import List, Optional
from pydantic import BaseModel
from app.domain.models.common.artist import CommonArtist
from app.domain.models.common.track import CommonTrack

class CommonAlbum(BaseModel):
    title: Optional[str]
    year: Optional[str]
    description: Optional[str]
    thumbnails: None | str
    artists: List[CommonArtist] = []
    track_count: Optional[int]
    duration: Optional[str]
    duration_seconds: Optional[int]
    audio_playlist_id: Optional[str]
    tracks: List[CommonTrack] = []