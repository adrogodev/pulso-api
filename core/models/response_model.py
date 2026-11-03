from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseHttp(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None


class ErrorDetail(BaseModel):
    code: str
    detail: object | None = None


class ResponseErrorHttp(BaseModel):
    success: bool = False
    message: str
    error: ErrorDetail
