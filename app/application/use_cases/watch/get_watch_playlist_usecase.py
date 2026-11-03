from app.application.services.cached_loader import CachedLoader
from app.application.services.stream_links import StreamLinkBuilder
from app.domain.contracts.services.ytmusic.watch_service import IWatchService
from app.domain.models.stream import ensure_video_id
from app.domain.models.ytmusic.watch import WatchPlaylist
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract


class GetWatchPlaylistUseCase(UseCaseContract[tuple[str, int], WatchPlaylist]):
    def __init__(self, service: IWatchService, loader: CachedLoader, links: StreamLinkBuilder, ttl: int):
        self._service = service
        self._loader = loader
        self._links = links
        self._ttl = ttl

    async def execute(self, args: UseCaseArgs[tuple[str, int]]) -> WatchPlaylist:
        video_id, limit = args.data
        ensure_video_id(video_id)

        async def load() -> WatchPlaylist:
            playlist = await self._service.get_watch_playlist(video_id, limit)
            self._links.apply(playlist.tracks)
            return playlist

        return await self._loader.get_or_load(f"watch:{video_id}:{limit}", self._ttl, load, WatchPlaylist)
