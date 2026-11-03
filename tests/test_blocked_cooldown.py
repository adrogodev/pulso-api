"""After YouTube blocks the server, stream requests fail fast instead of hammering YouTube again."""

import pytest

from tests.test_errors import download_error

BOT_CHECK = "Sign in to confirm you're not a bot. This helps protect our community."


async def test_block_fails_fast_for_every_video_during_cooldown(client, ydl):
    ydl.error = download_error(BOT_CHECK)
    first = await client.get("/api/stream/song_vid_01")
    ydl.error = None  # YouTube would answer now, but the server is still cooling down
    second = await client.get("/api/stream/video_vid_1/info")
    assert (first.status_code, second.status_code) == (503, 503)
    assert second.json()["error"]["code"] == "UPSTREAM_BLOCKED"
    assert ydl.calls == 1


async def test_rate_limit_also_starts_the_cooldown(client, ydl):
    ydl.error = download_error("HTTP Error 429: Too Many Requests")
    await client.get("/api/stream/song_vid_01")
    ydl.error = None
    resp = await client.get("/api/stream/song_vid_01/info")
    assert resp.json()["error"]["code"] == "UPSTREAM_RATE_LIMITED"
    assert ydl.calls == 1


async def test_resolution_resumes_after_the_cooldown(client, ydl, monkeypatch):
    import app.application.services.stream_resolver as resolver_module

    now = [1000.0]
    monkeypatch.setattr(resolver_module.time, "monotonic", lambda: now[0])
    ydl.error = download_error(BOT_CHECK)
    await client.get("/api/stream/song_vid_01")
    ydl.error = None
    now[0] += 61
    resp = await client.get("/api/stream/song_vid_01/info")
    assert resp.status_code == 200
    assert ydl.calls == 2


async def test_other_errors_do_not_start_a_cooldown(client, ydl):
    ydl.error = download_error("Video unavailable. This video has been removed by the uploader")
    assert (await client.get("/api/stream/song_vid_01")).status_code == 404
    ydl.error = None
    assert (await client.get("/api/stream/video_vid_1/info")).status_code == 200


@pytest.mark.parametrize("settings_overrides", [{"STREAM_BLOCKED_COOLDOWN_SECONDS": 0}])
async def test_zero_disables_the_cooldown(client, ydl):
    ydl.error = download_error(BOT_CHECK)
    await client.get("/api/stream/song_vid_01")
    ydl.error = None
    assert (await client.get("/api/stream/song_vid_01/info")).status_code == 200
