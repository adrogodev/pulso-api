import logging

from app.application.dtos.inputs.stream_input import AudioStreamRequest
from app.application.dtos.outputs.stream_output import AudioStream
from app.application.services.stream_resolver import StreamResolver
from app.domain.contracts.streaming import AudioTransport
from app.domain.errors import UpstreamBlockedError, UpstreamUnavailableError
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract

logger = logging.getLogger("rythmx.stream")

# googlevideo answers these when a signed URL expired or was revoked
EXPIRED_STATUSES = {403, 410}


class GetAudioStreamUseCase(UseCaseContract[AudioStreamRequest, AudioStream]):
    def __init__(self, resolver: StreamResolver, transport: AudioTransport):
        self._resolver = resolver
        self._transport = transport

    async def execute(self, args: UseCaseArgs[AudioStreamRequest]) -> AudioStream:
        req = args.data
        source = await self._resolver.get(req.video_id)
        upstream = await self._transport.open(source, req.range_header)

        if upstream.status_code in EXPIRED_STATUSES:
            # The cached URL stopped working: resolve again exactly once and retry
            logger.info("upstream %s for %s, re-resolving", upstream.status_code, req.video_id)
            await upstream.close()
            source = await self._resolver.refresh(req.video_id)
            upstream = await self._transport.open(source, req.range_header)
            if upstream.status_code in EXPIRED_STATUSES:
                await upstream.close()
                raise UpstreamBlockedError("YouTube refused the audio stream")

        # 416 is a valid answer to an out-of-bounds Range and is passed through
        if upstream.status_code >= 400 and upstream.status_code != 416:
            await upstream.close()
            raise UpstreamUnavailableError(f"Upstream audio answered {upstream.status_code}")

        return AudioStream(source=source, upstream=upstream)
