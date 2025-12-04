from app.domain.contracts.services.ytmusic.search_service import ISearchService
from core.contracts.usecase_contract import UseCaseContract, UseCaseArgs
from app.application.dtos.inputs.search_input import SearchInput
from app.domain.models.ytmusic.search import Search
from typing import List

class SearchUseCase(UseCaseContract[SearchInput, List[Search]]):
    def __init__(self, services: ISearchService):
        self.services = services
    
    async def execute(self, args: UseCaseArgs[SearchInput]) -> List[Search]:
        return self.services.search(args.data)