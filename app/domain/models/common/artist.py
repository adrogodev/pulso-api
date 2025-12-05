from pydantic import BaseModel
from typing import Optional

class CommonArtist(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None