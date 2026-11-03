import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import (
    ContentRestrictedError,
    DomainError,
    InvalidInputError,
    NotFoundError,
    PrivateContentError,
    UpstreamBlockedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from core.models.response_model import ErrorDetail, ResponseErrorHttp

logger = logging.getLogger("rythmx.errors")

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    InvalidInputError: 400,
    PrivateContentError: 403,
    NotFoundError: 404,
    ContentRestrictedError: 451,
    UpstreamUnavailableError: 502,
    UpstreamBlockedError: 503,
    UpstreamTimeoutError: 504,
}


def status_for(error: DomainError) -> int:
    for error_type in type(error).__mro__:
        if error_type in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[error_type]
    return 500


def error_response(status_code: int, message: str, code: str, detail: object = None, headers=None) -> Response:
    body = ResponseErrorHttp(message=message, error=ErrorDetail(code=code, detail=detail))
    return Response(
        body.model_dump_json(exclude_none=True),
        status_code=status_code,
        media_type="application/json",
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> Response:
        status = status_for(exc)
        if status >= 500:
            logger.warning("%s: %s", exc.code, exc.message)
        return error_response(status, exc.message, exc.code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> Response:
        errors = [{k: v for k, v in e.items() if k in ("loc", "msg", "type")} for e in exc.errors()]
        return error_response(422, "Invalid request", "VALIDATION_ERROR", jsonable_encoder(errors))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> Response:
        return error_response(exc.status_code, str(exc.detail), f"HTTP_{exc.status_code}", headers=exc.headers)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> Response:
        logger.exception("unhandled error", exc_info=exc)
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
