from typing import TypeVar, Generic, Type
from pydantic import BaseModel
from app.application.dtos.outputs.search_output import SearchOutput
from app.application.dtos.outputs.search_output import SearchByArtistOutput

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
        if hasattr(data, "thumbnails") and data.thumbnails:
            thumbnails = [
                t.model_dump() if hasattr(t, "model_dump") else t
                for t in data.thumbnails
            ]


        artists = []
        raw_artists = getattr(data, "artists", None)

        if raw_artists:
            artists = [
                {
                    "id": getattr(artist, "id", "") or "",
                    "name": getattr(artist, "name", "") or "",
                }
                for artist in raw_artists
            ]

        return SearchOutput(
            title=getattr(data, "title", None),
            id=_id,
            thumbnail=thumbnails,
            year=getattr(data, "year", None),
            duration=getattr(data, "duration", None),
            duration_seconds=getattr(data, "duration_seconds", None),
            artists=artists
        )

class SearchByArtistMapper(Generic[T]):
    @staticmethod
    def map(data: T, category: str) -> SearchByArtistOutput:


        if category == "songs":
            _id = getattr(data, "videoId", None)

        elif category == "albums":
            _id = getattr(data, "browseId", None)

        else:
            _id = None

        thumbnails = None
        if hasattr(data, "thumbnails"):
            thumbnails = [t.model_dump() for t in data.thumbnails]

        return SearchByArtistOutput(
            category=getattr(data, "category", None),
            title=getattr(data, "title", None),
            id=_id,
            thumbnail=thumbnails,
            year=getattr(data, "year", None),
            duration=getattr(data, "duration", None),
            duration_seconds=getattr(data, "duration_seconds", None)
        )
