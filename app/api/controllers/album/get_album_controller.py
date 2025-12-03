from app.application.use_cases.albums.get_album_usecase import GetAlbumUseCase
from core.contracts.usecase_contract import UseCaseArgs
from app.domain.models.common.album import Album
from core.contracts.controller_contract import ControllerContract
from typing import Any
from core.models.response_model import ResponseHttp

class GetAlbumController(ControllerContract):
    def __init__(self, use_case: GetAlbumUseCase):
        self._use_case = use_case
    
    async def execute(self, album_id:str) -> Any:
        try:
            args = UseCaseArgs(data=album_id, context=None)
            result: Album = await self._use_case.execute(args)
            return ResponseHttp[Album](
                success=True,
                message="Album obtenido exitosamente",
                data=result
            )   

        except Exception as e:
            print(f"Error en execute: {e}")
            return None