from typing import Protocol

from app.domain.models.ytmusic.album import Album


class IAlbumService(Protocol):
    async def get_album_data(self, id: str) -> Album: ...
