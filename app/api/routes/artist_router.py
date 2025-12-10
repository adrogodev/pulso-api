from fastapi import APIRouter , Depends
from app.api.config.factory.dependencies_factory import get_artist_controller
from app.domain.models.ytmusic.artist import Artist
from core.models.response_model import ResponseHttp
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/artist", tags=["Artists"])

@router.get("", response_model=ResponseHttp[Artist])
async def get_artist( id: str):
    controller = get_artist_controller()
    response = await controller.execute(id)
    
    return JSONResponse(
        content=response.model_dump(exclude_none=True)
    )