from app.application.services.stream_links import StreamLinkBuilder
from app.domain.models.stream import ensure_video_id
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract


class GetSongLinkUseCase(UseCaseContract[str, str]):
    """Deprecated: kept for /api/songs. Returns this API's stream URL for the song."""

    def __init__(self, links: StreamLinkBuilder):
        self._links = links

    async def execute(self, args: UseCaseArgs[str]) -> str:
        return self._links.url_for(ensure_video_id(args.data))
