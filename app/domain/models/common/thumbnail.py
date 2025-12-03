from pydantic import BaseModel

class Thumbnail(BaseModel):
    url: None | str
    width: None | int
    height: None | int