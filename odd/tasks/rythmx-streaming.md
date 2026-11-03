# Rythmx streaming, performance and fixes

Objective: audio streaming proxy through the API, performance work and fixes of known problems.
Branch: `feat/streaming-performance` · Delivery: `ask-on-risk` · Test runner: `uv run pytest`

## Specs

- S1 Streaming: "Usa yt-dlp como librería (no por subprocess) para resolver la URL del stream de audio sin descargar el archivo. Formato preferido: bestaudio, priorizando m4a/AAC (itag 140) [...] con fallback a webm/opus (itag 251). Que el formato preferido sea configurable por .env."
- S2 "Nuevo endpoint GET /api/stream/{video_id}: hace de proxy del audio usando un httpx.AsyncClient compartido y StreamingResponse. Debe soportar HTTP Range de forma completa (reenviar el header Range, responder 206 con Content-Range, Accept-Ranges: bytes, Content-Length y Content-Type correctos) [...] Transmite en chunks (por ejemplo, 64 KB) sin cargar el archivo en memoria y corta la conexión upstream si el cliente se desconecta."
- S3 "Nuevo endpoint GET /api/stream/{video_id}/info: devuelve metadatos del stream (mime, bitrate, duración, tamaño, formato elegido y momento de expiración), envuelto en ResponseHttp."
- S4 "Nuevo endpoint POST /api/stream/prefetch: recibe una lista de video_ids [...] y resuelve sus URLs en segundo plano para calentar la caché."
- S5 "Cachea las URLs resueltas hasta su expiración real (lee el parámetro "expire" de la URL de googlevideo) menos un margen de seguridad configurable. Si upstream responde 403 o 410, invalida la entrada, re-resuelve una sola vez y reintenta."
- S6 yt-dlp in threadpool with semaphore + single-flight dedup.
- S7 "Mapea los errores de yt-dlp (video no disponible, restricción de edad o región, privado) a respuestas HTTP claras y consistentes (404, 451, 502, etc.)."
- S8 Ports/adapters: AudioStreamProvider (domain), GetAudioStream + PrefetchStreams (application), YtDlpStreamAdapter (infrastructure), controller/router (api), registered in container.
- S9 /api/songs replaced or deprecated with migration notes.
- S10 `stream_url` on every song, video and track in search and album, built with PUBLIC_BASE_URL.
- S11 GET /api/watch/{video_id}, GET /api/lyrics/{video_id}, GET /api/search/suggestions?q=...
- S12 Python 3.12+, latest stable deps, uv + pyproject.toml + lockfile.
- S13 ytmusicapi never blocks the event loop; single YTMusic instance.
- S14 CachePort with in-memory (cachetools) default and optional Redis; configurable TTLs (search 10m, suggestions 10m, album/artist 6h, lyrics 24h, streams by expiry).
- S15 ORJSON default response, centralized exclude_none; GZip excluding /api/stream; lifespan for httpx client (pool, keep-alive, HTTP/2, timeouts) and YTMusic.
- S16 Cache-Control + ETag on metadata; Server-Timing middleware + slow log; uvloop/httptools; rate limiting per IP; remove costly duplicate mappings.
- S17 CORS from .env list; credentials never with "*".
- S18 GET /api/artist/{artist_id} (old format deprecated); single ResponseHttp[T] envelope and global exception handlers.
- S19 pytest + pytest-asyncio + httpx ASGITransport tests: every endpoint, Range (206, Content-Range), cache hit/miss/expiry, single-flight, 403 re-resolution, error mapping.
- S20 .env.example, README, benchmark script with before/after numbers.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T0 | S12, S19, S20 | inline | done (baseline bench) | 712d535 |
| T1 | S13, S15, S17, S18 | inline | done, 68 tests green | 9c15602 |
| T2 | S13, S14, S16 | inline | done, 68 tests green | 9c15602 |
| T3 | S1-S10 | inline | done, 68 tests green | 9c15602 |
| T4 | S11 | inline | done, 68 tests green | 9c15602 |
| T5 | S18, S20 | inline | done except .env.example (permission-denied path) | 9c15602, 97a4873 |

Route evidence: one coherent codebase, units depend on each other (F1 -> F2 -> F3), no Writer trigger reason; parent writes inline.

## Log

- L1 (2026-11-03) Original request: full prompt "Contexto del proyecto ... Al terminar, dame un resumen de los cambios, las decisiones que tomaste y cualquier riesgo o limitación pendiente." (Objetivos 1-3 + criterios de aceptación; quoted fragments in Specs).
- L2 (2026-11-03) User approved the phased plan: "Si, continua con la ejecucion del plan".
- L3 (2026-11-03) Environment: corporate FortiGate intercepts TLS (fixed for dev via `truststore`) and blocks YouTube/YouTube Music by policy ("Application Control Violation ... YouTube_Music"). Real upstream checks are impossible from this network; benchmarks use a simulated upstream with fixed latency; real-browser acceptance stays pending for the user.
- L4 (2026-11-03) FastAPI 0.162 deprecates ORJSONResponse; JSON is serialized once in `api/http/responses.py` with Pydantic `model_dump_json(exclude_none=True)` instead (S15 adapted, orjson dropped).
- L5 (2026-11-03) yt-dlp 2026.10.26 needs a JS runtime for YouTube; `yt-dlp[default,deno]` ships Deno inside the venv.
- L6 (2026-11-03) F1-F4 were implemented in one pass because main/container wire every layer; tests ran at the end (68 passed, -W error). Benchmark (simulated upstream, c=10): search p50 5525 ms -> 44 ms, 1.8 -> 192 rps; cached stream first byte 7 ms sequential.
- L7 (2026-11-03) `.env.example` is behind a deny permission rule; the full template was written to the session scratchpad for the user to copy.
- L8 (2026-11-03) Native assess: high (executable_change + item 4). Independent verifier launched; native review pending candidate consent.
- L9 (2026-11-03) Verifier: all specs pass except S20 (.env.example, known permission block). Blocker fixed: `ensure_video_id` accepted a trailing newline (re.match + `$`), leaking LF into the /api/songs Link header; now fullmatch + regression tests. Advisory fixed: STREAM_PREFETCH_MAX_IDS was ignored; now enforced (400 TOO_MANY_IDS). 73 tests green.
