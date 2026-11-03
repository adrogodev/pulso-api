# Rythmx API

A FastAPI backend that exposes the YouTube Music catalog and plays audio **through the API itself**.
The frontend never talks to YouTube Music or `googlevideo.com`:

```
browser ──> Rythmx API ──> ytmusicapi (catalog) / yt-dlp (audio URL) ──> YouTube
```

## Architecture

Clean / hexagonal layers. Dependencies point inward only.

| Layer | Contents |
|---|---|
| `app/domain` | Models (`Song`, `Album`, `Artist`, `Search`, `WatchPlaylist`, `Lyrics`, `StreamSource`), errors, ports (`CachePort`, `AudioStreamProvider`, `AudioTransport`, `I*Service`) |
| `app/application` | Use cases (search, album, artist, watch, lyrics, stream, prefetch), `CachedLoader` (read-through cache + single-flight), `StreamResolver`, `StreamLinkBuilder` |
| `app/infrastructure` | Adapters: ytmusicapi (`YTMusicGateway` thread pool), yt-dlp (`YtDlpStreamAdapter`), httpx (`HttpxAudioTransport`), caches (`MemoryCache`, `RedisCache`) |
| `app/api` | Routers, thin controllers, global exception handlers, middlewares, OpenAPI examples |
| `core`, `ioc` | Settings, base contracts, `ResponseHttp[T]`, single-flight, DI container |

Domain models use Pydantic (as before); no other external library is imported by `app/domain`.

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                 # runtime + dev dependencies
uv sync --extra redis   # optional Redis cache backend
cp .env.example .env
```

`yt-dlp[default,deno]` installs the Deno JavaScript runtime that yt-dlp needs to solve YouTube's
signature challenges; no system-wide install is required.

Behind a corporate proxy that inspects TLS, set `USE_SYSTEM_TRUSTSTORE=true` (and `UV_SYSTEM_CERTS=1` for uv).

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PUBLIC_BASE_URL` | `http://localhost:8000` | Base of every `stream_url` returned by the API |
| `CORS_ORIGINS` | `*` | Comma separated origins. Credentials are enabled only for explicit origins, never with `*` |
| `USE_SYSTEM_TRUSTSTORE` | `false` | Use the OS certificate store |
| `YTMUSIC_LANGUAGE` / `YTMUSIC_LOCATION` | `en` / empty | ytmusicapi locale |
| `YTMUSIC_MAX_CONCURRENCY` | `8` | Threads used for ytmusicapi calls |
| `CACHE_BACKEND` | `memory` | `memory` (per worker) or `redis` (shared) |
| `CACHE_MAX_ITEMS` | `4096` | Memory cache size |
| `REDIS_URL` | `redis://localhost:6379/0` | Used when `CACHE_BACKEND=redis` |
| `CACHE_TTL_SEARCH` / `CACHE_TTL_SUGGESTIONS` | `600` | Seconds |
| `CACHE_TTL_ALBUM` / `CACHE_TTL_ARTIST` | `21600` | Seconds |
| `CACHE_TTL_WATCH` | `600` | Seconds |
| `CACHE_TTL_LYRICS` | `86400` | Seconds |
| `HTTP_CACHE_MAX_AGE` | `300` | `Cache-Control: max-age` of metadata endpoints |
| `STREAM_FORMAT` | `140/251/bestaudio[ext=m4a]/bestaudio` | yt-dlp format selector: AAC (itag 140, plays in Safari) first, Opus (251) as fallback |
| `STREAM_EXPIRY_MARGIN_SECONDS` | `300` | A resolved URL is cached until its `expire` minus this margin |
| `STREAM_FALLBACK_TTL_SECONDS` | `1800` | Lifetime assumed when a URL has no `expire` parameter |
| `STREAM_RETRY_DELAY_SECONDS` | `0.5` | Pause before retrying a 403 on the same URL (googlevideo sometimes rejects the first hit on a fresh URL) |
| `STREAM_CHUNK_SIZE` | `65536` | Proxy chunk size in bytes |
| `STREAM_UPSTREAM_WINDOW_BYTES` | `10485760` | Max bytes per upstream Range request; larger spans are read as consecutive windows (googlevideo throttles bigger ranges) |
| `STREAM_PREFETCH_MAX_IDS` | `50` | Maximum ids per `/api/stream/prefetch` request (400 `TOO_MANY_IDS` above it) |
| `YTDLP_MAX_CONCURRENCY` | `4` | Concurrent yt-dlp resolutions |
| `YTDLP_JS_RUNTIME` | `deno` | `deno`, `node`, `bun` or `quickjs` |
| `HTTP_CONNECT_TIMEOUT` / `HTTP_READ_TIMEOUT` | `5` / `30` | Upstream audio timeouts (seconds) |
| `HTTP_MAX_CONNECTIONS` / `HTTP_MAX_KEEPALIVE` / `HTTP_KEEPALIVE_EXPIRY` | `100` / `20` / `30` | Upstream connection pool |
| `HTTP2_ENABLED` | `true` | HTTP/2 towards googlevideo |
| `RATE_LIMIT_ENABLED` | `true` | Per-IP token bucket on `/api/*` |
| `RATE_LIMIT_PER_MINUTE` / `RATE_LIMIT_BURST` | `120` / `60` | Sustained rate and burst |
| `TRUST_PROXY_HEADERS` | `false` | Use `X-Forwarded-For` for the client IP (only behind a trusted proxy) |
| `SLOW_REQUEST_MS` | `1000` | Requests slower than this (time to headers) are logged |

`MUSIC_SOURCE_LINK` is no longer used and is ignored if present.

## Running

Development:

```bash
uv run uvicorn app.main:app --reload
```

Production (Linux/macOS; `uvloop` is not available on Windows, where uvicorn falls back to asyncio):

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --workers 2 --loop uvloop --http httptools --proxy-headers --no-access-log
```

Workers: the app is I/O bound and already concurrent inside one process (async proxy + thread pools for
the blocking libraries), so start with **1 worker per CPU core, 2–4 in total**. Each worker has its own
memory cache, rate limiter and resolved-URL cache: with more than one worker use `CACHE_BACKEND=redis`
so a song resolved by one worker is reused by the others. More workers also means more parallel
yt-dlp resolutions against YouTube from the same IP.

API reference with examples: <http://localhost:8000/docs> (Scalar).

## Endpoints

All JSON responses use the same envelope:

```json
{ "success": true, "message": "...", "data": { } }
{ "success": false, "message": "...", "error": { "code": "VIDEO_NOT_FOUND" } }
```

| Method | Path | Description |
|---|---|---|
| GET | `/api/search?query=&filter=&limit=` | Songs, videos, albums and artists. `filter`: `songs`, `videos`, `albums`, `artists` |
| GET | `/api/search/suggestions?q=` | Autocomplete suggestions |
| GET | `/api/album/{album_id}` | Album with tracks |
| GET | `/api/artist/{artist_id}` | Artist with top songs and albums |
| GET | `/api/watch/{video_id}?limit=25` | Up-next queue / radio |
| GET | `/api/lyrics/{video_id}` | Lyrics (404 `LYRICS_NOT_FOUND` when unavailable) |
| GET | `/api/stream/{video_id}` | **Audio proxy** with full HTTP Range support (200/206/416) |
| GET | `/api/stream/{video_id}/info` | Format, mime, bitrate, duration, size, `expires_at` |
| POST | `/api/stream/prefetch` | `{"video_ids": [...]}` resolves URLs in the background (202) |
| GET | `/api/artist?id=` | **Deprecated**: 307 redirect to `/api/artist/{artist_id}` |
| GET | `/api/songs?song_id=` | **Deprecated**: returns `/api/stream/{video_id}` of this API |

Every song, video and track in search, album, artist and watch responses has a `stream_url`.

Metadata endpoints send `Cache-Control` and a weak `ETag` (`If-None-Match` returns 304). Every response
has a `Server-Timing` header.

### Playing audio in the frontend

```html
<audio controls preload="none" src="http://localhost:8000/api/stream/dQw4w9WgXcQ"></audio>
```

Seeking works because the proxy forwards `Range` and answers `206` with `Content-Range`. To make the next
song start instantly, prefetch the queue:

```js
await fetch("/api/stream/prefetch", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ video_ids: queue.map((t) => t.id) }),
});
```

### Error codes

| HTTP | Codes |
|---|---|
| 400 | `INVALID_VIDEO_ID`, `TOO_MANY_IDS` |
| 403 | `CONTENT_PRIVATE` |
| 404 | `NOT_FOUND`, `VIDEO_NOT_FOUND`, `AUDIO_FORMAT_UNAVAILABLE`, `LYRICS_NOT_FOUND` |
| 422 | `VALIDATION_ERROR` |
| 429 | `RATE_LIMITED` (with `Retry-After`) |
| 451 | `AGE_RESTRICTED`, `GEO_RESTRICTED` |
| 502 | `UPSTREAM_UNAVAILABLE` |
| 503 | `UPSTREAM_BLOCKED`, `UPSTREAM_RATE_LIMITED` (YouTube bot check / throttling) |
| 504 | `UPSTREAM_TIMEOUT` |

### Migration from 0.1

- `/api/songs?song_id=X` used to return a YouTube Music link. It now returns this API's
  `/api/stream/X` and sends `Deprecation: true`. Use the `stream_url` field instead.
- `/api/artist?id=X` redirects to `/api/artist/X`. Update clients to the path form.
- Errors are no longer `200` with `data: null`: they use real status codes and the error envelope.
- Search results gained `videos` and `albums`; `filter` restricts the category.

## How streaming works

1. `StreamResolver` looks up `stream:{video_id}` in the cache. On a miss, yt-dlp runs in a bounded
   thread pool; concurrent requests for the same id share one resolution (single-flight).
2. The URL is cached until its `expire` query parameter minus `STREAM_EXPIRY_MARGIN_SECONDS`.
3. The proxy opens the URL on a shared pooled `httpx.AsyncClient` (HTTP/2, keep-alive), forwards
   `Range`, and streams 64 KB chunks. Client disconnects close the upstream connection.
4. Upstream is always read with bounded `Range` windows of at most `STREAM_UPSTREAM_WINDOW_BYTES`:
   googlevideo throttles requests without `Range`, or with ranges above ~10 MB, to roughly playback
   speed and then drops them. The windows are stitched into one response, so the client still gets a
   single 200 (no `Range`) or 206 with the `Content-Range` of the span it asked for.
5. A 403 is retried once on the same URL after `STREAM_RETRY_DELAY_SECONDS`, because googlevideo sometimes
   rejects the first hit on a freshly issued URL. If it persists (or on 410), the entry is invalidated,
   the id is resolved again once, and the request is retried the same way. A final refusal returns 503.

## Tests

```bash
uv run pytest
```

ytmusicapi, yt-dlp and googlevideo are replaced by fakes (`tests/conftest.py`). Covered: every endpoint,
Range (200/206/416, Content-Range), cache hit/miss/expiry, single-flight, 403 re-resolution, error mapping,
CORS, rate limiting, gzip exclusion, client disconnect and event-loop responsiveness.

## Benchmark

`bench/sim_server.py` runs the API against a simulated upstream (ytmusicapi blocks 300 ms per call plus
250 ms for the first call of each client instance, as the real client fetches a visitor id; yt-dlp blocks
800 ms; a local server plays googlevideo with Range support). `bench/bench.py` fires concurrent requests.

```bash
uv run python bench/sim_server.py --port 8000      # terminal 1
uv run python bench/bench.py -n 40 -c 10           # terminal 2
```

Results on a Windows laptop, 40 requests per scenario, concurrency 10 (`first` = cold request):

| Scenario | Before p50 | Before rps | After first (cold) | After p50 | After rps |
|---|---|---|---|---|---|
| search | 5525 ms | 1.8 | 773 ms | 44 ms | 192 |
| album | 5519 ms | 1.8 | 306 ms | 38 ms | 202 |
| artist | 5519 ms | 1.8 | 312 ms | 80 ms¹ | 112 |
| stream first byte (cached URL) | n/a | n/a | 11 ms | 57 ms | 126 |

Sequential (concurrency 1) cache hits after the changes: search p50 4 ms, album 3 ms,
stream info 3 ms, first audio byte 7 ms.

¹ `artist` uses the deprecated `?id=` form, which costs a redirect; `/api/artist/{id}` p50 is 39 ms.

### Against real YouTube (local machine, 2026-11-03)

| Measurement | Result |
|---|---|
| First audio byte, URL already resolved (cache hit) | 26–37 ms (first googlevideo connection after start: ~320 ms) |
| Seek (`Range` near the end of a 28 MB file) | 0.2 s |
| Full 28 MB file, `Range: bytes=0-` (windowed) | 3.4 s |
| Cold resolution with yt-dlp (song never played) | 4–11 s, first one ~8 s |
| Search, cold / cache hit | ~0.6–2 s / 3.5 ms |
| 5 different searches in parallel | 1.8 s wall (each ~1.3 s) |

Cold resolution is dominated by yt-dlp talking to YouTube; use `/api/stream/prefetch` for the
queue so the next song is already resolved when it starts.

Before, every request blocked the event loop (requests were served one at a time) and created a new
`YTMusic` client because the DI container did not keep singletons. These numbers measure the API's own
overhead; see the table above for measurements against real YouTube.
