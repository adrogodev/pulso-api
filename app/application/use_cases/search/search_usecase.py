from typing import List
from app.application.dtos.inputs.search_input import SearchInput
from app.services.ytmusic.ytmusic_service import YTMusicService
from app.domain.enums.category import Category
from app.application.dtos.outputs.search_output import SearchOutput
from app.application.mappers.search_mapper import SearchMapper
from app.services.ytmusic.objects.search.responses.song_response import SongResponse
from app.services.ytmusic.objects.search.responses.album_response import AlbumResponse
from app.services.ytmusic.objects.search.responses.playlist_response import PlaylistResponse
from app.services.ytmusic.objects.search.requests.search_request import SearchRequest

class SearchUseCase:
    def __init__(self, services: YTMusicService):
        self.services = services
    
    def execute(self, query: SearchInput) -> List[SearchOutput]:
        queryRequest = SearchRequest (
         query=query.value,
         filter=query.type,
         limit=query.limit,
        )

        # Obtener respuesta segun categoria
        if query.type == Category.SONGS:
            response: List[SongResponse] = self.services.search_songs(queryRequest)

        elif query.type == Category.ALBUMS:
            response: List[AlbumResponse] = self.services.search_albums(queryRequest)
        
        elif query.type == Category.PLAYLISTS:
            response: List[PlaylistResponse] = self.services.search_playlists(queryRequest)

        else:
            return []

        # Se mapean los resultados
        results = [SearchMapper.map(item,query.type.value) for item in response]
        return results