from app.infrastructure.services.ytmusic.objects.search.search_request import SearchRequest
from app.application.dtos.inputs.search_input import SearchInput

class SearchRequestMapper:
    @staticmethod
    def map(request: SearchInput) -> SearchRequest:
        return SearchRequest(
                query=request.query,
                filter=None,
                scope=None,
                # limit= (request.limit if request.limit is not None else 10),
                limit= (request.limit or 10),
                ignore_spelling=False
        )