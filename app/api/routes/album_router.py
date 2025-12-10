from app.application.use_cases.albums.get_album_usecase import GetAlbumUseCase
from app.api.config.factory.dependencies_factory import get_album_controller
from core.contracts.usecase_contract import UseCaseArgs
from core.models.response_model import ResponseHttp
from app.domain.models.ytmusic.album import Album
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/album", tags=["Albums"])

@router.get("/{album_id}", response_model=ResponseHttp[Album])
async def get_album(album_id: str):
    # Obtener controlador del factory
    controller = get_album_controller()
    response = await controller.execute(album_id)

    return JSONResponse(
        content=response.model_dump(exclude_none=True)
    )
