from app.application.services.cached_loader import CachedLoader
from app.domain.contracts.services.ytmusic.watch_service import IWatchService
from app.domain.models.stream import ensure_video_id
from app.domain.models.ytmusic.watch import Lyrics
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract


class GetLyricsUseCase(UseCaseContract[str, Lyrics]):
    def __init__(self, service: IWatchService, loader: CachedLoader, ttl: int):
        self._service = service
        self._loader = loader
        self._ttl = ttl

    async def execute(self, args: UseCaseArgs[str]) -> Lyrics:
        video_id = ensure_video_id(args.data)
        return await self._loader.get_or_load(
            f"lyrics:{video_id}", self._ttl, lambda: self._service.get_lyrics(video_id), Lyrics
        )
