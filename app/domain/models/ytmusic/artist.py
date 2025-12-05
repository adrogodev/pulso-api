from typing import List, Optional
from pydantic import BaseModel, Field

class Artist(BaseModel):
    id: Optional[str] = None
    name: str
    subscribers: Optional[int] = None
    description: Optional[str] = None
    views: Optional[int] = None
    thumbnail: Optional[str] = None

    count_songs: Optional[int] = None
    songs: List["Song"] = Field(default_factory=list)

    count_albums: Optional[int] = None
    albums: List["Album"] = Field(default_factory=list)

    class Config:
        from_attributes = True


