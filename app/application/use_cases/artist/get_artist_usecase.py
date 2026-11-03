from app.application.services.cached_loader import CachedLoader
from app.application.services.stream_links import StreamLinkBuilder
from app.domain.contracts.services.ytmusic.artist_service import IArtistService
from app.domain.models.ytmusic.artist import Artist
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract


class GetArtistUseCase(UseCaseContract[str, Artist]):
    def __init__(self, artist_service: IArtistService, loader: CachedLoader, links: StreamLinkBuilder, ttl: int):
        self._artist_service = artist_service
        self._loader = loader
        self._links = links
        self._ttl = ttl

    async def execute(self, args: UseCaseArgs[str]) -> Artist:
        artist_id = args.data

        async def load() -> Artist:
            artist = await self._artist_service.get_artist(artist_id)
            self._links.apply(artist.songs)
            return artist

        return await self._loader.get_or_load(f"artist:{artist_id}", self._ttl, load, Artist)
