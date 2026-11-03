import asyncio
from typing import Any, Awaitable, Callable, Dict, TypeVar

T = TypeVar("T")


class SingleFlight:
    """Deduplicates concurrent calls by key: N simultaneous callers share one execution.

    The shared work runs in its own task, so a caller that gets cancelled (e.g. the HTTP
    client disconnected) does not cancel the work for the other callers.
    """

    def __init__(self) -> None:
        self._inflight: Dict[str, asyncio.Future[Any]] = {}

    async def do(self, key: str, fn: Callable[[], Awaitable[T]]) -> T:
        task = self._inflight.get(key)
        if task is None:
            task = asyncio.ensure_future(fn())
            self._inflight[key] = task
            task.add_done_callback(lambda t, k=key: self._forget(k, t))
        return await asyncio.shield(task)

    def in_flight(self, key: str) -> bool:
        return key in self._inflight

    def _forget(self, key: str, task: asyncio.Future[Any]) -> None:
        if self._inflight.get(key) is task:
            del self._inflight[key]
        if not task.cancelled():
            task.exception()  # mark as retrieved; callers already received it
