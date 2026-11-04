# Pulso API

A standalone REST API over YouTube Music. It exposes the catalog (search, albums, artists, radio queues,
lyrics) and plays audio **through the API itself**. Clients (a web frontend, a mobile app, any HTTP
audio player) never talk to YouTube Music or `googlevideo.com`:

```
client ──> Pulso API ──> ytmusicapi (catalog) / yt-dlp (audio URL) ──> YouTube
```

## Features

- **Search** of songs, videos, albums and artists, plus autocomplete suggestions.
- **Catalog**: albums with tracks, artists with top songs and albums, "up next" radio queues, lyrics.
- **Audio streaming proxy** with full HTTP `Range` support (play, seek, resume), AAC by default and Opus
  as fallback. Works with `<audio>`, just_audio / ExoPlayer and AVPlayer.
- **Prefetch** of upcoming tracks so the next song starts instantly.
- Every song, video and track carries a ready-to-play `stream_url`.
- **Performance**: non-blocking calls to ytmusicapi and yt-dlp, read-through cache (memory or Redis) with
  single-flight, `ETag` / `Cache-Control`, gzip for JSON, pooled HTTP/2 client towards googlevideo.
- **Operations**: one JSON envelope for every response, real HTTP status codes, per-IP rate limiting,
  configurable CORS, `Server-Timing` header and slow-request logging.

## Tech stack

Python 3.12+ (3.14 pinned in `.python-version`), FastAPI, Pydantic 2, ytmusicapi, yt-dlp (with Deno),
httpx (HTTP/2), anyio, cachetools, optional Redis, uv for dependency management, pytest for tests.

## Quick start

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs> for the interactive API reference, or try:

```bash
curl "http://localhost:8000/api/search?query=daft%20punk&filter=songs&limit=3"
```

## Project structure

```
app/
  domain/          models, errors and ports (no framework or library code besides Pydantic)
  application/     use cases, DTOs, cache loader, stream resolver and link builder
  infrastructure/  adapters: ytmusicapi, yt-dlp, httpx transport, memory/Redis cache
  api/             routers, controllers, middlewares, exception handlers, OpenAPI examples
  main.py          app factory (create_app) and lifespan
core/              settings, base contracts, response envelope, single-flight
ioc/               dependency injection container
tests/             pytest suite with fakes for YouTube Music, yt-dlp and googlevideo
bench/             benchmark client and simulated upstream server
odd/tasks/         feature log of the streaming and performance work
deploy/            production docker-compose stack and Caddyfile
.github/workflows/ CI: tests, Docker image build and GitHub releases
Dockerfile         production image
```

Each layer has a `config_*.py` that registers its dependencies in the container; `app/main.py` wires them
together in `create_app`.

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

`.env.example` lists every variable, grouped and commented, with the defaults below. Copy it to `.env`
(local) or paste it into the environment of your deployment (for example Dokploy → **Environment**) and change
at least `PUBLIC_BASE_URL` and `CORS_ORIGINS`. `.env` is git-ignored; never commit real values.

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
| `STREAM_BLOCKED_COOLDOWN_SECONDS` | `60` | After a bot check or rate limit, stream requests fail fast with 503 for this long instead of asking YouTube again (0 disables) |
| `YTDLP_MAX_CONCURRENCY` | `4` | Concurrent yt-dlp resolutions |
| `YTDLP_JS_RUNTIME` | `deno` | `deno`, `node`, `bun` or `quickjs` |
| `YTDLP_COOKIES_FILE` | empty | Path inside the container to a Netscape `cookies.txt` of a YouTube account, e.g. `/run/secrets/youtube-cookies.txt` (see [Setting up the cookies](#setting-up-the-cookies)) |
| `YTDLP_PROXY` | empty | Proxy URL for yt-dlp and for the audio proxy, e.g. `http://user:pass@host:port` |
| `YTDLP_EXTRACTOR_ARGS` | empty | yt-dlp `--extractor-args` groups separated by spaces, e.g. `youtube:player_client=tv,web_safari,mweb`. Leave it empty when using cookies |
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
| GET | `/` | Health check: `{"message": "pulso api running..."}` (no envelope) |
| GET | `/docs` | Interactive API reference (Scalar); schema at `/openapi.json` |
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
| 503 | `UPSTREAM_BLOCKED`, `UPSTREAM_RATE_LIMITED` (YouTube bot check / throttling), `COOKIES_UNAVAILABLE`, `STREAM_MISCONFIGURED` (server streaming settings, see the startup logs) |
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

## Mobile clients

- Android emulator: set `PUBLIC_BASE_URL=http://10.0.2.2:8000`. `10.0.2.2` is the emulator's alias for the
  host loopback, so the default bind works. Physical devices need `--host 0.0.0.0` and the PC's LAN IP.
- The API is plain HTTP in development: allow cleartext traffic on Android
  (`android:usesCleartextTraffic` or a `network_security_config`) and an ATS exception on iOS.
- `CORS_ORIGINS` only matters for browsers (including web builds of mobile apps); native apps ignore CORS.
- Restart the server after changing `PUBLIC_BASE_URL`: cached responses keep the old `stream_url`.

## Development

| Task | Command |
|---|---|
| Install dependencies | `uv sync` |
| Add a dependency | `uv add <package>` (updates `pyproject.toml` and `uv.lock`) |
| Upgrade dependencies | `uv lock --upgrade && uv sync` |
| Run the API | `uv run uvicorn app.main:app --reload` |
| Run tests | `uv run pytest` |

`uv.lock` pins the exact version and hash of every dependency; commit it and never edit it by hand.

Logs use the `pulso.*` logger names (`pulso.http`, `pulso.stream`, `pulso.ytdlp`, `pulso.ytmusic`,
`pulso.cache`, `pulso.errors`). Redis keys use the `pulso:` prefix.

## Deployment (Docker image + VPS)

GitHub only builds and publishes the image; the VPS pulls it.

```
git push tag vX.Y.Z ──> GitHub Actions: tests ──> image ghcr.io/adrogodev/pulso-api:X.Y.Z + latest
                                           └──> GitHub release
VPS: docker pull ghcr.io/adrogodev/pulso-api:latest ──> run it
```

The workflow `.github/workflows/release.yml`:

| Job | When | What |
|---|---|---|
| `test` | push, pull request (tags also check the version) | `uv sync --locked` and `uv run pytest` |
| `image` | push to `main` or tag `v*.*.*` | Builds the `Dockerfile` and pushes it to GHCR |
| `release` | tag `v*.*.*` | Creates the GitHub release with generated notes |

Image tags in `ghcr.io/adrogodev/pulso-api` (public, no login needed to pull):

| Tag | Points to | Updated by |
|---|---|---|
| `latest` | The most recent release | every `v*.*.*` tag |
| `X.Y.Z` (e.g. `0.0.1`) | That exact release, never changes | its `vX.Y.Z` tag |
| `X.Y` (e.g. `0.0`) | Newest patch of that minor version | every `vX.Y.*` tag |
| `main` | The latest commit on `main` (not released yet) | every push to `main` |
| `sha-<commit>` | One exact commit | every build |

The image runs a single uvicorn worker with the in-memory cache; Redis is not required. Before scaling to
several workers or containers, set `CACHE_BACKEND=redis` and add a Redis service.

### Publish a release

1. Update `version` in `pyproject.toml` and `app/main.py`, run `uv lock`, commit and push to `main`.
2. Tag and push the tag:

   ```bash
   git tag -a v0.0.2 -m "v0.0.2"
   git push origin v0.0.2
   ```

The workflow runs the tests, pushes `0.0.2`, `0.0` and `latest`, and creates the GitHub release with notes
generated from the commits since the previous tag. The tag must match the `version` in `pyproject.toml`,
otherwise nothing is published.

### Run on the VPS

Install Docker once (Ubuntu/Debian):

```bash
curl -fsSL https://get.docker.com | sh
```

Pull and run the API alone (port 8000):

```bash
docker pull ghcr.io/adrogodev/pulso-api:latest
docker run -d --name pulso-api --restart unless-stopped -p 8000:8000 \
  -e PUBLIC_BASE_URL=http://<VPS_IP>:8000 \
  ghcr.io/adrogodev/pulso-api:latest
```

Pass more settings with `-e NAME=value` or `--env-file .env` (see `.env.example`).

Update to a new release:

```bash
docker pull ghcr.io/adrogodev/pulso-api:latest
docker rm -f pulso-api
# run the same docker run command again
docker image prune -f
```

Use a specific version instead of `latest` (for example `:0.0.1`) to pin it or to roll back.

### Optional: HTTPS with Caddy (docker compose)

`deploy/docker-compose.yml` runs the image behind Caddy, which serves HTTPS with a Let's Encrypt certificate.

```bash
mkdir -p /opt/pulso-api && cd /opt/pulso-api
curl -fsSLO https://raw.githubusercontent.com/adrogodev/pulso-api/main/deploy/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/adrogodev/pulso-api/main/deploy/Caddyfile
```

Create `/opt/pulso-api/.env`:

```dotenv
IMAGE_TAG=latest                        # or a version such as 0.0.1
API_DOMAIN=api.example.com              # or :80 to serve plain HTTP on the server IP
PUBLIC_BASE_URL=https://api.example.com # http://<VPS_IP> without a domain
CORS_ORIGINS=https://app.example.com    # browser frontends allowed to call the API
CACHE_BACKEND=memory
```

With a domain, point a DNS `A` record to the VPS IP first and open ports 80 and 443. Then:

```bash
docker compose pull && docker compose up -d
docker compose ps
docker compose logs -f api
```

To update, change `IMAGE_TAG` if needed and run `docker compose pull && docker compose up -d` again.

## YouTube bot check on servers

From a datacenter IP (any VPS), YouTube often answers yt-dlp with "Sign in to confirm you're not a bot".
The API then returns `503 UPSTREAM_BLOCKED` on `/api/stream/*` while search keeps working. It does not
happen from a residential IP. Options, from simplest:

1. **Cookies of a YouTube account** (`YTDLP_COOKIES_FILE`). Recommended: it is the option that works from a
   VPS. Use a secondary account, because it can be flagged.
2. **A residential proxy** (`YTDLP_PROXY`). The audio proxy uses it too, because googlevideo URLs only work
   from the IP that resolved them. Paid, and every streamed byte goes through it.
3. **Another player client** (`YTDLP_EXTRACTOR_ARGS=youtube:player_client=tv,web_safari,mweb`). Free, but on
   its own it is usually not enough from a datacenter IP.

### Setting up the cookies

**1. Export them** (the file is a credential of the account: never commit it or share it)

1. Install the **Get cookies.txt LOCALLY** extension (Chrome, Brave, Edge or Firefox).
2. Open a **private window**, allow the extension there and sign in to youtube.com with the secondary account.
3. In the same tab open `https://www.youtube.com/robots.txt`.
4. Export with **Export** (current site only), in Netscape format. Do not use "Export All Cookies": that
   file would also carry the sessions of every other site you are signed in to. The file should only have
   `.youtube.com` / `.google.com` lines and starts with `# Netscape HTTP Cookie File`.
5. Close the private window **without signing out**. Signing out invalidates the exported cookies.

**2. Give them to the container** (read-only; every extraction works on a private copy)

- **Dokploy (compose service)**
  1. If the logs ever showed `is a directory`, remove that directory on the VPS first:
     `rmdir /etc/dokploy/compose/<app-name>/files/youtube-cookies.txt`.
  2. **Advanced → Volumes → Add Volume → File Mount**: paste the file in **Content** and set
     **File Path** to `youtube-cookies.txt`. Dokploy stores it in `../files/`.
  3. Mount it in the compose (**General → Compose**):

     ```yaml
     services:
       api:
         volumes:
           - ../files/youtube-cookies.txt:/run/secrets/youtube-cookies.txt:ro
     ```

- **`deploy/docker-compose.yml`**: save the file as `/opt/pulso-api/youtube-cookies.txt` (`chmod 644`) and
  uncomment the `volumes` lines of the `api` service.
- **Plain Docker**:

  ```bash
  docker run ... -v /opt/pulso-api/youtube-cookies.txt:/run/secrets/youtube-cookies.txt:ro \
    -e YTDLP_COOKIES_FILE=/run/secrets/youtube-cookies.txt ghcr.io/adrogodev/pulso-api:latest
  ```

**3. Point the API to them** and redeploy. Leave `YTDLP_EXTRACTOR_ARGS` empty so yt-dlp picks the player
clients that work with an account:

```dotenv
YTDLP_COOKIES_FILE=/run/secrets/youtube-cookies.txt
YTDLP_EXTRACTOR_ARGS=
```

**4. Check it**: the startup log has no `ERROR pulso.ytdlp` line and a stream answers `206`:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "Range: bytes=0-1023" https://<host>/api/stream/dQw4w9WgXcQ
```

The first play of a song takes longer (around 10 to 30 s on a VPS) while yt-dlp resolves it; after that the
URL is cached and responds in about a second. Use `/api/stream/prefetch` to resolve the next songs ahead.

**5. Renew them** when streams answer `503 UPSTREAM_BLOCKED` again (cookies last weeks to months): export
them again, replace the File Mount content (or the file) and redeploy.

If the file cannot be used, the API still starts (search keeps working), logs one `ERROR pulso.ytdlp` line at
startup with the cause, and every stream answers `503 COOKIES_UNAVAILABLE`:

| Startup log | Fix |
|---|---|
| `YTDLP_COOKIES_FILE does not exist` | The volume line is missing in the compose, or the path differs from `YTDLP_COOKIES_FILE` |
| `YTDLP_COOKIES_FILE is a directory, not a file` | The File Mount does not exist under that name, so Docker created a directory: create it as `youtube-cookies.txt` and redeploy |
| `YTDLP_COOKIES_FILE cannot be read (Permission denied)` | The container runs as uid 10001: make the file readable (`chmod 644`) |

## Legal notice

This project extracts audio from YouTube through ytmusicapi and yt-dlp, which goes against the YouTube
Terms of Service. It is intended for personal and educational use; evaluate that risk before publishing or
operating it commercially.
