import pytest
import requests
from yt_dlp.utils import DownloadError, ExtractorError, GeoRestrictedError
from ytmusicapi.exceptions import YTMusicServerError


def download_error(message: str, cause: Exception | None = None) -> DownloadError:
    cause = cause or ExtractorError(message, expected=True)
    return DownloadError(f"ERROR: [youtube] abc: {message}", exc_info=(type(cause), cause, None))


@pytest.mark.parametrize(
    "error, status, code",
    [
        (download_error("Private video. Sign in if you've been granted access to this video"), 403, "CONTENT_PRIVATE"),
        (download_error("Sign in to confirm your age. This video may be inappropriate for some users."), 451, "AGE_RESTRICTED"),
        (
            download_error("The uploader has not made this video available in your country", GeoRestrictedError("geo")),
            451,
            "GEO_RESTRICTED",
        ),
        (download_error("Video unavailable. This video has been removed by the uploader"), 404, "VIDEO_NOT_FOUND"),
        (download_error("Requested format is not available. Use --list-formats"), 404, "AUDIO_FORMAT_UNAVAILABLE"),
        (download_error("Sign in to confirm you're not a bot. This helps protect our community."), 503, "UPSTREAM_BLOCKED"),
        (download_error("HTTP Error 429: Too Many Requests"), 503, "UPSTREAM_RATE_LIMITED"),
        (download_error("Read timed out."), 504, "UPSTREAM_TIMEOUT"),
        (download_error("Something unexpected"), 502, "UPSTREAM_UNAVAILABLE"),
        (RuntimeError("boom"), 502, "UPSTREAM_UNAVAILABLE"),
    ],
)
async def test_yt_dlp_errors_map_to_http(client, ydl, error, status, code):
    ydl.error = error
    for path in ("/api/stream/song_vid_01", "/api/stream/song_vid_01/info"):
        resp = await client.get(path)
        assert resp.status_code == status
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == code
        assert body["message"]


@pytest.mark.parametrize(
    "error, status, code",
    [
        (YTMusicServerError("Server returned HTTP 400: Bad Request.\nInvalid argument"), 404, "NOT_FOUND"),
        (YTMusicServerError("Server returned HTTP 500: Internal Server Error.\n"), 502, "UPSTREAM_UNAVAILABLE"),
        (requests.ConnectionError("refused"), 502, "UPSTREAM_UNAVAILABLE"),
        (requests.ReadTimeout("slow"), 504, "UPSTREAM_TIMEOUT"),
        (KeyError("contents"), 404, "NOT_FOUND"),
    ],
)
async def test_ytmusic_errors_map_to_http(client, ytmusic, error, status, code):
    ytmusic.errors["get_album"] = error
    resp = await client.get("/api/album/MPREb_album_1")
    assert resp.status_code == status
    assert resp.json()["error"]["code"] == code


async def test_unexpected_error_returns_500_envelope(app, ytmusic):
    import httpx

    ytmusic.errors["search"] = ZeroDivisionError("bug")
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        resp = await c.get("/api/search", params={"query": "x"})
    assert resp.status_code == 500
    assert resp.json() == {"success": False, "message": "Internal server error", "error": {"code": "INTERNAL_ERROR"}}


async def test_unknown_route_uses_envelope(client):
    resp = await client.get("/api/nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "HTTP_404"
