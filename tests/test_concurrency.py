"""The blocking libraries (ytmusicapi, yt-dlp) must never block the event loop."""

import asyncio
import time


async def test_concurrent_ytmusic_calls_run_in_parallel(client, ytmusic):
    ytmusic.latency = 0.3
    started = time.perf_counter()
    responses = await asyncio.gather(
        *(client.get("/api/search", params={"query": f"query {i}"}) for i in range(5))
    )
    elapsed = time.perf_counter() - started
    assert all(r.status_code == 200 for r in responses)
    # serial execution would take ~1.5 s
    assert elapsed < 0.9


async def test_event_loop_stays_responsive_during_slow_calls(client, ytmusic, ydl):
    ytmusic.latency = 0.5
    ydl.latency = 0.5
    slow = [
        asyncio.create_task(client.get("/api/album/MPREb_album_1")),
        asyncio.create_task(client.get("/api/stream/song_vid_01/info")),
    ]
    await asyncio.sleep(0.05)
    started = time.perf_counter()
    health = await client.get("/")
    assert health.status_code == 200
    assert time.perf_counter() - started < 0.2
    await asyncio.gather(*slow)


async def test_single_ytmusic_instance_is_reused(app):
    from ioc.container import Container

    assert Container.resolve("ytmusic_client") is Container.resolve("ytmusic_client")
    assert Container.resolve("search_controller") is Container.resolve("search_controller")
