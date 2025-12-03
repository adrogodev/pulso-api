from typing import Protocol, Any

class ControllerContract(Protocol):
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        ...