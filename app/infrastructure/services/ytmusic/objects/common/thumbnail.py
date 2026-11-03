from typing import Optional

from pydantic import BaseModel


class YTMusicThumbnail(BaseModel):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
