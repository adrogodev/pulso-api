from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")

class ResponseHttp(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None


class ResponseErrorHttp(BaseModel, Generic[T]):
    success: bool
    message: str
    error: T | None    
    