from typing import Annotated

from fastapi import APIRouter, Path, Query, Request

from app.api.config.factory.dependencies_factory import get_lyrics_controller, get_watch_playlist_controller
from app.api.http.openapi import ERR_400, LYRICS_EXAMPLE, METADATA_ERRORS, WATCH_EXAMPLE
from app.api.http.responses import json_response
from app.domain.models.stream import VIDEO_ID_PATTERN
from app.domain.models.ytmusic.watch import Lyrics, WatchPlaylist
from core.models.response_model import ResponseHttp

router = APIRouter(prefix="/api", tags=["Watch"])

VideoId = Annotated[str, Path(pattern=VIDEO_ID_PATTERN, examples=["dQw4w9WgXcQ"])]


@router.get(
    "/watch/{video_id}",
    response_model=ResponseHttp[WatchPlaylist],
    summary="Up-next queue / radio for a song",
    description="Every track includes a `stream_url` that plays through this API.",
    responses={**WATCH_EXAMPLE, **ERR_400, **METADATA_ERRORS},
)
async def watch(request: Request, video_id: VideoId, limit: Annotated[int, Query(ge=1, le=50)] = 25):
    response = await get_watch_playlist_controller().execute((video_id, limit))
    return json_response(request, response, cache_control=request.app.state.metadata_cache_control)


@router.get(
    "/lyrics/{video_id}",
    response_model=ResponseHttp[Lyrics],
    summary="Song lyrics, when available",
    responses={**LYRICS_EXAMPLE, **ERR_400, **METADATA_ERRORS},
)
async def lyrics(request: Request, video_id: VideoId):
    response = await get_lyrics_controller().execute(video_id)
    return json_response(request, response, cache_control=request.app.state.metadata_cache_control)
