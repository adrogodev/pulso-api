from pydantic import BaseModel
from typing import Optional

class Artist(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None