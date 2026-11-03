import time
from typing import Optional

from app.application.services.cached_loader import CachedLoader
from app.domain.contracts.streaming import AudioStreamProvider
from app.domain.errors import UpstreamBlockedError
from app.domain.models.stream import StreamSource, ensure_video_id


class StreamResolver:
    """Cached, single-flight resolution of audio URLs.

    Entries live until the URL's real expiry minus a safety margin, so a cached URL
    is never handed out when it is about to stop working.

    A block (bot check, rate limit) applies to the server's IP, not to one video, so for
    `blocked_cooldown_seconds` every resolution fails fast instead of asking YouTube again.
    """

    def __init__(
        self,
        provider: AudioStreamProvider,
        loader: CachedLoader,
        expiry_margin_seconds: int,
        blocked_cooldown_seconds: float = 0,
    ):
        self._provider = provider
        self._loader = loader
        self._margin = expiry_margin_seconds
        self._cooldown = blocked_cooldown_seconds
        self._blocked: Optional[UpstreamBlockedError] = None
        self._blocked_until = 0.0

    @staticmethod
    def cache_key(video_id: str) -> str:
        return f"stream:{video_id}"

    def _ttl(self, source: StreamSource) -> float:
        return source.seconds_to_expiry() - self._margin

    async def get(self, video_id: str) -> StreamSource:
        ensure_video_id(video_id)
        return await self._loader.get_or_load(
            self.cache_key(video_id), self._ttl, lambda: self._resolve(video_id), StreamSource
        )

    async def _resolve(self, video_id: str) -> StreamSource:
        if self._blocked is not None and time.monotonic() < self._blocked_until:
            raise UpstreamBlockedError(self._blocked.message, code=self._blocked.code)
        try:
            return await self._provider.resolve(video_id)
        except UpstreamBlockedError as e:
            if self._cooldown > 0:
                self._blocked, self._blocked_until = e, time.monotonic() + self._cooldown
            raise

    async def refresh(self, video_id: str) -> StreamSource:
        await self._loader.invalidate(self.cache_key(video_id))
        return await self.get(video_id)

    async def is_cached(self, video_id: str) -> bool:
        return await self._loader.peek(self.cache_key(video_id), StreamSource) is not None
