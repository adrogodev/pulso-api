from typing import Protocol, Optional
from app.domain.models.common.album import Album

class IAlbumService(Protocol):
    def get_album_data(self, id: str) -> Optional[Album]:
        ...