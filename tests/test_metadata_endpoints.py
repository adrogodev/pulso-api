import httpx

from tests.conftest import make_settings

STREAM_BASE = "http://testserver/api/stream/"


async def test_root_health(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "pulso api running..."}


async def test_startup_logs_service_name_and_version(caplog, ytmusic, ydl, googlevideo):
    from app.main import create_app

    upstream = httpx.AsyncClient(transport=httpx.MockTransport(googlevideo))
    application = create_app(
        make_settings(),
        overrides={"ytmusic_client": ytmusic, "ytdlp_factory": ydl.factory, "http_client": upstream},
    )
    with caplog.at_level("INFO", logger="pulso"):
        async with application.router.lifespan_context(application):
            pass
    expected = f"pulso-api {application.version} started"
    assert expected in [r.getMessage() for r in caplog.records if r.name == "pulso"]


async def test_search_returns_all_categories_with_stream_urls(client, ytmusic):
    resp = await client.get("/api/search", params={"query": "  Daft   Punk "})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert [s["id"] for s in data["songs"]] == ["song_vid_01"]
    assert data["songs"][0]["stream_url"] == STREAM_BASE + "song_vid_01"
    assert data["songs"][0]["album"] == {"id": "MPREb_album_1", "title": "Random Access Memories", "artists": [], "songs": []}
    assert [v["stream_url"] for v in data["videos"]] == [STREAM_BASE + "video_vid_1"]
    assert [a["id"] for a in data["albums"]] == ["MPREb_album_1"]
    # top result and artists section refer to the same artist: deduplicated
    assert [a["id"] for a in data["artists"]] == ["UC_artist_1"]
    assert ytmusic.calls[0][2] == {"query": "Daft Punk", "filter": None, "limit": 10}


async def test_search_filter_and_limit_reach_ytmusic(client, ytmusic):
    resp = await client.get("/api/search", params={"query": "x", "filter": "videos", "limit": 5})
    assert resp.status_code == 200
    assert ytmusic.calls[0][2] == {"query": "x", "filter": "videos", "limit": 5}


async def test_search_returns_at_most_limit_items_per_category(client, ytmusic):
    # ytmusicapi treats limit as a minimum and usually returns ~20 items
    song = next(i for i in ytmusic.search_payload if i["resultType"] == "song")
    ytmusic.search_payload = [{**song, "videoId": f"song_vid_{n:02d}"} for n in range(20)]
    resp = await client.get("/api/search", params={"query": "x", "filter": "songs", "limit": 2})
    assert resp.status_code == 200
    assert [s["id"] for s in resp.json()["data"]["songs"]] == ["song_vid_00", "song_vid_01"]


async def test_search_validation_uses_error_envelope(client):
    resp = await client.get("/api/search", params={"query": "x", "filter": "podcasts"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_suggestions(client):
    resp = await client.get("/api/search/suggestions", params={"q": "daft"})
    assert resp.status_code == 200
    assert resp.json()["data"] == {
        "query": "daft",
        "suggestions": ["daft punk", "daft punk get lucky", "daft punk one more time"],
    }


async def test_album_includes_id_track_artists_and_stream_urls(client):
    resp = await client.get("/api/album/MPREb_album_1")
    assert resp.status_code == 200
    album = resp.json()["data"]
    assert album["id"] == "MPREb_album_1"
    assert album["songs_count"] == 2
    track = album["songs"][0]
    assert track["track_number"] == 1
    assert track["artists"][0]["name"] == "Daft Punk"
    assert track["stream_url"] == STREAM_BASE + "track_vid_1"
    # tracks without their own thumbnail inherit the album cover
    assert track["thumbnail"] == album["thumbnail"]


async def test_artist_by_path(client, ytmusic):
    resp = await client.get("/api/artist/UC_artist_1")
    assert resp.status_code == 200
    artist = resp.json()["data"]
    assert artist["id"] == "UC_artist_1"
    assert artist["count_songs"] == 1
    assert artist["songs"][0]["artists"][0]["name"] == "Daft Punk"
    assert artist["songs"][0]["stream_url"] == STREAM_BASE + "song_vid_01"
    assert artist["albums"][0]["id"] == "MPREb_album_1"
    assert ytmusic.calls[0][1] == ("UC_artist_1",)


async def test_artist_legacy_query_redirects(client):
    resp = await client.get("/api/artist", params={"id": "UC_artist_1"})
    assert resp.status_code == 307
    assert resp.headers["location"] == "http://testserver/api/artist/UC_artist_1"
    followed = await client.get("/api/artist", params={"id": "UC_artist_1"}, follow_redirects=True)
    assert followed.json()["data"]["name"] == "Daft Punk"


async def test_songs_is_deprecated_and_returns_own_stream_url(client):
    resp = await client.get("/api/songs", params={"song_id": "song_vid_01"})
    assert resp.status_code == 200
    assert resp.json()["data"] == STREAM_BASE + "song_vid_01"
    assert resp.headers["deprecation"] == "true"
    assert 'rel="successor-version"' in resp.headers["link"]


async def test_songs_rejects_invalid_id(client):
    resp = await client.get("/api/songs", params={"song_id": "../../etc"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_VIDEO_ID"


async def test_watch_playlist(client, ytmusic):
    resp = await client.get("/api/watch/song_vid_01", params={"limit": 2})
    assert len(resp.json()["data"]["tracks"]) == 2
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["playlist_id"] == "RDAMVMsong_vid_01"
    assert [t["stream_url"] for t in data["tracks"]] == [STREAM_BASE + "song_vid_01", STREAM_BASE + "track_vid_1"]
    assert data["tracks"][0]["duration_seconds"] == 369
    assert ytmusic.calls[0][2] == {"limit": 2}


async def test_lyrics(client):
    resp = await client.get("/api/lyrics/song_vid_01")
    assert resp.status_code == 200
    assert resp.json()["data"] == {
        "video_id": "song_vid_01",
        "text": "Like the legend of the phoenix...",
        "source": "Source: LyricFind",
    }


async def test_lyrics_not_available(client, ytmusic):
    ytmusic.watch_payload = {**ytmusic.watch_payload, "lyrics": None}
    resp = await client.get("/api/lyrics/song_vid_01")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "LYRICS_NOT_FOUND"


async def test_metadata_has_cache_control_and_etag(client):
    first = await client.get("/api/album/MPREb_album_1")
    assert first.headers["cache-control"] == "public, max-age=300"
    etag = first.headers["etag"]
    second = await client.get("/api/album/MPREb_album_1", headers={"If-None-Match": etag})
    assert second.status_code == 304
    assert second.content == b""
    assert second.headers["etag"] == etag


async def test_docs_and_openapi_list_new_endpoints(client):
    docs = await client.get("/docs")
    assert docs.status_code == 200
    paths = (await client.get("/openapi.json")).json()["paths"]
    for path in (
        "/api/stream/{video_id}",
        "/api/stream/{video_id}/info",
        "/api/stream/prefetch",
        "/api/watch/{video_id}",
        "/api/lyrics/{video_id}",
        "/api/search/suggestions",
        "/api/artist/{artist_id}",
    ):
        assert path in paths
    assert paths["/api/songs"]["get"]["deprecated"] is True
    assert paths["/api/artist"]["get"]["deprecated"] is True
    assert "206" in paths["/api/stream/{video_id}"]["get"]["responses"]


async def test_watch_limit_caps_tracks(client):
    # ytmusicapi treats limit as a minimum and may return more tracks
    resp = await client.get("/api/watch/song_vid_01", params={"limit": 1})
    assert [t["id"] for t in resp.json()["data"]["tracks"]] == ["song_vid_01"]
