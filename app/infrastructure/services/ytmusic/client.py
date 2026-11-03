import json
import logging
from functools import partial
from typing import Any

import anyio
import requests
from ytmusicapi.exceptions import YTMusicServerError, YTMusicUserError

from app.domain.errors import (
    DomainError,
    NotFoundError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

logger = logging.getLogger("rythmx.ytmusic")


class TimeoutSession(requests.Session):
    """requests.Session with a default timeout: ytmusicapi sets none, so a stuck call would pin a thread."""

    def __init__(self, timeout: float):
        super().__init__()
        self._timeout = timeout

    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", self._timeout)
        return super().request(*args, **kwargs)


class YTMusicGateway:
    """Runs the synchronous ytmusicapi client in a bounded thread pool and translates its errors."""

    def __init__(self, client: Any, max_concurrency: int):
        self._client = client
        self._limiter = anyio.CapacityLimiter(max_concurrency)

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        fn = partial(getattr(self._client, method), *args, **kwargs)
        try:
            return await anyio.to_thread.run_sync(fn, limiter=self._limiter)
        except DomainError:
            raise
        except requests.Timeout as e:
            raise UpstreamTimeoutError("YouTube Music did not answer in time") from e
        except requests.RequestException as e:
            raise UpstreamUnavailableError("Could not reach YouTube Music") from e
        except (YTMusicServerError, YTMusicUserError) as e:
            if "HTTP 404" in str(e) or "HTTP 400" in str(e):
                raise NotFoundError("Resource not found on YouTube Music") from e
            raise UpstreamUnavailableError("YouTube Music returned an error") from e
        except json.JSONDecodeError as e:
            raise UpstreamUnavailableError("YouTube Music returned an unexpected response") from e
        except (KeyError, IndexError, TypeError) as e:
            # ytmusicapi parsers fail this way on unknown or empty ids
            logger.warning("ytmusicapi %s failed to parse: %r", method, e)
            raise NotFoundError("Resource not found on YouTube Music") from e
