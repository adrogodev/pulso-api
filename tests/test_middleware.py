import pytest


@pytest.mark.parametrize("settings_overrides", [{"RATE_LIMIT_ENABLED": True, "RATE_LIMIT_PER_MINUTE": 60, "RATE_LIMIT_BURST": 3}])
async def test_rate_limit_per_ip(client):
    codes = [(await client.get("/api/search", params={"query": "x"})).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    limited = await client.get("/api/search", params={"query": "x"})
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    assert int(limited.headers["retry-after"]) >= 1
    # non-API routes are not limited
    assert (await client.get("/")).status_code == 200


@pytest.mark.parametrize("settings_overrides", [{"CORS_ORIGINS": "http://localhost:5173, https://pulso.app"}])
async def test_cors_explicit_origins_allow_credentials(client):
    resp = await client.get("/", headers={"Origin": "http://localhost:5173"})
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert resp.headers["access-control-allow-credentials"] == "true"
    other = await client.get("/", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers


async def test_cors_wildcard_never_sends_credentials(client):
    resp = await client.get("/", headers={"Origin": "https://anything.example"})
    assert resp.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in resp.headers


async def test_cors_exposes_range_headers_for_audio(client):
    resp = await client.get(
        "/api/stream/song_vid_01", headers={"Origin": "https://x.example", "Range": "bytes=0-1"}
    )
    exposed = resp.headers["access-control-expose-headers"].lower()
    assert "content-range" in exposed and "accept-ranges" in exposed


async def test_server_timing_header(client):
    resp = await client.get("/api/album/MPREb_album_1")
    assert resp.headers["server-timing"].startswith("app;dur=")


async def test_json_is_gzipped(client):
    resp = await client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert resp.headers["content-encoding"] == "gzip"


@pytest.mark.parametrize("settings_overrides", [{"SLOW_REQUEST_MS": 0}])
async def test_slow_requests_are_logged(client, caplog):
    with caplog.at_level("WARNING", logger="pulso.http"):
        await client.get("/")
    assert any("slow request GET /" in r.message for r in caplog.records)
