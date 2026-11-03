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
    assert "content-range" not in resp.headers
    # googlevideo throttles and drops requests without Range, so the proxy always sends one
    assert googlevideo.requests[0].headers["range"] == "bytes=0-10485759"


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
    # same URL retried once first, then re-resolved once
    assert [r.url.params["n"] for r in googlevideo.requests] == ["1", "1", "2"]
    # the refreshed URL replaced the cached one
    await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-9"})
    assert ydl.calls == 2


async def test_persistent_403_maps_to_503_without_loops(client, ydl, googlevideo):
    googlevideo.always_status = 403
    resp = await client.get("/api/stream/song_vid_01")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "UPSTREAM_BLOCKED"
    assert ydl.calls == 2
    assert [r.url.params["n"] for r in googlevideo.requests] == ["1", "1", "2", "2"]


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


async def test_upstream_drop_mid_stream_ends_response_without_error_log(client, googlevideo, caplog):
    googlevideo.fail_after_bytes = 100_000  # more than one 64 KB chunk
    with caplog.at_level("WARNING"):
        resp = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-"})
    assert resp.status_code == 206
    assert 0 < len(resp.content) < SIZE
    assert not any(r.levelname == "ERROR" for r in caplog.records)
    assert any("dropped" in r.message for r in caplog.records)


async def test_transient_403_on_fresh_url_is_retried_without_re_resolving(client, ydl, googlevideo):
    # googlevideo sometimes rejects the very first hit on a just-issued URL
    googlevideo.transient_403_n = {"1"}
    resp = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-9"})
    assert resp.status_code == 206
    assert resp.content == AUDIO[:10]
    assert ydl.calls == 1
    assert [r.url.params["n"] for r in googlevideo.requests] == ["1", "1"]


async def test_gone_url_is_re_resolved_immediately(client, ydl, googlevideo):
    googlevideo.gone_n = {"1"}
    resp = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-9"})
    assert resp.status_code == 206
    assert [r.url.params["n"] for r in googlevideo.requests] == ["1", "2"]


WINDOW = 50_000


@pytest.mark.parametrize("settings_overrides", [{"STREAM_UPSTREAM_WINDOW_BYTES": WINDOW}])
async def test_full_download_is_fetched_in_bounded_upstream_windows(client, googlevideo):
    # googlevideo throttles ranges larger than ~10 MB, so upstream is read window by window
    resp = await client.get("/api/stream/song_vid_01")
    assert resp.status_code == 200
    assert resp.content == AUDIO
    assert resp.headers["content-length"] == str(SIZE)
    assert "content-range" not in resp.headers
    assert [r.headers["range"] for r in googlevideo.requests] == [
        "bytes=0-49999", "bytes=50000-99999", "bytes=100000-149999", "bytes=150000-199999"
    ]


@pytest.mark.parametrize("settings_overrides", [{"STREAM_UPSTREAM_WINDOW_BYTES": WINDOW}])
async def test_client_range_spanning_windows_keeps_its_content_range(client, googlevideo):
    resp = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=10-120009"})
    assert resp.status_code == 206
    assert resp.content == AUDIO[10:120010]
    assert resp.headers["content-range"] == f"bytes 10-120009/{SIZE}"
    assert resp.headers["content-length"] == "120000"
    assert [r.headers["range"] for r in googlevideo.requests] == [
        "bytes=10-50009", "bytes=50010-100009", "bytes=100010-120009"
    ]


@pytest.mark.parametrize("settings_overrides", [{"STREAM_UPSTREAM_WINDOW_BYTES": WINDOW}])
async def test_open_ended_client_range_reads_until_end_of_file(client):
    resp = await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=60000-"})
    assert resp.status_code == 206
    assert resp.content == AUDIO[60000:]
    assert resp.headers["content-range"] == f"bytes 60000-{SIZE - 1}/{SIZE}"


@pytest.mark.parametrize("settings_overrides", [{"STREAM_UPSTREAM_WINDOW_BYTES": WINDOW}])
async def test_failing_later_window_ends_body_early_without_error(client, googlevideo, caplog):
    googlevideo.forbid_from_byte = 100_000
    with caplog.at_level("WARNING"):
        resp = await client.get("/api/stream/song_vid_01")
    assert resp.status_code == 200
    assert resp.content == AUDIO[:100_000]
    assert not any(r.levelname == "ERROR" for r in caplog.records)


async def test_multi_range_is_passed_through_untouched(client, googlevideo):
    await client.get("/api/stream/song_vid_01", headers={"Range": "bytes=0-9, 20-29"})
    assert googlevideo.requests[0].headers["range"] == "bytes=0-9, 20-29"


@pytest.mark.parametrize("settings_overrides", [{"STREAM_UPSTREAM_WINDOW_BYTES": WINDOW}])
async def test_short_upstream_windows_never_skip_bytes(client, googlevideo):
    # upstream may answer a 206 shorter than the window requested; the next window starts after it
    googlevideo.max_response_bytes = 30_000
    resp = await client.get("/api/stream/song_vid_01")
    assert resp.status_code == 200
    assert resp.content == AUDIO
