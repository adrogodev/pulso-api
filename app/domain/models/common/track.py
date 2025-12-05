from typing import List, Optional
from pydantic import BaseModel
from app.domain.models.common.artist import CommonArtist

class CommonTrack(BaseModel):
    id: Optional[str]
    title: Optional[str]
    duration: Optional[str]
    duration_seconds: Optional[int]
    artists: List[CommonArtist] = []
    thumbnails: None | str