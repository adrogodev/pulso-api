from typing import Any, Generic, TypeVar

from core.contracts.controller_contract import ControllerContract
from core.contracts.usecase_contract import UseCaseArgs, UseCaseContract
from core.models.response_model import ResponseHttp

T = TypeVar("T")


class EnvelopeController(ControllerContract, Generic[T]):
    """Runs a use case and wraps its result in ResponseHttp. Errors propagate to the global handlers."""

    message = "OK"

    def __init__(self, use_case: UseCaseContract[Any, T]):
        self._use_case = use_case

    async def execute(self, data: Any) -> ResponseHttp[T]:
        result = await self._use_case.execute(UseCaseArgs(data=data, context=None))
        return ResponseHttp[T](success=True, message=self.message, data=result)
