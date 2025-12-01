from typing import List, Optional
from pydantic import BaseModel
from app.services.ytmusic.models.shared import Thumbnail, Artist

class AlbumResponse(BaseModel):
    category: Optional[str] = None
    resultType: str
    title: str
    type: Optional[str] = None
    playlistId: Optional[str] = None
    duration: Optional[str] = None
    year: Optional[str] = None
    artists: List[Artist] = []
    browseId: Optional[str] = None
    isExplicit: Optional[bool] = False
    thumbnails: List[Thumbnail] = []