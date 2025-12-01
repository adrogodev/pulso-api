from typing import List
from app.application.dtos.inputs.search_input import SearchInput
from app.services.ytmusic.ytmusic_service import YTMusicService
from app.services.ytmusic.objects.search.requests.search_request import SearchRequest
from app.services.ytmusic.objects.search.responses.song_response import SongResponse

class GetSongsUseCase:
    def __init__(self, service: YTMusicService):
        self.service = service
    
    def execute(self, data: SearchInput) -> List[SongResponse]:
        queryRequest = SearchRequest (
         query=data.query,
         filter='songs',
         scope=None,
         limit=data.limit,
         ignore_spelling=False
        )

        songs = self.service.search_songs(queryRequest)
        return songs