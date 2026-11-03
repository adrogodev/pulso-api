from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Artist(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    name: str
    subscribers: Optional[str] = None
    description: Optional[str] = None
    views: Optional[str] = None
    thumbnail: Optional[str] = None

    count_songs: Optional[int] = None
    songs: List["Song"] = Field(default_factory=list)

    count_albums: Optional[int] = None
    albums: List["Album"] = Field(default_factory=list)
