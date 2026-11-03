"""Shared OpenAPI response documentation and examples (rendered by Scalar at /docs)."""

from typing import Any, Dict

from core.models.response_model import ResponseErrorHttp

ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


def _error(description: str, code: str, message: str) -> Dict[str, Any]:
    return {
        "model": ResponseErrorHttp,
        "description": description,
        "content": {
            "application/json": {"example": {"success": False, "message": message, "error": {"code": code}}}
        },
    }


ERR_400 = {400: _error("Invalid input", "INVALID_VIDEO_ID", "Invalid video id")}
ERR_404 = {404: _error("Not found", "NOT_FOUND", "Resource not found on YouTube Music")}
ERR_429 = {429: _error("Rate limited (see Retry-After)", "RATE_LIMITED", "Too many requests")}
ERR_UPSTREAM = {
    502: _error("YouTube failed", "UPSTREAM_UNAVAILABLE", "YouTube Music returned an error"),
    503: _error("YouTube blocked this server", "UPSTREAM_BLOCKED", "YouTube is asking this server to sign in (bot check)"),
    504: _error("YouTube timed out", "UPSTREAM_TIMEOUT", "YouTube Music did not answer in time"),
}
ERR_STREAM = {
    **ERR_400,
    403: _error("Private video", "CONTENT_PRIVATE", "This video is private"),
    404: _error("Video or audio format unavailable", "VIDEO_NOT_FOUND", "Video not found or unavailable"),
    451: _error("Age or region restricted", "AGE_RESTRICTED", "This video is age restricted"),
    **ERR_UPSTREAM,
}
METADATA_ERRORS = {**ERR_404, **ERR_429, **ERR_UPSTREAM}

_SONG = {
    "id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "thumbnail": "https://lh3.googleusercontent.com/abc",
    "duration": "3:33",
    "duration_seconds": 213,
    "artists": [{"id": "UCuAXFkgsw1L7xaCfnd5JJOw", "name": "Rick Astley", "songs": [], "albums": []}],
    "stream_url": "http://localhost:8000/api/stream/dQw4w9WgXcQ",
}


def ok_example(data: Any, message: str = "OK") -> Dict[int, Dict[str, Any]]:
    return {200: {"content": {"application/json": {"example": {"success": True, "message": message, "data": data}}}}}


SEARCH_EXAMPLE = ok_example(
    {"artists": [], "songs": [_SONG], "videos": [], "albums": []}, "Busqueda exitosa"
)
SUGGESTIONS_EXAMPLE = ok_example(
    {"query": "never gon", "suggestions": ["never gonna give you up", "never gonna let you down"]},
    "Sugerencias obtenidas exitosamente",
)
STREAM_INFO_EXAMPLE = ok_example(
    {
        "video_id": "dQw4w9WgXcQ",
        "format_id": "140",
        "mime_type": "audio/mp4",
        "ext": "m4a",
        "codec": "mp4a.40.2",
        "bitrate_kbps": 129.5,
        "duration_seconds": 213,
        "filesize": 3449447,
        "expires_at": 1793750400,
        "stream_url": "http://localhost:8000/api/stream/dQw4w9WgXcQ",
    },
    "Informacion del stream obtenida exitosamente",
)
WATCH_EXAMPLE = ok_example(
    {"video_id": "dQw4w9WgXcQ", "playlist_id": "RDAMVMdQw4w9WgXcQ", "tracks": [_SONG]},
    "Cola de reproduccion obtenida exitosamente",
)
LYRICS_EXAMPLE = ok_example(
    {"video_id": "dQw4w9WgXcQ", "text": "We're no strangers to love...", "source": "Source: Musixmatch"},
    "Letra obtenida exitosamente",
)
STREAM_AUDIO = {
    200: {"description": "Full audio (no Range header)", "content": {"audio/mp4": {}, "audio/webm": {}}},
    206: {
        "description": "Partial audio for a `Range: bytes=start-end` request, with Content-Range",
        "content": {"audio/mp4": {}, "audio/webm": {}},
    },
    416: {"description": "Requested range not satisfiable"},
}
