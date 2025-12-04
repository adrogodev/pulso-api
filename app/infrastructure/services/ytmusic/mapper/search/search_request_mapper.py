from app.infrastructure.services.ytmusic.objects.search.search_request import SearchRequest
from app.application.dtos.inputs.search_input import SearchInput

class SearchRequestMapper:
    @staticmethod
    def map(request: SearchInput) -> SearchRequest:
        return SearchRequest(
                query=request.value,
                filter=request.type.value,
                scope=None,
                limit=request.limit,
                ignore_spelling=False
        )