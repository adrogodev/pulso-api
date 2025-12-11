from fastapi import APIRouter
from app.api.config.factory.dependencies_factory import get_link_song_controller
from core.models.response_model import ResponseHttp

router = APIRouter(prefix="/api/songs", tags=["Songs"])

@router.get("", response_model=ResponseHttp[str])
async def get_link_song(song_id: str):
    controller = get_link_song_controller()
    response = await controller.execute(song_id)
    return response