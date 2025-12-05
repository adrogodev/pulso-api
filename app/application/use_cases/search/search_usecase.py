from app.domain.contracts.services.ytmusic.search_service import ISearchService
from core.contracts.usecase_contract import UseCaseContract, UseCaseArgs
from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search

class SearchUseCase(UseCaseContract[SearchInput, Search]):
    def __init__(self, services: ISearchService):
        self.services = services
    
    async def execute(self, args: UseCaseArgs[SearchInput]) -> Search:
        return self.services.search(args.data)