from typing import Annotated

from fastapi import APIRouter, Path, Request

from app.api.config.factory.dependencies_factory import get_album_controller
from app.api.http.openapi import ID_PATTERN, METADATA_ERRORS
from app.api.http.responses import json_response
from app.domain.models.ytmusic.album import Album
from core.models.response_model import ResponseHttp

router = APIRouter(prefix="/api/album", tags=["Albums"])


@router.get(
    "/{album_id}",
    response_model=ResponseHttp[Album],
    summary="Album detail with its tracks",
    description="Every track includes a `stream_url` that plays through this API.",
    responses=METADATA_ERRORS,
)
async def get_album(request: Request, album_id: Annotated[str, Path(pattern=ID_PATTERN, examples=["MPREb_4pL8gzRtw1p"])]):
    response = await get_album_controller().execute(album_id)
    return json_response(request, response, cache_control=request.app.state.metadata_cache_control)
