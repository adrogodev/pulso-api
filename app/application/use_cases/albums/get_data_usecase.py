
from app.services.ytmusic.ytmusic_service import YTMusicService
from app.application.mappers.album_mapper import AlbumMapper
from app.application.dtos.outputs.album_output import AlbumDataOutput
from app.services.ytmusic.objects.albums.responses.get_album_data_response import GetAlbumDataResponse

class GetAlbumDataUseCase:
    def __init__(self, service: YTMusicService):
        self.service = service
    
    def execute(self, browseId: str) -> AlbumDataOutput:
        data: GetAlbumDataResponse = self.service.get_album_data(browseId)

        result = AlbumMapper.map(data)

        return result