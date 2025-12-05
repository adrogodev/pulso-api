from typing import List, Optional
from pydantic import BaseModel, Field

class Song(BaseModel):
    id: Optional[str] = None
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None

    artists: List["Artist"] = Field(default_factory=list)
    album: Optional["Album"] = None

    class Config:
        from_attributes = True


