from typing import Dict, Any, Callable

class Container:
    _registry: Dict[str, Callable[[], Any]] = {}
    _singletons: Dict[str, Any] = {}

    @classmethod
    def register(cls,key:str,factory: Callable[[], Any], singleton: bool = False) -> None:
        cls._registry[key] = (factory, singleton)

    @classmethod
    def resolve(cls,key:str) -> Any:
        if key not in cls._registry:
            raise Exception(f"Dependency not registered '{key}'")
        
        factory, singleton = cls._registry[key]
        if singleton :
            if key  not in cls._singletons:
                cls._singletons[key] = factory()
                return cls._singletons[key]
            else:
                return factory()