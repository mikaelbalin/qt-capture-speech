from typing import Dict, Any, TypeVar, Type, Callable, Optional
from .interfaces import (
    CameraServiceInterface,
    SpeechServiceInterface,
    FileManagerInterface,
    ConfigManagerInterface,
)
from .exceptions import AppBaseException

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}

    def register_singleton(
        self, interface: Type[T], implementation: Type[T], *args, **kwargs
    ) -> None:
        """Register a singleton service."""
        key = interface.__name__
        self._factories[key] = lambda: implementation(*args, **kwargs)

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a service instance."""
        key = interface.__name__
        self._singletons[key] = instance

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function."""
        key = interface.__name__
        self._factories[key] = factory

    def get(self, interface: Type[T]) -> T:
        """Get service instance."""
        key = interface.__name__

        # Check if already instantiated singleton
        if key in self._singletons:
            return self._singletons[key]

        # Check if factory exists
        if key in self._factories:
            instance = self._factories[key]()
            self._singletons[key] = instance
            return instance

        raise AppBaseException(f"Service not registered: {key}")

    def has(self, interface: Type[T]) -> bool:
        """Check if service is registered."""
        key = interface.__name__
        return key in self._factories or key in self._singletons

    def clear(self) -> None:
        """Clear all registered services."""
        # Cleanup singletons if they have cleanup methods
        for instance in self._singletons.values():
            if hasattr(instance, "cleanup"):
                try:
                    instance.cleanup()
                except Exception:
                    pass  # Log error in production

        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
