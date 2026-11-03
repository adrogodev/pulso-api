from typing import AsyncIterator, Dict, Optional, Protocol

from app.domain.models.stream import StreamSource


class AudioStreamProvider(Protocol):
    """Resolves a video id into a direct, time-limited audio URL."""

    async def resolve(self, video_id: str) -> StreamSource: ...


class UpstreamAudio(Protocol):
    """An open upstream audio response. Must be closed by the consumer."""

    status_code: int
    headers: Dict[str, str]

    def iter_bytes(self, chunk_size: int) -> AsyncIterator[bytes]: ...

    async def close(self) -> None: ...


class AudioTransport(Protocol):
    """Opens the byte stream behind a resolved source, forwarding an optional Range header."""

    async def open(self, source: StreamSource, range_header: Optional[str]) -> UpstreamAudio: ...
