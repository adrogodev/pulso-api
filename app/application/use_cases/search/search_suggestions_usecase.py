from app.application.services.cached_loader import CachedLoader
from app.domain.contracts.services.ytmusic.search_service import ISearchService
from app.domain.models.ytmusic.watch import SearchSuggestions
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract


class SearchSuggestionsUseCase(UseCaseContract[str, SearchSuggestions]):
    def __init__(self, services: ISearchService, loader: CachedLoader, ttl: int):
        self._services = services
        self._loader = loader
        self._ttl = ttl

    async def execute(self, args: UseCaseArgs[str]) -> SearchSuggestions:
        query = " ".join(args.data.split())

        async def load() -> SearchSuggestions:
            return SearchSuggestions(query=query, suggestions=await self._services.suggestions(query))

        return await self._loader.get_or_load(f"suggest:{query.lower()}", self._ttl, load, SearchSuggestions)
