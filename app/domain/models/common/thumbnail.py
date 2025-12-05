from pydantic import BaseModel

class CommonThumbnail(BaseModel):
    url: None | str
    width: None | int
    height: None | int