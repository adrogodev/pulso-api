from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search
from typing import Protocol, Optional
from typing import List

class ISearchService(Protocol):
    def search(self, request: SearchInput) -> Optional[List[Search]]:
        ...