import logging
from contextlib import asynccontextmanager
from typing import Any, Mapping, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

import app.domain.models.ytmusic  # noqa: F401  resolves forward references between domain models
from app.api.config.config_api import config_api
from app.api.http.errors import register_exception_handlers
from app.api.http.middleware import RateLimitMiddleware, SelectiveGZipMiddleware, TimingMiddleware
from app.api.routes.api_router import api_router
from app.application.config.config_application import config_application
from app.infrastructure.config.config_infrastructure import config_infrastructure
from core.config.settings.env_settings import EnvSettings, get_settings
from ioc.container import Container

logger = logging.getLogger("rythmx")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Shared clients are created once per process and closed on shutdown
    Container.resolve('ytmusic_client')
    http_client = Container.resolve('http_client')
    try:
        yield
    finally:
        await Container.resolve('prefetch_streams_usecase').wait_idle()
        await http_client.aclose()
        await Container.resolve('cache').close()


def create_app(settings: Optional[EnvSettings] = None, overrides: Optional[Mapping[str, Any]] = None) -> FastAPI:
    """Builds the app. `overrides` replaces container entries (used by tests and the benchmark)."""
    settings = settings or get_settings()
    if settings.USE_SYSTEM_TRUSTSTORE:
        import truststore

        truststore.inject_into_ssl()

    Container.reset()
    config_infrastructure(settings)
    config_application(settings)
    config_api()
    for key, instance in (overrides or {}).items():
        Container.register_instance(key, instance)

    app = FastAPI(
        title="Rythmx API",
        version="0.2.0",
        description="YouTube Music catalog and audio streaming. The frontend only talks to this API.",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.metadata_cache_control = f"public, max-age={settings.HTTP_CACHE_MAX_AGE}"

    @app.get("/docs", include_in_schema=False)
    async def scalar_html():
        return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)

    @app.get("/", tags=["Health"])
    async def root():
        return {"message": "rythmx api running..."}

    register_exception_handlers(app)
    app.include_router(api_router)

    # Added innermost first: GZip -> RateLimit -> CORS -> Timing (outermost)
    app.add_middleware(SelectiveGZipMiddleware, exclude_prefixes=["/api/stream"])
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(
            RateLimitMiddleware,
            per_minute=settings.RATE_LIMIT_PER_MINUTE,
            burst=settings.RATE_LIMIT_BURST,
            trust_proxy_headers=settings.TRUST_PROXY_HEADERS,
        )
    origins = settings.cors_origins
    wildcard = "*" in origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if wildcard else origins,
        # Browsers reject credentials with "*", so they are only enabled for explicit origins
        allow_credentials=not wildcard,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "Content-Length", "Accept-Ranges", "ETag", "Server-Timing", "Retry-After"],
    )
    app.add_middleware(TimingMiddleware, slow_request_ms=settings.SLOW_REQUEST_MS)
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# httpx logs every proxied audio request at INFO
logging.getLogger("httpx").setLevel(logging.WARNING)
app = create_app()
