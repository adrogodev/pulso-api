from typing import List, Optional
from pydantic import BaseModel
from app.services.ytmusic.models.shared import Thumbnail

class PlaylistResponse(BaseModel):
    category: Optional[str] = None
    resultType: str
    title: str
    itemCount: Optional[str] = None
    author: Optional[str] = None
    browseId: Optional[str] = None
    thumbnails: List[Thumbnail] = []