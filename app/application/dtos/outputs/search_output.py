from pydantic import BaseModel
from typing import Optional, List

class Thumbnail(BaseModel):
    url: str
    width: int
    height: int

class Artist(BaseModel):
    name: str
    id: str

class Album(BaseModel):
    name: str
    id: Optional[str] = None
    
class Song(BaseModel):
    category: Optional[str]
    resultType: str
    title: str
    album: Optional[Album]
    inLibrary: bool
    pinnedToListenAgain: bool
    videoId: str
    videoType: str
    duration: Optional[str]
    year: Optional[str]
    artists: List[Artist]
    duration_seconds: Optional[int]
    views: Optional[str]
    isExplicit: Optional[bool]
    thumbnails: List[Thumbnail]
