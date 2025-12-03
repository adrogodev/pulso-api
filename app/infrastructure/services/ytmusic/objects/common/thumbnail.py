from pydantic import BaseModel

class YTMusicThumbnail(BaseModel):
    url: str
    width: int
    height: int