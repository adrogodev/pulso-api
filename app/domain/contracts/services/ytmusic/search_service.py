from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search
from typing import Protocol, Optional

class ISearchService(Protocol):
    def search(self, request: SearchInput) -> Optional[Search]:
        ...