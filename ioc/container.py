from typing import Any, Callable, Dict, Tuple


class Container:
    _registry: Dict[str, Tuple[Callable[[], Any], bool]] = {}
    _singletons: Dict[str, Any] = {}

    @classmethod
    def register(cls, key: str, factory: Callable[[], Any], singleton: bool = False) -> None:
        cls._registry[key] = (factory, singleton)
        cls._singletons.pop(key, None)

    @classmethod
    def register_instance(cls, key: str, instance: Any) -> None:
        cls._registry[key] = (lambda: instance, True)
        cls._singletons[key] = instance

    @classmethod
    def resolve(cls, key: str) -> Any:
        if key not in cls._registry:
            raise Exception(f"Dependency not registered '{key}'")

        factory, singleton = cls._registry[key]
        if not singleton:
            return factory()
        if key not in cls._singletons:
            cls._singletons[key] = factory()
        return cls._singletons[key]

    @classmethod
    def is_registered(cls, key: str) -> bool:
        return key in cls._registry

    @classmethod
    def reset(cls) -> None:
        cls._registry.clear()
        cls._singletons.clear()
