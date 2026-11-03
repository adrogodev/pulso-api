import asyncio
import logging
from typing import List, Set

from app.application.dtos.outputs.stream_output import PrefetchResult
from app.application.services.stream_resolver import StreamResolver
from app.domain.errors import DomainError
from app.domain.models.stream import ensure_video_id
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract

logger = logging.getLogger("rythmx.stream")


class PrefetchStreamsUseCase(UseCaseContract[List[str], PrefetchResult]):
    """Warms the stream cache in the background (e.g. for the playback queue)."""

    def __init__(self, resolver: StreamResolver):
        self._resolver = resolver
        self._tasks: Set[asyncio.Task] = set()

    async def execute(self, args: UseCaseArgs[List[str]]) -> PrefetchResult:
        ids = list(dict.fromkeys(ensure_video_id(v) for v in args.data))
        scheduled = 0
        for video_id in ids:
            if await self._resolver.is_cached(video_id):
                continue
            task = asyncio.create_task(self._warm(video_id))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
            scheduled += 1
        return PrefetchResult(requested=len(ids), scheduled=scheduled, already_cached=len(ids) - scheduled)

    async def _warm(self, video_id: str) -> None:
        try:
            await self._resolver.get(video_id)
        except DomainError as e:
            logger.info("prefetch of %s failed: %s", video_id, e.code)
        except Exception:
            logger.exception("prefetch of %s failed", video_id)

    async def wait_idle(self) -> None:
        """Waits for pending prefetches (used on shutdown and in tests)."""
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
