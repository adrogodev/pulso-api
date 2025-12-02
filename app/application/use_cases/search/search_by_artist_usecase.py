from typing import Optional, List
from app.services.ytmusic.ytmusic_service import YTMusicService
from app.services.ytmusic.objects.search.requests.search_request import SearchRequest
from app.application.dtos.inputs.search_input import SearchByArtistInput
from app.domain.enums.category import Category
from app.application.dtos.outputs.search_output import SearchByArtistOutput
from app.application.mappers.search_mapper import SearchByArtistMapper

class SearchByArtistUseCase:
    def __init__(self, service: YTMusicService):
        self.service = service
    
    def execute(self, data: SearchByArtistInput) -> List[SearchByArtistOutput]:
        
        base_query = SearchRequest(
            query=data.artist,
            limit=data.size
        )

        all_results = []

        if data.category is None:

            songs = self.service.search_songs(base_query)
            albums = self.service.search_albums(base_query)

            mapped_songs = [
                SearchByArtistMapper.map(item, Category.SONGS.value)
                for item in songs
            ]

            mapped_albums = [
                SearchByArtistMapper.map(item, Category.ALBUMS.value)
                for item in albums
            ]

            all_results = mapped_songs + mapped_albums

        else:
            if data.category == Category.SONGS:
                songs = self.service.search_songs(base_query)
                all_results = [
                    SearchByArtistMapper.map(item, Category.SONGS.value)
                    for item in songs
                ]

            elif data.category == Category.ALBUMS:
                albums = self.service.search_albums(base_query)
                all_results = [
                    SearchByArtistMapper.map(item, Category.ALBUMS.value)
                    for item in albums
                ]

            else:
                return []

        page = data.page or 1
        size = data.size or 20

        start = (page - 1) * size
        end = start + size

        return all_results[start:end]
