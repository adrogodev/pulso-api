from pydantic import BaseModel
from typing import Optional

class SearchInput(BaseModel):
    query: str
    filter: Optional[str] = None
    scope: Optional[str] = None
    limit: Optional[int] = 20
    ignore_spelling: Optional[bool] = False
