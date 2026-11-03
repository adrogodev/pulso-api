"""Pure ASGI middlewares (no BaseHTTPMiddleware) so audio streaming and disconnects pass through untouched."""

import logging
import math
import time
from typing import Iterable, Tuple

from cachetools import TTLCache
from starlette.datastructures import MutableHeaders
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.http.errors import error_response

logger = logging.getLogger("rythmx.http")


class TimingMiddleware:
    """Adds `Server-Timing: app;dur=<ms>` (time until headers are sent) and logs slow requests."""

    def __init__(self, app: ASGIApp, slow_request_ms: int):
        self.app = app
        self.slow_request_ms = slow_request_ms

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()

        async def send_with_timing(message: Message) -> None:
            if message["type"] == "http.response.start":
                duration = (time.perf_counter() - started) * 1000
                MutableHeaders(scope=message).append("Server-Timing", f"app;dur={duration:.1f}")
                if duration >= self.slow_request_ms:
                    logger.warning(
                        "slow request %s %s -> %s in %.0f ms",
                        scope["method"], scope["path"], message["status"], duration,
                    )
            await send(message)

        await self.app(scope, receive, send_with_timing)


class SelectiveGZipMiddleware:
    """GZip for JSON responses, skipping paths (audio) where compression only costs CPU and breaks ranges."""

    def __init__(self, app: ASGIApp, exclude_prefixes: Iterable[str], minimum_size: int = 500):
        self.app = app
        self.gzip = GZipMiddleware(app, minimum_size=minimum_size)
        self.exclude_prefixes = tuple(exclude_prefixes)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"].startswith(self.exclude_prefixes):
            await self.app(scope, receive, send)
        else:
            await self.gzip(scope, receive, send)


def client_ip(scope: Scope, trust_proxy_headers: bool) -> str:
    if trust_proxy_headers:
        for name, value in scope.get("headers", []):
            if name == b"x-forwarded-for":
                return value.decode("latin-1").split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    """Per-IP token bucket on /api routes, so a single client cannot get this server's IP blocked by YouTube.

    State is per process: with several workers the effective limit is multiplied by the worker count.
    """

    def __init__(
        self,
        app: ASGIApp,
        per_minute: int,
        burst: int,
        trust_proxy_headers: bool = False,
        prefix: str = "/api/",
        max_clients: int = 10000,
    ):
        self.app = app
        self.rate = per_minute / 60.0
        self.per_minute = per_minute
        self.burst = burst
        self.trust_proxy_headers = trust_proxy_headers
        self.prefix = prefix
        self._buckets: TTLCache[str, Tuple[float, float]] = TTLCache(maxsize=max_clients, ttl=3600)

    def _take(self, key: str) -> float:
        """Consumes one token; returns 0 when allowed, otherwise seconds until the next token."""
        now = time.monotonic()
        tokens, last = self._buckets.get(key, (float(self.burst), now))
        tokens = min(float(self.burst), tokens + (now - last) * self.rate)
        if tokens < 1:
            self._buckets[key] = (tokens, now)
            return (1 - tokens) / self.rate
        self._buckets[key] = (tokens - 1, now)
        return 0.0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] == "OPTIONS" or not scope["path"].startswith(self.prefix):
            await self.app(scope, receive, send)
            return
        wait = self._take(client_ip(scope, self.trust_proxy_headers))
        if wait > 0:
            response = error_response(
                429,
                "Too many requests",
                "RATE_LIMITED",
                headers={"Retry-After": str(math.ceil(wait)), "X-RateLimit-Limit": str(self.per_minute)},
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
