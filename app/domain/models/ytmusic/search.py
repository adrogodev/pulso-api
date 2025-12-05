from typing import List
from pydantic import BaseModel, Field

class Search(BaseModel):
    artists: List["Artist"] = Field(default_factory=list)
    songs: List["Song"] = Field(default_factory=list)

