import hashlib
from typing import Mapping, Optional

from fastapi import Request
from fastapi.responses import Response
from pydantic import BaseModel


def _etag_matches(if_none_match: Optional[str], etag: str) -> bool:
    if not if_none_match:
        return False
    tags = {t.strip() for t in if_none_match.split(",")}
    return "*" in tags or etag in tags or etag.removeprefix("W/") in tags


def json_response(
    request: Request,
    model: BaseModel,
    *,
    status_code: int = 200,
    cache_control: Optional[str] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """Single place where JSON is serialized: Pydantic's Rust serializer, always with exclude_none.

    When cache_control is given, a weak ETag is added and If-None-Match is honored with a 304.
    """
    body = model.model_dump_json(exclude_none=True).encode()
    response_headers = dict(headers or {})

    if cache_control and request.method in ("GET", "HEAD"):
        etag = 'W/"' + hashlib.blake2b(body, digest_size=16).hexdigest() + '"'
        response_headers["ETag"] = etag
        response_headers["Cache-Control"] = cache_control
        if _etag_matches(request.headers.get("if-none-match"), etag):
            return Response(status_code=304, headers=response_headers)

    return Response(body, status_code=status_code, media_type="application/json", headers=response_headers)
