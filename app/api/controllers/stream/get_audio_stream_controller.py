from app.application.dtos.inputs.stream_input import AudioStreamRequest
from app.application.dtos.outputs.stream_output import AudioStream
from app.application.use_cases.stream.get_audio_stream_usecase import GetAudioStreamUseCase
from core.contracts.controller_contract import ControllerContract
from core.contracts.usecase_contract import UseCaseArgs


class GetAudioStreamController(ControllerContract):
    """Returns the open upstream audio; the router turns it into a streaming HTTP response."""

    def __init__(self, use_case: GetAudioStreamUseCase):
        self._use_case = use_case

    async def execute(self, video_id: str, range_header: str | None) -> AudioStream:
        req = AudioStreamRequest(video_id=video_id, range_header=range_header)
        return await self._use_case.execute(UseCaseArgs(data=req, context=None))
