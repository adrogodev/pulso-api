
from typing import List, Optional
from pydantic import BaseModel
from app.services.ytmusic.models.shared import Thumbnail

class ArtistResponse(BaseModel):
    category: Optional[str] = None
    resultType: str
    artist: str
    shuffleId: Optional[str] = None
    radioId: Optional[str] = None
    browseId: Optional[str] = None
    thumbnails: List[Thumbnail] = []