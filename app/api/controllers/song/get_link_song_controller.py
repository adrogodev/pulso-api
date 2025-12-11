from core.contracts.controller_contract import ControllerContract
from app.application.use_cases.songs.get_link_songs_usecase import GetLinkSongsUseCase
from core.contracts.usecase_contract import UseCaseArgs
from core.models.response_model import ResponseHttp
from typing import Any

class GetLinkSongController(ControllerContract):
    def __init__(self, use_case: GetLinkSongsUseCase):
        self._use_case = use_case
    
    async def execute(self, song_id: str) -> Any:
        try:
            args = UseCaseArgs(data=song_id, context=None)
            result: str = await self._use_case.execute(args)
            return ResponseHttp[str](
                success=True,
                message="Link obtenido exitosamente",
                data=result
            )
        except Exception as e:
            print(f"Error en execute: {e}")
            return None