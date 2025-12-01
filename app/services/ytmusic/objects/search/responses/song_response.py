
from typing import List, Optional
from pydantic import BaseModel
from app.services.ytmusic.models.shared import Thumbnail, Artist, Album

class SongResponse(BaseModel):
    category: Optional[str] = None
    resultType: str
    title: str
    album: Optional[Album] = None
    inLibrary: Optional[bool] = False
    pinnedToListenAgain: Optional[bool] = False
    videoId: str
    videoType: Optional[str] = None
    duration: Optional[str] = None
    year: Optional[str] = None
    artists: List[Artist] = []
    duration_seconds: Optional[int] = None
    views: Optional[str] = None
    isExplicit: Optional[bool] = False
    thumbnails: List[Thumbnail] = []