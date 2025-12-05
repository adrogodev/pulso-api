from typing import List, Optional
from pydantic import BaseModel
from app.domain.models.common.thumbnail import Thumbnail
from app.domain.models.common.artist import Artist

class SearchResponse(BaseModel):
    category: str
    resultType: str
    title: Optional[str] = None
    artist: Optional[str] = None
    artists: Optional[List[Artist]] = None  
    browseId: Optional[str] = None
    videoId: Optional[str] = None
    shuffleId: Optional[str] = None
    radioId: Optional[str] = None
    thumbnails: Optional[List[Thumbnail]] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None

