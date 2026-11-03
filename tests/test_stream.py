import asyncio
import time

import pytest

from tests.conftest import AUDIO

SIZE = len(AUDIO)


async def test_full_stream_without_range(client, googlevideo):
    resp = await client.get("/api/stream/song_vid_01")
    assert resp.status_code == 200
    assert resp.content == AUDIO
    assert resp.headers["content-type"] == "audio/mp4"
    assert resp.headers["content-length"] == str(SIZE)
    assert resp.headers["accept-ranges"] == "bytes"
    assert "range" not in googlevideo.requests[0].headers


async def test_range_request_returns_206_with_content_range(client, googlevideo):
    resp = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=100-1123"})
    assert resp.status_code == 206
    assert resp.content == AUDIO[100:1124]
    assert resp.headers["content-range"] == f"bytes 100-1123/{SIZE}"
    assert resp.headers["content-length"] == "1024"
    assert resp.headers["accept-ranges"] == "bytes"
    assert resp.headers["content-type"] == "audio/mp4"
    upstream = googlevideo.requests[0]
    assert upstream.headers["range"] == "bytes=100-1123"
    assert upstream.headers["user-agent"] == "test-agent"
    assert upstream.headers["accept-encoding"] == "identity"
    # upstream cookies never leak to the client
    assert "set-cookie" not in resp.headers


async def test_safari_probe_and_open_ended_range(client):
    probe = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-1"})
    assert probe.status_code == 206
    assert probe.headers["content-range"] == f"bytes 0-1/{SIZE}"
    assert probe.content == AUDIO[:2]

    tail = await client.get("/api/stream/song_vid_01", headers={"Range": f"bytes={SIZE - 10}-"})
    assert tail.status_code == 206
    assert tail.content == AUDIO[-10:]
    assert tail.headers["content-range"] == f"bytes {SIZE - 10}-{SIZE - 1}/{SIZE}"


async def test_unsatisfiable_range_passes_through_416(client):
    resp = await client.get("/api/stream/song_vid_01", headers={"Range": f"bytes={SIZE + 5}-"})
    assert resp.status_code == 416
    assert resp.headers["content-range"] == f"bytes */{SIZE}"


async def test_stream_is_never_gzipped(client):
    resp = await client.get("/api/stream/song_vid_01", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in resp.headers
    assert resp.content == AUDIO


async def test_resolution_is_cached_between_requests(client, ydl):
    for _ in range(3):
        await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-9"})
    assert ydl.calls == 1


async def test_expired_upstream_url_is_re_resolved_once(client, ydl, googlevideo):
    googlevideo.forbidden_n = {"1"}  # the first resolved URL answers 403
    resp = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-9"})
    assert resp.status_code == 206
    assert resp.content == AUDIO[:10]
    assert ydl.calls == 2
    assert [r.url.params["n"] for r in googlevideo.requests] == ["1", "2"]
    # the refreshed URL replaced the cached one
    await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-9"})
    assert ydl.calls == 2


async def test_persistent_403_maps_to_503_without_loops(client, ydl, googlevideo):
    googlevideo.always_status = 403
    resp = await client.get("/api/stream/song_vid_01")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "UPSTREAM_BLOCKED"
    assert ydl.calls == 2
    assert len(googlevideo.requests) == 2


async def test_upstream_server_error_maps_to_502(client, googlevideo):
    googlevideo.always_status = 500
    resp = await client.get("/api/stream/song_vid_01")
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"


async def test_invalid_video_id_is_rejected_before_yt_dlp(client, ydl):
    resp = await client.get("/api/stream/not-a-valid-id-at-all")
    assert resp.status_code == 422
    assert ydl.calls == 0


async def test_stream_info(client):
    resp = await client.get("/api/stream/song_vid_01/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    info = body["data"]
    assert info["format_id"] == "140"
    assert info["mime_type"] == "audio/mp4"
    assert info["codec"] == "mp4a.40.2"
    assert info["bitrate_kbps"] == 129.5
    assert info["duration_seconds"] == 369
    assert info["filesize"] == SIZE
    assert info["expires_at"] > time.time()
    assert info["stream_url"] == "http://testserver/api/stream/song_vid_01"
    # the signed googlevideo URL is never exposed
    assert "googlevideo" not in resp.text


async def test_prefetch_warms_cache_in_background(app, client, ydl):
    resp = await client.post(
        "/api/stream/prefetch", json={"video_ids": ["song_vid_01", "track_vid_1", "song_vid_01"]}
    )
    assert resp.status_code == 202
    assert resp.json()["data"] == {"requested": 2, "scheduled": 2, "already_cached": 0}

    from ioc.container import Container

    await Container.resolve("prefetch_streams_usecase").wait_idle()
    assert ydl.calls == 2

    again = await client.post("/api/stream/prefetch", json={"video_ids": ["song_vid_01"]})
    assert again.json()["data"] == {"requested": 1, "scheduled": 0, "already_cached": 1}
    await client.get("/api/stream/song_vid_01/info")
    assert ydl.calls == 2


async def test_prefetch_validates_ids(client):
    resp = await client.post("/api/stream/prefetch", json={"video_ids": ["bad id"]})
    assert resp.status_code == 422
    empty = await client.post("/api/stream/prefetch", json={"video_ids": []})
    assert empty.status_code == 422


async def test_concurrent_requests_resolve_once(client, ydl):
    ydl.latency = 0.2
    responses = await asyncio.gather(*(client.get("/api/stream/song_vid_01/info") for _ in range(8)))
    assert all(r.status_code == 200 for r in responses)
    assert ydl.calls == 1


@pytest.mark.parametrize("settings_overrides", [{"STREAM_EXPIRY_MARGIN_SECONDS": 300}])
async def test_url_close_to_expiry_is_not_cached(client, ydl):
    ydl.expire_in = 200  # less than the safety margin
    await client.get("/api/stream/song_vid_01/info")
    await client.get("/api/stream/song_vid_01/info")
    assert ydl.calls == 2


async def test_client_disconnect_closes_upstream():
    from app.api.routes.stream_router import UpstreamStreamingResponse

    closed = asyncio.Event()

    async def endless():
        while True:
            yield b"x" * 1024
            await asyncio.sleep(0.01)

    async def on_close():
        closed.set()

    response = UpstreamStreamingResponse(endless(), media_type="audio/mp4", on_close=on_close)
    sent = []

    async def receive():
        await asyncio.sleep(0.05)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message["type"])

    scope = {"type": "http", "asgi": {"spec_version": "2.3"}, "method": "GET", "headers": []}
    await asyncio.wait_for(response(scope, receive, send), timeout=2)
    assert closed.is_set()
    assert "http.response.start" in sent


@pytest.mark.parametrize("bad_id", ["song_vid_01\n", "song_vid_01\r\n", "song_vid_0", "song vid 01"])
async def test_video_id_guard_rejects_malformed_ids(client, bad_id):
    resp = await client.get("/api/songs", params={"song_id": bad_id})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_VIDEO_ID"


@pytest.mark.parametrize("settings_overrides", [{"STREAM_PREFETCH_MAX_IDS": 2}])
async def test_prefetch_respects_configured_max_ids(client, ydl):
    resp = await client.post(
        "/api/stream/prefetch", json={"video_ids": ["song_vid_01", "track_vid_1", "video_vid_1"]}
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "TOO_MANY_IDS"
    assert ydl.calls == 0
