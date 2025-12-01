from typing import TypeVar, Generic, Type
from pydantic import BaseModel
from app.application.dtos.outputs.search_output import SearchOutput

T = TypeVar('T', bound=BaseModel)

class SearchMapper(Generic[T]):
    @staticmethod
    def map(data: T, category: str) -> SearchOutput:


        if category == "songs":
            _id = getattr(data, "videoId", None)

        elif category == "albums":
            _id = getattr(data, "browseId", None)

        elif category == "playlists":
            _id = getattr(data, "browseId", None)

        else:
            _id = None

        thumbnails = None
        if hasattr(data, "thumbnails"):
            thumbnails = [t.model_dump() for t in data.thumbnails]

        artists = None
        if hasattr(data, "artists"):
            artists = [a.model_dump() for a in data.artists]

        return SearchOutput(
            title=getattr(data, "title", None),
            id=_id,
            thumbnail=thumbnails,
            year=getattr(data, "year", None),
            duration=getattr(data, "duration", None),
            duration_seconds=getattr(data, "duration_seconds", None),
            artists=artists
        )
