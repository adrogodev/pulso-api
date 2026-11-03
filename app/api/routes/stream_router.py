from typing import Annotated, Awaitable, Callable

import anyio
from fastapi import APIRouter, Path, Request
from fastapi.responses import StreamingResponse
from starlette.types import Receive, Scope, Send

from app.api.config.factory.dependencies_factory import (
    get_audio_stream_controller,
    get_stream_info_controller,
    prefetch_streams_controller,
)
from app.api.http.openapi import ERR_429, ERR_STREAM, STREAM_AUDIO, STREAM_INFO_EXAMPLE
from app.api.http.responses import json_response
from app.application.dtos.inputs.stream_input import PrefetchInput
from app.application.dtos.outputs.stream_output import PrefetchResult
from app.domain.models.stream import VIDEO_ID_PATTERN, StreamInfo
from core.models.response_model import ResponseHttp

router = APIRouter(prefix="/api/stream", tags=["Stream"])

VideoId = Annotated[str, Path(pattern=VIDEO_ID_PATTERN, examples=["dQw4w9WgXcQ"])]

# Headers copied from googlevideo; everything else (cookies, alt-svc, server info) is dropped
_FORWARDED_HEADERS = ("content-length", "content-range", "last-modified")


class UpstreamStreamingResponse(StreamingResponse):
    """StreamingResponse that always releases the upstream connection, even when the client
    disconnects before or during the transfer."""

    def __init__(self, *args, on_close: Callable[[], Awaitable[None]], **kwargs):
        super().__init__(*args, **kwargs)
        self._on_close = on_close

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            with anyio.CancelScope(shield=True):
                await self._on_close()


@router.get(
    "/{video_id}",
    response_class=StreamingResponse,
    summary="Play audio (proxy with HTTP Range support)",
    description=(
        "Use directly as `<audio src=\".../api/stream/{video_id}\">`. Forwards the `Range` header, answers "
        "206 with `Content-Range`, and streams in chunks without buffering the file."
    ),
    responses={**STREAM_AUDIO, **ERR_STREAM, **ERR_429},
)
async def stream_audio(request: Request, video_id: VideoId):
    stream = await get_audio_stream_controller().execute(video_id, request.headers.get("range"))
    upstream = stream.upstream

    headers = {"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=3600"}
    for name in _FORWARDED_HEADERS:
        if name in upstream.headers:
            headers[name.title()] = upstream.headers[name]

    media_type = upstream.headers.get("content-type", "")
    if not media_type.startswith("audio/"):
        media_type = stream.source.mime_type

    chunk_size = request.app.state.settings.STREAM_CHUNK_SIZE
    return UpstreamStreamingResponse(
        upstream.iter_bytes(chunk_size),
        status_code=upstream.status_code,
        headers=headers,
        media_type=media_type,
        on_close=upstream.close,
    )


@router.get(
    "/{video_id}/info",
    response_model=ResponseHttp[StreamInfo],
    summary="Stream metadata (format, bitrate, size, expiry)",
    responses={**STREAM_INFO_EXAMPLE, **ERR_STREAM, **ERR_429},
)
async def stream_info(request: Request, video_id: VideoId):
    response = await get_stream_info_controller().execute(video_id)
    return json_response(request, response, cache_control="private, max-age=60")


@router.post(
    "/prefetch",
    status_code=202,
    response_model=ResponseHttp[PrefetchResult],
    summary="Resolve stream URLs in the background (e.g. the playback queue)",
    responses={400: ERR_STREAM[400], **ERR_429},
)
async def prefetch(request: Request, body: PrefetchInput):
    response = await prefetch_streams_controller().execute(body.video_ids)
    return json_response(request, response, status_code=202)
