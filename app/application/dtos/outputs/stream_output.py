from dataclasses import dataclass

from pydantic import BaseModel

from app.domain.contracts.streaming import UpstreamAudio
from app.domain.models.stream import StreamSource


@dataclass
class AudioStream:
    """An open upstream audio response plus the source it came from."""

    source: StreamSource
    upstream: UpstreamAudio


class PrefetchResult(BaseModel):
    requested: int
    scheduled: int
    already_cached: int
