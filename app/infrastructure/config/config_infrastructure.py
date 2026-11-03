import ytmusicapi

from app.infrastructure.cache.memory_cache import MemoryCache
from app.infrastructure.services.streaming.httpx_audio_transport import HttpxAudioTransport, build_http_client
from app.infrastructure.services.streaming.ytdlp_stream_adapter import YtDlpStreamAdapter
from app.infrastructure.services.ytmusic.client import TimeoutSession, YTMusicGateway
from app.infrastructure.services.ytmusic.services.album_service import AlbumService
from app.infrastructure.services.ytmusic.services.artist_service import ArtistService
from app.infrastructure.services.ytmusic.services.search_service import SearchService
from app.infrastructure.services.ytmusic.services.watch_service import WatchService
from core.config.settings.env_settings import EnvSettings
from ioc.container import Container

YTMUSIC_REQUEST_TIMEOUT = 15


def _build_cache(settings: EnvSettings):
    if settings.CACHE_BACKEND == "redis":
        from app.infrastructure.cache.redis_cache import RedisCache

        return RedisCache(settings.REDIS_URL)
    return MemoryCache(settings.CACHE_MAX_ITEMS)


def config_infrastructure(settings: EnvSettings):

    # Registrar clientes (una sola instancia de YTMusic y de httpx por proceso)
    Container.register(
        'ytmusic_client',
        lambda: ytmusicapi.YTMusic(
            language=settings.YTMUSIC_LANGUAGE,
            location=settings.YTMUSIC_LOCATION,
            requests_session=TimeoutSession(YTMUSIC_REQUEST_TIMEOUT),
        ),
        singleton=True,
    )
    Container.register(
        'ytmusic_gateway',
        lambda: YTMusicGateway(Container.resolve('ytmusic_client'), settings.YTMUSIC_MAX_CONCURRENCY),
        singleton=True,
    )
    Container.register(
        'http_client',
        lambda: build_http_client(
            http2=settings.HTTP2_ENABLED,
            connect_timeout=settings.HTTP_CONNECT_TIMEOUT,
            read_timeout=settings.HTTP_READ_TIMEOUT,
            max_connections=settings.HTTP_MAX_CONNECTIONS,
            max_keepalive=settings.HTTP_MAX_KEEPALIVE,
            keepalive_expiry=settings.HTTP_KEEPALIVE_EXPIRY,
            proxy=settings.YTDLP_PROXY,
        ),
        singleton=True,
    )
    Container.register('cache', lambda: _build_cache(settings), singleton=True)

    # Registrar servicios
    Container.register('search_service', lambda: SearchService(Container.resolve('ytmusic_gateway')), singleton=True)
    Container.register('album_service', lambda: AlbumService(Container.resolve('ytmusic_gateway')), singleton=True)
    Container.register('artist_service', lambda: ArtistService(Container.resolve('ytmusic_gateway')), singleton=True)
    Container.register('watch_service', lambda: WatchService(Container.resolve('ytmusic_gateway')), singleton=True)

    # Streaming
    Container.register(
        'audio_stream_provider',
        lambda: YtDlpStreamAdapter(
            format_selector=settings.STREAM_FORMAT,
            max_concurrency=settings.YTDLP_MAX_CONCURRENCY,
            fallback_ttl_seconds=settings.STREAM_FALLBACK_TTL_SECONDS,
            js_runtime=settings.YTDLP_JS_RUNTIME,
            ydl_factory=Container.resolve('ytdlp_factory') if Container.is_registered('ytdlp_factory') else None,
            cookies_file=settings.YTDLP_COOKIES_FILE,
            proxy=settings.YTDLP_PROXY,
            extractor_args=settings.YTDLP_EXTRACTOR_ARGS,
        ),
        singleton=True,
    )
    Container.register(
        'audio_transport',
        lambda: HttpxAudioTransport(Container.resolve('http_client'), settings.STREAM_UPSTREAM_WINDOW_BYTES),
        singleton=True,
    )
