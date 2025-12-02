from pydantic import BaseModel
from typing import Optional
from app.domain.enums.category import Category

class SearchInput(BaseModel):
    type: Category
    value: str
    limit: Optional[int] = 20

class SearchByArtistInput(BaseModel):
    artist: str
    category: Optional[Category] = None
    page: Optional[int] = 1
    size: Optional[int] = 20
