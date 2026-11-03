import time
from typing import Callable, Optional, Tuple

from cachetools import TLRUCache

from app.domain.contracts.cache_port import CachePort


class MemoryCache(CachePort):
    """In-process cache with per-entry TTL. Each uvicorn worker has its own copy."""

    def __init__(self, max_items: int, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._data: TLRUCache[str, Tuple[bytes, float]] = TLRUCache(
            maxsize=max_items, ttu=lambda _key, value, _now: value[1], timer=clock
        )

    async def get(self, key: str) -> Optional[bytes]:
        entry = self._data.get(key)
        return entry[0] if entry else None

    async def set(self, key: str, value: bytes, ttl: float) -> None:
        self._data[key] = (value, self._clock() + ttl)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def close(self) -> None:
        self._data.clear()
