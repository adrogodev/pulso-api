import logging
from typing import Awaitable, Callable, Type, TypeVar, Union

from pydantic import BaseModel

from app.domain.contracts.cache_port import CachePort
from core.concurrency.single_flight import SingleFlight

logger = logging.getLogger("pulso.cache")

M = TypeVar("M", bound=BaseModel)
Ttl = Union[float, Callable[[M], float]]


class CachedLoader:
    """Read-through cache with single-flight loading.

    Cache backend failures are logged and treated as misses so they never break a request.
    """

    def __init__(self, cache: CachePort, single_flight: SingleFlight | None = None):
        self._cache = cache
        self._single_flight = single_flight or SingleFlight()

    async def get_or_load(self, key: str, ttl: Ttl, loader: Callable[[], Awaitable[M]], model: Type[M]) -> M:
        cached = await self.peek(key, model)
        if cached is not None:
            return cached

        async def load() -> M:
            value = await loader()
            seconds = ttl(value) if callable(ttl) else ttl
            if seconds > 0:
                try:
                    await self._cache.set(key, value.model_dump_json().encode(), seconds)
                except Exception:
                    logger.exception("cache set failed for %s", key)
            return value

        return await self._single_flight.do(key, load)

    async def peek(self, key: str, model: Type[M]) -> M | None:
        try:
            raw = await self._cache.get(key)
        except Exception:
            logger.exception("cache get failed for %s", key)
            return None
        if raw is None:
            return None
        try:
            return model.model_validate_json(raw)
        except ValueError:
            logger.warning("discarding undecodable cache entry %s", key)
            return None

    async def invalidate(self, key: str) -> None:
        try:
            await self._cache.delete(key)
        except Exception:
            logger.exception("cache delete failed for %s", key)
