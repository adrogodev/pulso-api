from typing import TypeVar, Generic, Protocol, Any

# Input type
T = TypeVar("T")

# Output type
U = TypeVar("U")

class UseCaseArgs(Generic[T]):
    def __init__(self, data: T, context: Any):
        self.data = data
        self.context = context

class UseCaseContract(Protocol, Generic[T, U]):
    async def execute(self, args: UseCaseArgs[T]) -> U:
        ...
