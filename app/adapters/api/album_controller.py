from fastapi import APIRouter
from app.application.use_cases.albums.get_data_usecase import GetAlbumDataUseCase
from app.services.ytmusic.ytmusic_service import YTMusicService
from app.domain.models.success_response import SuccessResponse
from app.application.dtos.outputs.album_output import AlbumDataOutput

router = APIRouter(prefix="/api/album", tags=["Albums"])

service = YTMusicService()
get_album_data_usecase = GetAlbumDataUseCase(service)

@router.get("/get-data")
def get_data(browseId: str) -> SuccessResponse[AlbumDataOutput]:
   album_data = get_album_data_usecase.execute(browseId)
   return SuccessResponse(
    success=True,
    message="Datos del albun obtenidos exitosamente",
    data=album_data
    )


