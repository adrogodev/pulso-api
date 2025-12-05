from app.domain.models.common.artist import Artist
from typing import List, Optional
from pydantic import BaseModel

class Search (BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    thumbnail: str | None = None
    description: Optional[str] = None
    duration: str | None = None
    duration_seconds: int | None = None
    artists:  str | None = None
    

    