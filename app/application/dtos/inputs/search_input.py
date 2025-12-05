from pydantic import BaseModel
from typing import Optional
from app.domain.enums.category import Category

class SearchInput(BaseModel):
    query: str
    limit: Optional[int] = None

