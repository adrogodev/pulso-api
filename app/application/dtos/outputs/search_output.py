from pydantic import BaseModel
from typing import Optional, List

class Thumbnail(BaseModel):
    url: str
    width: int
    height: int

class Artist(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None

class SearchOutput(BaseModel):
    title: str
    id: str
    thumbnail: List[Thumbnail]
    year: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    artists: Optional[List[Artist]] = None

class SearchByArtistOutput(BaseModel):
    category: Optional[str] = None
    title: str
    id: str
    thumbnail: List[Thumbnail]
    year: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None    
    