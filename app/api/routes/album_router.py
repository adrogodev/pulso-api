from fastapi import APIRouter, Depends, Request
from app.application.use_cases.albums.get_album_usecase import GetAlbumUseCase
from core.contracts.usecase_contract import UseCaseArgs
from app.api.config.factory.dependencies_factory import get_album_controller

router = APIRouter(prefix="/api/album", tags=["Albums"])


@router.get("/{album_id}")
async def get_album(album_id: str):
    # Obtener controlador del factory
    controller = get_album_controller()
    return await controller.execute(album_id)
