from core.contracts.usecase_contract import UseCaseContract
from app.domain.models.ytmusic.artist import Artist
from app.domain.contracts.services.ytmusic.artist_service import IArtistService
from core.contracts.usecase_contract import UseCaseArgs

class GetArtistUseCase(UseCaseContract[str, Artist]):
    def __init__(self, artist_service: IArtistService):
        self._artist_service = artist_service
    
    async def execute(self, args: UseCaseArgs[str]) -> Artist:
        artist_id = args.data
        return self._artist_service.get_artist(artist_id)