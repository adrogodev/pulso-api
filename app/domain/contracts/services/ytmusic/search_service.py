from typing import Optional, Protocol

from app.domain.enums.category import Category
from app.domain.models.ytmusic.search import Search


class ISearchService(Protocol):
    async def search(self, query: str, category: Optional[Category], limit: int) -> Search: ...

    async def suggestions(self, query: str) -> list[str]: ...
