from app.application.use_cases.search.search_usecase import SearchUseCase
from core.contracts.controller_contract import ControllerContract
from app.application.dtos.inputs.search_input import SearchInput
from core.contracts.usecase_contract import UseCaseArgs
from core.models.response_model import ResponseHttp
from app.domain.models.ytmusic.search import Search
from typing import Any

class SearchController(ControllerContract):
    def __init__(self, use_case: SearchUseCase):
        self._use_case = use_case
    
    async def execute(self, req: SearchInput) -> Any:
        try:
            args = UseCaseArgs(data=req,context=None)    
            result: Search = await self._use_case.execute(args)
            # print("--- DESDE EL CONTROLLER ---")
            # print(result)
            return ResponseHttp[Search](
                success=True,
                message="Busqueda exitosa",
                data=result
            )   

        except Exception as e:
            print(f"Error en execute: {e}")
            return None