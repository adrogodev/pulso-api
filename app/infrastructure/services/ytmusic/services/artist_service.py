from app.domain.contracts.services.ytmusic.artist_service import IArtistService
from app.domain.models.ytmusic.artist import Artist
from app.infrastructure.services.ytmusic.client import YTMusicGateway
from app.infrastructure.services.ytmusic.mapper.artist.get_artist.get_artist_response_mapper import (
    GetArtistResponseMapper,
)
from app.infrastructure.services.ytmusic.objects.artist.get_artist_response import GetArtistResponse


class ArtistService(IArtistService):
    def __init__(self, gateway: YTMusicGateway):
        self._gateway = gateway

    async def get_artist(self, artist_id: str) -> Artist:
        raw = await self._gateway.call("get_artist", artist_id)
        return GetArtistResponseMapper.map(artist_id, GetArtistResponse.model_validate(raw))
