from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.api.config.factory.dependencies_factory import get_link_song_controller
from app.api.http.openapi import ERR_400
from app.api.http.responses import json_response
from core.models.response_model import ResponseHttp

router = APIRouter(prefix="/api/songs", tags=["Songs"])


@router.get(
    "",
    response_model=ResponseHttp[str],
    deprecated=True,
    summary="Deprecated: returns this API's stream URL for a song",
    description=(
        "Previously returned a YouTube Music link. It now returns `/api/stream/{video_id}` of this API. "
        "Migrate by using the `stream_url` field of search/album/watch results, or build "
        "`/api/stream/{video_id}` directly."
    ),
    responses=ERR_400,
)
async def get_link_song(request: Request, song_id: Annotated[str, Query(examples=["dQw4w9WgXcQ"])]):
    response = await get_link_song_controller().execute(song_id)
    return json_response(
        request,
        response,
        headers={"Deprecation": "true", "Link": f'<{response.data}>; rel="successor-version"'},
    )
