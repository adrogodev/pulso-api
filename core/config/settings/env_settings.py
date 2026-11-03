from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Public URL of this API, used to build stream_url fields
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # CORS: comma separated origins, or "*" (credentials are disabled with "*")
    CORS_ORIGINS: str = "*"

    # TLS: use the OS certificate store (needed behind TLS-inspecting proxies)
    USE_SYSTEM_TRUSTSTORE: bool = False

    # YouTube Music client
    YTMUSIC_LANGUAGE: str = "en"
    YTMUSIC_LOCATION: str = ""
    YTMUSIC_MAX_CONCURRENCY: int = 8

    # Cache
    CACHE_BACKEND: Literal["memory", "redis"] = "memory"
    CACHE_MAX_ITEMS: int = 4096
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SEARCH: int = 600
    CACHE_TTL_SUGGESTIONS: int = 600
    CACHE_TTL_ALBUM: int = 21600
    CACHE_TTL_ARTIST: int = 21600
    CACHE_TTL_WATCH: int = 600
    CACHE_TTL_LYRICS: int = 86400

    # HTTP Cache-Control max-age for metadata endpoints
    HTTP_CACHE_MAX_AGE: int = 300

    # Audio streaming
    STREAM_FORMAT: str = "140/251/bestaudio[ext=m4a]/bestaudio"
    STREAM_EXPIRY_MARGIN_SECONDS: int = 300
    STREAM_FALLBACK_TTL_SECONDS: int = 1800
    STREAM_CHUNK_SIZE: int = 65536
    STREAM_PREFETCH_MAX_IDS: int = 50
    YTDLP_MAX_CONCURRENCY: int = 4
    YTDLP_JS_RUNTIME: str = "deno"

    # Outgoing HTTP client (audio proxy)
    HTTP_CONNECT_TIMEOUT: float = 5.0
    HTTP_READ_TIMEOUT: float = 30.0
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE: int = 20
    HTTP_KEEPALIVE_EXPIRY: float = 30.0
    HTTP2_ENABLED: bool = True

    # Rate limiting per client IP (token bucket)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_BURST: int = 60
    TRUST_PROXY_HEADERS: bool = False

    # Observability
    SLOW_REQUEST_MS: int = 1000

    # Deprecated: only kept so old .env files keep loading
    MUSIC_SOURCE_LINK: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def public_base_url(self) -> str:
        return self.PUBLIC_BASE_URL.rstrip("/")


@lru_cache
def get_settings() -> EnvSettings:
    return EnvSettings()
