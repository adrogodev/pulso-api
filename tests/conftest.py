import threading
import time
from typing import Any, Callable, Dict, List, Optional

import httpx
import pytest

from core.config.settings.env_settings import EnvSettings
from tests.fixtures import ytmusic_data

AUDIO = bytes(i % 251 for i in range(200_000))


class FakeYTMusic:
    """Blocking stand-in for ytmusicapi.YTMusic that records calls."""

    def __init__(self, latency: float = 0.0):
        self.latency = latency
        self.calls: List[tuple] = []
        self.errors: Dict[str, Exception] = {}
        self.lyrics_payload: Optional[dict] = ytmusic_data.lyrics()
        self.watch_payload = ytmusic_data.watch_playlist()
        self._lock = threading.Lock()

    def _call(self, name: str, payload: Callable[[], Any], *args, **kwargs):
        with self._lock:
            self.calls.append((name, args, kwargs))
        if self.latency:
            time.sleep(self.latency)
        if name in self.errors:
            raise self.errors[name]
        return payload()

    def count(self, name: str) -> int:
        return sum(1 for c in self.calls if c[0] == name)

    def search(self, query, filter=None, scope=None, limit=20, ignore_spelling=False):
        return self._call("search", ytmusic_data.search_results, query=query, filter=filter, limit=limit)

    def get_search_suggestions(self, query, detailed_runs=False):
        return self._call("get_search_suggestions", ytmusic_data.suggestions, query)

    def get_album(self, browseId):
        return self._call("get_album", ytmusic_data.album, browseId)

    def get_artist(self, channelId):
        return self._call("get_artist", ytmusic_data.artist, channelId)

    def get_watch_playlist(self, videoId=None, limit=25, **kwargs):
        return self._call("get_watch_playlist", lambda: dict(self.watch_payload), videoId, limit=limit)

    def get_lyrics(self, browseId, timestamps=False):
        return self._call("get_lyrics", lambda: self.lyrics_payload, browseId)


class FakeYdl:
    """Records yt-dlp extractions; every resolution produces a distinct URL (n=<count>)."""

    def __init__(self):
        self.calls = 0
        self.latency = 0.0
        self.error: Optional[Exception] = None
        self.expire_in = 6 * 3600
        self._lock = threading.Lock()

    def factory(self, params: dict):
        fake = self

        class _Ydl:
            def __init__(self):
                self.params = params

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def extract_info(self, url, download=False):
                with fake._lock:
                    fake.calls += 1
                    n = fake.calls
                if fake.latency:
                    time.sleep(fake.latency)
                if fake.error:
                    raise fake.error
                video_id = url.rsplit("=", 1)[-1]
                return {
                    "id": video_id,
                    "url": f"https://rr1.googlevideo.test/videoplayback?id={video_id}&n={n}"
                    f"&expire={int(time.time()) + fake.expire_in}",
                    "format_id": "140",
                    "ext": "m4a",
                    "acodec": "mp4a.40.2",
                    "abr": 129.5,
                    "duration": 369,
                    "filesize": len(AUDIO),
                    "http_headers": {"User-Agent": "test-agent", "Accept-Encoding": "gzip"},
                }

        return _Ydl()


class FakeGoogleVideo:
    """httpx MockTransport handler emulating googlevideo Range semantics."""

    def __init__(self):
        self.requests: List[httpx.Request] = []
        self.forbidden_n: set[str] = set()
        self.always_status: Optional[int] = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.always_status:
            return httpx.Response(self.always_status)
        if request.url.params.get("n") in self.forbidden_n:
            return httpx.Response(403)
        size = len(AUDIO)
        rng = request.headers.get("range")
        if not rng:
            return httpx.Response(200, headers={"Content-Type": "audio/mp4", "Content-Length": str(size)}, stream=httpx.ByteStream(AUDIO))
        start_s, _, end_s = rng.removeprefix("bytes=").partition("-")
        start = int(start_s)
        if start >= size:
            return httpx.Response(416, headers={"Content-Range": f"bytes */{size}"}, stream=httpx.ByteStream(b""))
        end = min(int(end_s) if end_s else size - 1, size - 1)
        body = AUDIO[start : end + 1]
        return httpx.Response(
            206,
            headers={
                "Content-Type": "audio/mp4",
                "Content-Length": str(len(body)),
                "Content-Range": f"bytes {start}-{end}/{size}",
                "Set-Cookie": "upstream=secret",
            },
            stream=httpx.ByteStream(body),
        )


def make_settings(**overrides) -> EnvSettings:
    base = dict(
        PUBLIC_BASE_URL="http://testserver",
        RATE_LIMIT_ENABLED=False,
        CORS_ORIGINS="*",
        STREAM_EXPIRY_MARGIN_SECONDS=300,
        HTTP2_ENABLED=False,
    )
    base.update(overrides)
    return EnvSettings(_env_file=None, **base)


@pytest.fixture
def ytmusic() -> FakeYTMusic:
    return FakeYTMusic()


@pytest.fixture
def ydl() -> FakeYdl:
    return FakeYdl()


@pytest.fixture
def googlevideo() -> FakeGoogleVideo:
    return FakeGoogleVideo()


@pytest.fixture
def settings_overrides() -> dict:
    return {}


@pytest.fixture
async def app(ytmusic, ydl, googlevideo, settings_overrides):
    from app.main import create_app

    upstream_client = httpx.AsyncClient(transport=httpx.MockTransport(googlevideo))
    application = create_app(
        make_settings(**settings_overrides),
        overrides={"ytmusic_client": ytmusic, "ytdlp_factory": ydl.factory, "http_client": upstream_client},
    )
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
