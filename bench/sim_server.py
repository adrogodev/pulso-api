"""Run the API against a simulated YouTube upstream for reproducible benchmarks.

ytmusicapi and yt-dlp are replaced by fakes that block the calling thread for a fixed
latency (like the real, synchronous libraries do). A local "googlevideo" server serves
audio bytes with HTTP Range support so the stream proxy can be measured end to end.

Usage:
    python bench/sim_server.py [--port 8000] [--latency-ms 300] [--resolve-ms 800]
"""

import argparse
import os
import sys
import threading
import time
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.fixtures import ytmusic_data  # noqa: E402

UPSTREAM_PORT = 8765
AUDIO_SIZE = 4 * 1024 * 1024
AUDIO = bytes(i % 251 for i in range(AUDIO_SIZE))


def _install_fakes(latency_s: float, visitor_s: float, resolve_s: float) -> None:
    import ytmusicapi

    class FakeYTMusic:
        """Blocking fake. Like the real client, the first call per instance fetches a visitor id."""

        def __init__(self, *args, **kwargs):
            self._warm = False

        def _call(self, payload):
            if not self._warm:
                time.sleep(visitor_s)
                self._warm = True
            time.sleep(latency_s)
            return payload

        def search(self, query, filter=None, scope=None, limit=20, ignore_spelling=False):
            return self._call(ytmusic_data.search_results())

        def get_album(self, browseId):
            return self._call(ytmusic_data.album())

        def get_artist(self, channelId):
            return self._call(ytmusic_data.artist())

        def get_watch_playlist(self, videoId=None, limit=25, **kwargs):
            return self._call(ytmusic_data.watch_playlist())

        def get_lyrics(self, browseId, timestamps=False):
            return self._call(ytmusic_data.lyrics())

        def get_search_suggestions(self, query, detailed_runs=False):
            return self._call(ytmusic_data.suggestions())

    ytmusicapi.YTMusic = FakeYTMusic

    try:
        import yt_dlp
    except ImportError:
        return

    class FakeYoutubeDL:
        def __init__(self, params=None):
            self.params = params or {}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=False, process=True):
            time.sleep(resolve_s)
            video_id = url.rsplit("=", 1)[-1]
            expire = int(time.time()) + 6 * 3600
            return {
                "id": video_id,
                "duration": 369,
                "format_id": "140",
                "ext": "m4a",
                "acodec": "mp4a.40.2",
                "abr": 129.5,
                "filesize": AUDIO_SIZE,
                "url": f"http://127.0.0.1:{UPSTREAM_PORT}/videoplayback?id={video_id}&itag=140&expire={expire}",
                "http_headers": {"User-Agent": "sim"},
            }

    yt_dlp.YoutubeDL = FakeYoutubeDL


def _upstream_app():
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route

    async def playback(request: Request) -> Response:
        rng = request.headers.get("range")
        if not rng:
            return Response(AUDIO, media_type="audio/mp4", headers={"Accept-Ranges": "bytes"})
        start_s, _, end_s = rng.removeprefix("bytes=").partition("-")
        start = int(start_s or 0)
        end = min(int(end_s) if end_s else AUDIO_SIZE - 1, AUDIO_SIZE - 1)
        return Response(
            AUDIO[start : end + 1],
            status_code=206,
            media_type="audio/mp4",
            headers={"Accept-Ranges": "bytes", "Content-Range": f"bytes {start}-{end}/{AUDIO_SIZE}"},
        )

    return Starlette(routes=[Route("/videoplayback", playback)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--latency-ms", type=int, default=300)
    parser.add_argument("--visitor-ms", type=int, default=250)
    parser.add_argument("--resolve-ms", type=int, default=800)
    args = parser.parse_args()

    os.environ.setdefault("MUSIC_SOURCE_LINK", "https://music.youtube.com/watch?v=")
    os.environ.setdefault("PUBLIC_BASE_URL", f"http://127.0.0.1:{args.port}")
    os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
    os.chdir(ROOT)
    _install_fakes(args.latency_ms / 1000, args.visitor_ms / 1000, args.resolve_ms / 1000)

    upstream = uvicorn.Server(uvicorn.Config(_upstream_app(), port=UPSTREAM_PORT, log_level="warning"))
    threading.Thread(target=upstream.run, daemon=True).start()

    from app.main import app

    uvicorn.run(app, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
