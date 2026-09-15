"""Base registry pattern for managing and coordinating document component handlers."""

from abc import ABC, abstractmethod
from typing import Any
from handlers.common.base import CommonBaseHandler


class BaseHandlerRegistry(ABC):
    """Abstract registry for coordinating component handlers."""

    def __init__(self):
        self._type_handlers: dict[str, CommonBaseHandler] = {}

    def register(self, type_name: str, handler: CommonBaseHandler) -> None:
        """Register a handler for a given JSON AST type name."""
        self._type_handlers[type_name] = handler

    def get_handler_for_type(self, type_name: str) -> CommonBaseHandler | None:
        """Retrieve handler corresponding to a JSON AST type name."""
        return self._type_handlers.get(type_name)

    def get(self, type_name: str) -> CommonBaseHandler | None:
        """Alias for get_handler_for_type."""
        return self.get_handler_for_type(type_name)

    @abstractmethod
    def get_handler_for_native(self, native_key: Any) -> CommonBaseHandler | None:
        """Retrieve handler corresponding to a native tag, opcode, or stream name."""
        pass


__all__ = ["BaseHandlerRegistry"]
