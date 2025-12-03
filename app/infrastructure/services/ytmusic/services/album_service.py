from app.infrastructure.services.ytmusic.mapper.get_album.get_album_response_mapper import GetAlbumResponseMapper
from app.infrastructure.services.ytmusic.objects.album.get_album_response import GetAlbumResponse
from app.domain.contracts.services.ytmusic.album_service import IAlbumService
from app.domain.models.common.album import Album
from ytmusicapi import YTMusic
from typing import Optional

class AlbumService(IAlbumService):
    def __init__(self, client: YTMusic):
        self._client = client
    
    def get_album_data(self, id: str) -> Optional[Album]:
        try:
            # data = GetAlbumResponse(**self._client.get_album(browseId=id)) 
            raw = self._client.get_album(browseId=id)
            data = GetAlbumResponse(**raw) 
            return GetAlbumResponseMapper.map(data)
        except Exception as e:
            print(f"Error en get_album_data: {e}")
            return None
        