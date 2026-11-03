from app.domain.contracts.services.ytmusic.album_service import IAlbumService
from app.domain.models.ytmusic.album import Album
from app.infrastructure.services.ytmusic.client import YTMusicGateway
from app.infrastructure.services.ytmusic.mapper.get_album.get_album_response_mapper import GetAlbumResponseMapper
from app.infrastructure.services.ytmusic.objects.album.get_album_response import GetAlbumResponse


class AlbumService(IAlbumService):
    def __init__(self, gateway: YTMusicGateway):
        self._gateway = gateway

    async def get_album_data(self, id: str) -> Album:
        raw = await self._gateway.call("get_album", browseId=id)
        return GetAlbumResponseMapper.map(id, GetAlbumResponse.model_validate(raw))
