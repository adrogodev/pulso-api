
from pydantic import BaseModel
from typing import Optional

class Thumbnail(BaseModel):
    url: str
    width: int
    height: int

class Artist(BaseModel):
    name: str
    id: Optional[str] = None

class Album(BaseModel):
    name: str
    id: Optional[str] = None