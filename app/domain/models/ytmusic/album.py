from typing import List, Optional
from pydantic import BaseModel, Field

class Album(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    year: Optional[str] = None

    artists: List["Artist"] = Field(default_factory=list)
    songs: List["Song"] = Field(default_factory=list)

    class Config:
        from_attributes = True


