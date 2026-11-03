from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Album(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    year: Optional[str] = None
    artists: List["Artist"] = Field(default_factory=list)
    songs_count: Optional[int] = None
    songs: List["Song"] = Field(default_factory=list)
