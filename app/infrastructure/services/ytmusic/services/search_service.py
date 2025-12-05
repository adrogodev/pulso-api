from app.infrastructure.services.ytmusic.mapper.search.search_request_mapper import SearchRequestMapper
from app.infrastructure.services.ytmusic.mapper.search.search_response_mapper import SearchResponseMapper
from app.infrastructure.services.ytmusic.objects.search.search_response import SearchResponse
from app.domain.contracts.services.ytmusic.search_service import ISearchService
from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search
from typing import Optional
from ytmusicapi import YTMusic

class SearchService(ISearchService):
    def __init__(self, client: YTMusic):
        self._client = client

    def search(self, request: SearchInput) -> Search:
        try:
            search_req = SearchRequestMapper.map(request)
            params = search_req.to_dict()
            raw = self._client.search(**params)

            items = [SearchResponse(**item) for item in raw]
            # print(items)
            result = SearchResponseMapper.map(items)

            return result

        except Exception as e:
            print(f"Error en search: {e}")
            import traceback
            traceback.print_exc()
            return Search(artists=[], songs=[])