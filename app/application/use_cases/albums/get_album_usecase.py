from app.application.services.cached_loader import CachedLoader
from app.application.services.stream_links import StreamLinkBuilder
from app.domain.contracts.services.ytmusic.album_service import IAlbumService
from app.domain.models.ytmusic.album import Album
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract


class GetAlbumUseCase(UseCaseContract[str, Album]):
    def __init__(self, album_service: IAlbumService, loader: CachedLoader, links: StreamLinkBuilder, ttl: int):
        self._album_service = album_service
        self._loader = loader
        self._links = links
        self._ttl = ttl

    async def execute(self, args: UseCaseArgs[str]) -> Album:
        album_id = args.data

        async def load() -> Album:
            album = await self._album_service.get_album_data(album_id)
            self._links.apply(album.songs)
            return album

        return await self._loader.get_or_load(f"album:{album_id}", self._ttl, load, Album)
