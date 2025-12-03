from typing import List, Optional
from pydantic import BaseModel
from app.domain.models.common.artist import Artist

class Track(BaseModel):
    id: Optional[str]
    title: Optional[str]
    duration: Optional[str]
    duration_seconds: Optional[int]
    artists: List[Artist] = []
    thumbnails: None | str