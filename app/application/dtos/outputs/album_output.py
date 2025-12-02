
from pydantic import BaseModel
from typing import List, Optional

class Artist(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None

class Thumbnail(BaseModel):
    url: str
    width: int
    height: int

class TrackOutput(BaseModel):
    id: Optional[str]
    title: Optional[str]
    duration: Optional[str]
    duration_seconds: Optional[int]
    artists: List[Artist] = []
    thumbnails: List[Thumbnail] = []

class AlbumDataOutput(BaseModel):
    title: Optional[str]
    year: Optional[str]
    description: Optional[str]
    thumbnails: List[Thumbnail] = []
    artists: List[Artist] = []
    track_count: Optional[int]
    duration: Optional[str]
    duration_seconds: Optional[int]
    audio_playlist_id: Optional[str]
    tracks: List[TrackOutput] = []