from app.application.dtos.inputs.search_input import SearchInput
from app.application.services.cached_loader import CachedLoader
from app.application.services.stream_links import StreamLinkBuilder
from app.domain.contracts.services.ytmusic.search_service import ISearchService
from app.domain.models.ytmusic.search import Search
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract

DEFAULT_LIMIT = 10


class SearchUseCase(UseCaseContract[SearchInput, Search]):
    def __init__(self, services: ISearchService, loader: CachedLoader, links: StreamLinkBuilder, ttl: int):
        self.services = services
        self._loader = loader
        self._links = links
        self._ttl = ttl

    async def execute(self, args: UseCaseArgs[SearchInput]) -> Search:
        req = args.data
        query = " ".join(req.query.split())
        limit = req.limit or DEFAULT_LIMIT
        category = req.filter
        key = f"search:{category.value if category else 'all'}:{limit}:{query.lower()}"

        async def load() -> Search:
            result = await self.services.search(query, category, limit)
            self._links.apply([*result.songs, *result.videos])
            return result

        return await self._loader.get_or_load(key, self._ttl, load, Search)
