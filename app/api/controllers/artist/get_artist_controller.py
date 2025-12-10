from app.application.use_cases.artist.get_artist_usecase import GetArtistUseCase
from core.contracts.controller_contract import ControllerContract
from app.domain.models.ytmusic.artist import Artist
from core.models.response_model import ResponseHttp
from core.contracts.usecase_contract import UseCaseArgs

class GetArtistController(ControllerContract):
    def __init__(self, use_case: GetArtistUseCase):
        self._use_case = use_case
    
    async def execute(self, artist_id: str) -> Any:
        try:
            args = UseCaseArgs(data=artist_id, context=None)
            result: Artist = await self._use_case.execute(args)
            return ResponseHttp[Artist](
                success=True,
                message="Artista obtenido exitosamente",
                data=result
            )   

        except Exception as e:
            print(f"Error en execute: {e}")
            return None