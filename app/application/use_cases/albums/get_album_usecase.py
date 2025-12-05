from app.domain.models.common.album import CommonAlbum as Album
from app.domain.contracts.services.ytmusic.album_service import IAlbumService
from core.contracts.usecase_contract import UseCaseContract, UseCaseArgs

class GetAlbumUseCase(UseCaseContract[str, Album]):
    def __init__(self, album_service: IAlbumService):
        self._album_service = album_service
    
    async def execute(self, args: UseCaseArgs[str]) -> Album:
        album_id = args.data
        return self._album_service.get_album_data(album_id)