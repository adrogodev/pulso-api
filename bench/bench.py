"""Concurrent HTTP benchmark for Pulso API.

Usage:
    python bench/bench.py --base-url http://127.0.0.1:8000 -n 40 -c 10 [--out results.json]

Scenarios that return 404 on the target (e.g. endpoints that do not exist yet) are skipped.
"""

import argparse
import asyncio
import json
import statistics
import time

import httpx

SCENARIOS = [
    ("search", "GET", "/api/search?query=daft%20punk", None),
    ("album", "GET", "/api/album/MPREb_album_1", None),
    ("artist", "GET", "/api/artist?id=UC_artist_1", None),
    ("artist_path", "GET", "/api/artist/UC_artist_1", None),
    ("suggestions", "GET", "/api/search/suggestions?q=daft", None),
    ("stream_info", "GET", "/api/stream/song_vid_01/info", None),
    ("stream_ttfb", "GET", "/api/stream/song_vid_01", {"Range": "bytes=0-65535"}),
]


def _pct(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(p / 100 * (len(ordered) - 1))))]


async def _one(client: httpx.AsyncClient, method: str, path: str, headers) -> tuple[float, int]:
    start = time.perf_counter()
    async with client.stream(method, path, headers=headers, follow_redirects=True) as resp:
        async for _ in resp.aiter_raw():
            # time to first byte is what matters for audio playback
            if path.startswith("/api/stream/") and not path.endswith("/info"):
                break
        return (time.perf_counter() - start) * 1000, resp.status_code


async def _scenario(client, name, method, path, headers, n, c) -> dict | None:
    first_ms, status = await _one(client, method, path, headers)
    if status == 404:
        return None
    sem = asyncio.Semaphore(c)
    samples: list[float] = []
    errors = 0

    async def task():
        nonlocal errors
        async with sem:
            ms, code = await _one(client, method, path, headers)
            samples.append(ms)
            if code >= 400:
                errors += 1

    wall = time.perf_counter()
    await asyncio.gather(*(task() for _ in range(n)))
    wall = time.perf_counter() - wall
    return {
        "scenario": name,
        "first_ms": round(first_ms, 1),
        "p50_ms": round(statistics.median(samples), 1),
        "p95_ms": round(_pct(samples, 95), 1),
        "p99_ms": round(_pct(samples, 99), 1),
        "rps": round(n / wall, 1),
        "errors": errors,
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("-n", type=int, default=40, help="requests per scenario")
    parser.add_argument("-c", type=int, default=10, help="concurrency")
    parser.add_argument("--out")
    args = parser.parse_args()

    results = []
    async with httpx.AsyncClient(base_url=args.base_url, timeout=120) as client:
        for name, method, path, headers in SCENARIOS:
            row = await _scenario(client, name, method, path, headers, args.n, args.c)
            if row:
                results.append(row)

    header = f"{'scenario':<14}{'first':>9}{'p50':>9}{'p95':>9}{'p99':>9}{'rps':>8}{'err':>5}"
    print(header)
    for r in results:
        print(
            f"{r['scenario']:<14}{r['first_ms']:>9}{r['p50_ms']:>9}{r['p95_ms']:>9}"
            f"{r['p99_ms']:>9}{r['rps']:>8}{r['errors']:>5}"
        )
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
