import math
from typing import Optional

from app.domain.contracts.cache_port import CachePort


class RedisCache(CachePort):
    """Shared cache for multi-worker deployments. Requires the `redis` extra."""

    def __init__(self, url: str, prefix: str = "rythmx:"):
        from redis.asyncio import Redis

        self._redis = Redis.from_url(url)
        self._prefix = prefix

    async def get(self, key: str) -> Optional[bytes]:
        return await self._redis.get(self._prefix + key)

    async def set(self, key: str, value: bytes, ttl: float) -> None:
        await self._redis.set(self._prefix + key, value, ex=max(1, math.ceil(ttl)))

    async def delete(self, key: str) -> None:
        await self._redis.delete(self._prefix + key)

    async def close(self) -> None:
        await self._redis.aclose()
