from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import RedirectResponse

from app.api.config.factory.dependencies_factory import get_artist_controller
from app.api.http.openapi import ID_PATTERN, METADATA_ERRORS
from app.api.http.responses import json_response
from app.domain.models.ytmusic.artist import Artist
from core.models.response_model import ResponseHttp

router = APIRouter(prefix="/api/artist", tags=["Artists"])


@router.get(
    "/{artist_id}",
    response_model=ResponseHttp[Artist],
    summary="Artist detail with top songs and albums",
    responses=METADATA_ERRORS,
)
async def get_artist(
    request: Request, artist_id: Annotated[str, Path(pattern=ID_PATTERN, examples=["UCuAXFkgsw1L7xaCfnd5JJOw"])]
):
    response = await get_artist_controller().execute(artist_id)
    return json_response(request, response, cache_control=request.app.state.metadata_cache_control)


@router.get(
    "",
    deprecated=True,
    status_code=307,
    summary="Deprecated: use GET /api/artist/{artist_id}",
    description="Redirects (307) to `/api/artist/{artist_id}`. Will be removed in a future version.",
)
async def get_artist_legacy(request: Request, id: Annotated[str, Query(pattern=ID_PATTERN)]):
    return RedirectResponse(request.url_for("get_artist", artist_id=id), status_code=307)
