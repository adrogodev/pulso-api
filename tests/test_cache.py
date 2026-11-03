import asyncio

import pytest
from pydantic import BaseModel

from app.application.services.cached_loader import CachedLoader
from app.infrastructure.cache.memory_cache import MemoryCache
from core.concurrency.single_flight import SingleFlight


class Item(BaseModel):
    value: int


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


async def test_search_cache_hit_and_miss(client, ytmusic):
    await client.get("/api/search", params={"query": "daft punk"})
    await client.get("/api/search", params={"query": "DAFT  punk"})  # same normalized key: hit
    assert ytmusic.count("search") == 1
    await client.get("/api/search", params={"query": "daft punk", "filter": "songs"})  # different key: miss
    assert ytmusic.count("search") == 2


async def test_album_artist_lyrics_and_suggestions_are_cached(client, ytmusic):
    for _ in range(2):
        await client.get("/api/album/MPREb_album_1")
        await client.get("/api/artist/UC_artist_1")
        await client.get("/api/lyrics/song_vid_01")
        await client.get("/api/search/suggestions", params={"q": "daft"})
    assert ytmusic.count("get_album") == 1
    assert ytmusic.count("get_artist") == 1
    assert ytmusic.count("get_lyrics") == 1
    assert ytmusic.count("get_search_suggestions") == 1


async def test_errors_are_not_cached(client, ytmusic):
    ytmusic.errors["get_album"] = KeyError("contents")
    assert (await client.get("/api/album/MPREb_album_1")).status_code == 404
    del ytmusic.errors["get_album"]
    assert (await client.get("/api/album/MPREb_album_1")).status_code == 200
    assert ytmusic.count("get_album") == 2


async def test_memory_cache_entry_expires():
    clock = FakeClock()
    cache = MemoryCache(max_items=10, clock=clock)
    await cache.set("k", b"v", ttl=10)
    assert await cache.get("k") == b"v"
    clock.now += 9.9
    assert await cache.get("k") == b"v"
    clock.now += 0.2
    assert await cache.get("k") is None


async def test_cached_loader_hit_miss_and_expiry():
    clock = FakeClock()
    loader = CachedLoader(MemoryCache(max_items=10, clock=clock))
    calls = 0

    async def load() -> Item:
        nonlocal calls
        calls += 1
        return Item(value=calls)

    assert (await loader.get_or_load("k", 60, load, Item)).value == 1  # miss
    assert (await loader.get_or_load("k", 60, load, Item)).value == 1  # hit
    clock.now += 61
    assert (await loader.get_or_load("k", 60, load, Item)).value == 2  # expired -> miss
    assert calls == 2


async def test_cached_loader_ttl_from_value_and_non_positive_ttl_skips_cache():
    loader = CachedLoader(MemoryCache(max_items=10))
    calls = 0

    async def load() -> Item:
        nonlocal calls
        calls += 1
        return Item(value=-1)

    await loader.get_or_load("k", lambda item: item.value, load, Item)
    await loader.get_or_load("k", lambda item: item.value, load, Item)
    assert calls == 2


async def test_cache_backend_failure_degrades_to_miss():
    class BrokenCache:
        async def get(self, key):
            raise ConnectionError("redis down")

        async def set(self, key, value, ttl):
            raise ConnectionError("redis down")

        async def delete(self, key):
            raise ConnectionError("redis down")

        async def close(self):
            pass

    loader = CachedLoader(BrokenCache())

    async def load() -> Item:
        return Item(value=7)

    assert (await loader.get_or_load("k", 60, load, Item)).value == 7


async def test_single_flight_runs_once_for_concurrent_callers():
    flight = SingleFlight()
    calls = 0

    async def work():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return calls

    results = await asyncio.gather(*(flight.do("k", work) for _ in range(10)))
    assert results == [1] * 10
    assert calls == 1
    assert not flight.in_flight("k")


async def test_single_flight_shares_errors_and_allows_retry():
    flight = SingleFlight()

    async def boom():
        await asyncio.sleep(0.01)
        raise ValueError("nope")

    results = await asyncio.gather(*(flight.do("k", boom) for _ in range(3)), return_exceptions=True)
    assert all(isinstance(r, ValueError) for r in results)

    async def ok():
        return 1

    assert await flight.do("k", ok) == 1


async def test_single_flight_survives_leader_cancellation():
    flight = SingleFlight()

    async def work():
        await asyncio.sleep(0.05)
        return "done"

    leader = asyncio.create_task(flight.do("k", work))
    await asyncio.sleep(0)
    follower = asyncio.create_task(flight.do("k", work))
    await asyncio.sleep(0.01)
    leader.cancel()
    with pytest.raises(asyncio.CancelledError):
        await leader
    assert await follower == "done"
