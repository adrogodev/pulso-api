import asyncio
import logging
from typing import Optional

from app.application.dtos.inputs.stream_input import AudioStreamRequest
from app.application.dtos.outputs.stream_output import AudioStream
from app.application.services.stream_resolver import StreamResolver
from app.domain.contracts.streaming import AudioTransport, UpstreamAudio
from app.domain.errors import UpstreamBlockedError, UpstreamUnavailableError
from app.domain.models.stream import StreamSource
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract

logger = logging.getLogger("pulso.stream")

FORBIDDEN = 403
GONE = 410


class GetAudioStreamUseCase(UseCaseContract[AudioStreamRequest, AudioStream]):
    def __init__(self, resolver: StreamResolver, transport: AudioTransport, retry_delay_seconds: float):
        self._resolver = resolver
        self._transport = transport
        self._retry_delay = retry_delay_seconds

    async def _open(self, source: StreamSource, range_header: Optional[str]) -> UpstreamAudio:
        """Opens the URL, retrying a 403 once after a short pause: googlevideo sometimes rejects
        the very first hit on a freshly issued URL and accepts it moments later."""
        upstream = await self._transport.open(source, range_header)
        if upstream.status_code == FORBIDDEN:
            await upstream.close()
            await asyncio.sleep(self._retry_delay)
            upstream = await self._transport.open(source, range_header)
        return upstream

    async def execute(self, args: UseCaseArgs[AudioStreamRequest]) -> AudioStream:
        req = args.data
        source = await self._resolver.get(req.video_id)
        upstream = await self._open(source, req.range_header)

        if upstream.status_code in (FORBIDDEN, GONE):
            # The cached URL expired or was revoked: resolve again exactly once and retry
            logger.info("upstream %s for %s, re-resolving", upstream.status_code, req.video_id)
            await upstream.close()
            source = await self._resolver.refresh(req.video_id)
            upstream = await self._open(source, req.range_header)
            if upstream.status_code in (FORBIDDEN, GONE):
                await upstream.close()
                raise UpstreamBlockedError("YouTube refused the audio stream")

        # 416 is a valid answer to an out-of-bounds Range and is passed through
        if upstream.status_code >= 400 and upstream.status_code != 416:
            await upstream.close()
            raise UpstreamUnavailableError(f"Upstream audio answered {upstream.status_code}")

        return AudioStream(source=source, upstream=upstream)
