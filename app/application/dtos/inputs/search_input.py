from typing import Optional

from pydantic import BaseModel, Field

from app.domain.enums.category import Category


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=200, examples=["daft punk"])
    filter: Optional[Category] = Field(default=None, description="Restrict results to one category")
    limit: Optional[int] = Field(default=None, ge=1, le=50)
