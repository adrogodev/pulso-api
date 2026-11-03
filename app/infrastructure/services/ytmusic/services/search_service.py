from typing import Optional

from app.domain.contracts.services.ytmusic.search_service import ISearchService
from app.domain.enums.category import Category
from app.domain.models.ytmusic.search import Search
from app.infrastructure.services.ytmusic.client import YTMusicGateway
from app.infrastructure.services.ytmusic.mapper.search.search_response_mapper import SearchResponseMapper
from app.infrastructure.services.ytmusic.objects.search.search_response import SearchResponse


class SearchService(ISearchService):
    def __init__(self, gateway: YTMusicGateway):
        self._gateway = gateway

    async def search(self, query: str, category: Optional[Category], limit: int) -> Search:
        raw = await self._gateway.call(
            "search", query=query, filter=category.value if category else None, limit=limit
        )
        result = SearchResponseMapper.map([SearchResponse.model_validate(item) for item in raw])
        # ytmusicapi treats limit as a minimum and usually returns ~20 items per category
        result.artists = result.artists[:limit]
        result.songs = result.songs[:limit]
        result.videos = result.videos[:limit]
        result.albums = result.albums[:limit]
        return result

    async def suggestions(self, query: str) -> list[str]:
        raw = await self._gateway.call("get_search_suggestions", query)
        return [s for s in raw if isinstance(s, str)]
