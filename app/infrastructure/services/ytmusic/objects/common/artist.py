from pydantic import BaseModel
from typing import Optional

class YTMusicArtist(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None