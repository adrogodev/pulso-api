from typing import Protocol

from app.domain.models.ytmusic.artist import Artist


class IArtistService(Protocol):
    async def get_artist(self, artist_id: str) -> Artist: ...
