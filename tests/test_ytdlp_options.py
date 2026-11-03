"""yt-dlp options that get a datacenter IP past YouTube's bot check: cookies, proxy and extractor args."""

import logging

import pytest

from app.domain.errors import StreamConfigurationError
from app.infrastructure.services.streaming.httpx_audio_transport import build_http_client
from app.infrastructure.services.streaming.ytdlp_stream_adapter import YtDlpStreamAdapter
from tests.conftest import FakeYdl

VIDEO_ID = "dQw4w9WgXcQ"


def make_adapter(ydl: FakeYdl, **kwargs) -> YtDlpStreamAdapter:
    return YtDlpStreamAdapter(
        format_selector="140", max_concurrency=1, fallback_ttl_seconds=60, js_runtime="", ydl_factory=ydl.factory, **kwargs
    )


async def test_defaults_add_no_cookies_proxy_or_extractor_args(ydl):
    await make_adapter(ydl).resolve(VIDEO_ID)
    assert not {"cookiefile", "proxy", "extractor_args"} & set(ydl.last_params)


async def test_each_extraction_reads_cookies_from_its_own_copy(ydl, tmp_path):
    source = tmp_path / "cookies.txt"
    source.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    seen = []

    def factory(params):
        with open(params["cookiefile"], encoding="utf-8") as f:
            seen.append((params["cookiefile"], f.read()))
        return ydl.factory(params)

    adapter = make_adapter(ydl, cookies_file=str(source))
    adapter._ydl_factory = factory
    await adapter.resolve(VIDEO_ID)
    await adapter.resolve(VIDEO_ID)

    # yt-dlp rewrites the cookie file: never the read-only source, never shared between extractions
    (first, content), (second, _) = seen
    assert content == "# Netscape HTTP Cookie File\n"
    assert str(source) not in (first, second) and first != second
    assert source.read_text(encoding="utf-8") == "# Netscape HTTP Cookie File\n"


@pytest.mark.parametrize("kind", ["missing", "directory", "unreadable"])
async def test_unusable_cookies_file_is_a_clear_error(ydl, tmp_path, monkeypatch, caplog, kind):
    path = tmp_path / "youtube-cookies.txt"
    if kind == "directory":
        # what Docker creates when a bind-mounted file does not exist on the host
        path.mkdir()
    elif kind == "unreadable":
        path.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
        real_open = open

        def deny(file, *args, **kwargs):
            if str(file) == str(path):
                raise PermissionError(13, "Permission denied", str(file))
            return real_open(file, *args, **kwargs)

        monkeypatch.setattr("builtins.open", deny)

    adapter = make_adapter(ydl, cookies_file=str(path))
    assert any(r.levelname == "ERROR" and "YTDLP_COOKIES_FILE" in r.getMessage() for r in caplog.records)
    with pytest.raises(StreamConfigurationError) as raised:
        await adapter.resolve(VIDEO_ID)
    assert raised.value.code == "COOKIES_UNAVAILABLE"
    assert ydl.calls == 0


async def test_proxy_is_passed_to_ytdlp(ydl):
    await make_adapter(ydl, proxy="http://user:pass@proxy.test:8080").resolve(VIDEO_ID)
    assert ydl.last_params["proxy"] == "http://user:pass@proxy.test:8080"


async def test_extractor_args_use_the_ytdlp_cli_syntax(ydl):
    args = "youtube:player_client=tv,web_safari youtubepot-bgutilhttp:base_url=http://bgutil:4416"
    await make_adapter(ydl, extractor_args=args).resolve(VIDEO_ID)
    assert ydl.last_params["extractor_args"] == {
        "youtube": {"player_client": ["tv", "web_safari"]},
        "youtubepot-bgutilhttp": {"base_url": ["http://bgutil:4416"]},
    }


async def test_ytdlp_output_stays_at_debug(ydl, caplog):
    await make_adapter(ydl).resolve(VIDEO_ID)
    ytdlp_logger = ydl.last_params["logger"]
    with caplog.at_level(logging.DEBUG):
        ytdlp_logger.error("ERROR: [youtube] abc: Sign in to confirm you're not a bot.")
        ytdlp_logger.warning("WARNING: [youtube] something odd")
    # the adapter already logs one WARNING per failure, so yt-dlp's own lines would duplicate it
    assert [r.levelno for r in caplog.records if r.name == "pulso.ytdlp"] == [logging.DEBUG, logging.DEBUG]


async def test_invalid_extractor_args_are_a_clear_error(ydl, caplog):
    adapter = make_adapter(ydl, extractor_args="no-colon-here")
    assert any(r.levelname == "ERROR" and "YTDLP_EXTRACTOR_ARGS" in r.getMessage() for r in caplog.records)
    with pytest.raises(StreamConfigurationError) as raised:
        await adapter.resolve(VIDEO_ID)
    assert raised.value.code == "STREAM_MISCONFIGURED"


@pytest.mark.parametrize("settings_overrides", [{"YTDLP_COOKIES_FILE": "/run/secrets/does-not-exist.txt"}])
async def test_bad_cookies_answer_503_and_search_keeps_working(client, caplog):
    # the adapter is built at startup, so the configuration problem shows up in the boot logs
    assert any(r.name == "pulso.ytdlp" and r.levelname == "ERROR" for r in caplog.get_records("setup"))
    for path in ("/api/stream/song_vid_01", "/api/stream/song_vid_01/info"):
        resp = await client.get(path)
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "COOKIES_UNAVAILABLE"
    assert (await client.get("/api/search", params={"query": "x"})).status_code == 200


async def test_audio_client_uses_the_same_proxy():
    # googlevideo URLs are bound to the IP that resolved them, so audio must leave through the same proxy
    client = build_http_client(
        http2=False, connect_timeout=1, read_timeout=1, max_connections=1, max_keepalive=1,
        keepalive_expiry=1, proxy="http://proxy.test:8080",
    )
    try:
        assert any(pattern.pattern == "all://" for pattern in client._mounts)
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    "settings_overrides",
    [{"YTDLP_PROXY": "http://proxy.test:8080", "YTDLP_EXTRACTOR_ARGS": "youtube:player_client=tv"}],
)
async def test_settings_reach_the_adapter(client, ydl):
    resp = await client.get(f"/api/stream/{VIDEO_ID}/info")
    assert resp.status_code == 200
    assert ydl.last_params["proxy"] == "http://proxy.test:8080"
    assert ydl.last_params["extractor_args"] == {"youtube": {"player_client": ["tv"]}}
