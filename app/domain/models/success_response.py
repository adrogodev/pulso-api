from typing import TypeVar, Generic
from pydantic.generics import GenericModel

T = TypeVar("T")

class SuccessResponse(GenericModel, Generic[T]):
    success: bool
    message: str
    data: T