from app.application.services.cached_loader import CachedLoader
from app.application.services.stream_links import StreamLinkBuilder
from app.application.services.stream_resolver import StreamResolver
from app.application.use_cases.albums.get_album_usecase import GetAlbumUseCase
from app.application.use_cases.artist.get_artist_usecase import GetArtistUseCase
from app.application.use_cases.search.search_suggestions_usecase import SearchSuggestionsUseCase
from app.application.use_cases.search.search_usecase import SearchUseCase
from app.application.use_cases.stream.get_audio_stream_usecase import GetAudioStreamUseCase
from app.application.use_cases.stream.get_song_link_usecase import GetSongLinkUseCase
from app.application.use_cases.stream.get_stream_info_usecase import GetStreamInfoUseCase
from app.application.use_cases.stream.prefetch_streams_usecase import PrefetchStreamsUseCase
from app.application.use_cases.watch.get_lyrics_usecase import GetLyricsUseCase
from app.application.use_cases.watch.get_watch_playlist_usecase import GetWatchPlaylistUseCase
from core.config.settings.env_settings import EnvSettings
from ioc.container import Container


def config_application(settings: EnvSettings):
    r = Container.resolve

    # Servicios compartidos
    Container.register('cached_loader', lambda: CachedLoader(r('cache')), singleton=True)
    Container.register('stream_links', lambda: StreamLinkBuilder(settings.public_base_url), singleton=True)
    Container.register(
        'stream_resolver',
        lambda: StreamResolver(
            r('audio_stream_provider'),
            r('cached_loader'),
            settings.STREAM_EXPIRY_MARGIN_SECONDS,
            settings.STREAM_BLOCKED_COOLDOWN_SECONDS,
        ),
        singleton=True,
    )

    # Registrar casos de uso
    Container.register(
        'search_usecase',
        lambda: SearchUseCase(r('search_service'), r('cached_loader'), r('stream_links'), settings.CACHE_TTL_SEARCH),
        singleton=True,
    )
    Container.register(
        'search_suggestions_usecase',
        lambda: SearchSuggestionsUseCase(r('search_service'), r('cached_loader'), settings.CACHE_TTL_SUGGESTIONS),
        singleton=True,
    )
    Container.register(
        'get_album_usecase',
        lambda: GetAlbumUseCase(r('album_service'), r('cached_loader'), r('stream_links'), settings.CACHE_TTL_ALBUM),
        singleton=True,
    )
    Container.register(
        'get_artist_usecase',
        lambda: GetArtistUseCase(r('artist_service'), r('cached_loader'), r('stream_links'), settings.CACHE_TTL_ARTIST),
        singleton=True,
    )
    Container.register(
        'get_watch_playlist_usecase',
        lambda: GetWatchPlaylistUseCase(r('watch_service'), r('cached_loader'), r('stream_links'), settings.CACHE_TTL_WATCH),
        singleton=True,
    )
    Container.register(
        'get_lyrics_usecase',
        lambda: GetLyricsUseCase(r('watch_service'), r('cached_loader'), settings.CACHE_TTL_LYRICS),
        singleton=True,
    )
    Container.register('get_link_songs_usecase', lambda: GetSongLinkUseCase(r('stream_links')), singleton=True)
    Container.register(
        'get_audio_stream_usecase',
        lambda: GetAudioStreamUseCase(
            r('stream_resolver'), r('audio_transport'), settings.STREAM_RETRY_DELAY_SECONDS
        ),
        singleton=True,
    )
    Container.register(
        'get_stream_info_usecase', lambda: GetStreamInfoUseCase(r('stream_resolver'), r('stream_links')), singleton=True
    )
    Container.register(
        'prefetch_streams_usecase',
        lambda: PrefetchStreamsUseCase(r('stream_resolver'), settings.STREAM_PREFETCH_MAX_IDS),
        singleton=True,
    )
