from typing import List, Optional
from pydantic import BaseModel
from app.domain.models.common.thumbnail import Thumbnail
from app.domain.models.common.artist import Artist

class SearchResponse(BaseModel):
    category: str
    resultType: str
    artist: str  
    browseId: str
    shuffleId: Optional[str] = None
    radioId: Optional[str] = None
    thumbnails: Optional[List[Thumbnail]] = None

