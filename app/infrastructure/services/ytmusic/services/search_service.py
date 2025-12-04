from app.infrastructure.services.ytmusic.mapper.search.search_request_mapper import SearchRequestMapper
from app.infrastructure.services.ytmusic.mapper.search.search_response_mapper import SearchResponseMapper
from app.infrastructure.services.ytmusic.objects.search.search_response import SearchResponse
from app.domain.contracts.services.ytmusic.search_service import ISearchService
from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search
from typing import List, Optional
from ytmusicapi import YTMusic

class SearchService(ISearchService):
    def __init__(self, client: YTMusic):
        self._client = client

    def search(self, request:SearchInput) -> Optional[List[Search]]:
        try:
            search_req = SearchRequestMapper.map(request)
            params=search_req.to_dict()

            raw = self._client.search(**params)
            # print(raw)
            data = [SearchResponse(**item) for item in raw]

            return SearchResponseMapper.map(request.type, data)
  
        except Exception as e:
            print(f"Error en search: {e}")
            return []