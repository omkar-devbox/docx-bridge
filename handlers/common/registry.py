"""Base registry pattern for managing and coordinating document component handlers."""

from abc import ABC, abstractmethod
from typing import Any
from handlers.common.base import CommonBaseHandler
from handlers.common.resolver import HandlerResolver
from handlers.common.errors import RegistrationError


class BaseHandlerRegistry(ABC):
    """Abstract registry for coordinating component handlers."""

    def __init__(self):
        self._type_handlers: dict[str, CommonBaseHandler] = {}
        self._tag_handlers: dict[str, CommonBaseHandler] = {}
        self._resolver = HandlerResolver(
            tag_handlers=self._tag_handlers,
            type_handlers=self._type_handlers,
        )

    def register(self, type_name: str, handler: CommonBaseHandler) -> None:
        """Register a handler for a given JSON AST type name."""
        if not isinstance(handler, CommonBaseHandler):
            raise RegistrationError(f"Handler {handler} must inherit from CommonBaseHandler")
        self._type_handlers[type_name] = handler
        self._resolver.register_type(type_name, handler)

    def register_tag(self, tag: str, handler: CommonBaseHandler) -> None:
        """Register a handler for a given native tag."""
        if not isinstance(handler, CommonBaseHandler):
            raise RegistrationError(f"Handler {handler} must inherit from CommonBaseHandler")
        self._tag_handlers[tag] = handler
        self._resolver.register_tag(tag, handler)

    def get_handler_for_type(self, type_name: str) -> CommonBaseHandler | None:
        """Retrieve handler corresponding to a JSON AST type name."""
        return self._type_handlers.get(type_name)

    def get_handler_for_tag(self, tag: str) -> CommonBaseHandler | None:
        """Retrieve handler corresponding to a native tag."""
        return self._tag_handlers.get(tag)

    def get(self, type_name: str) -> CommonBaseHandler | None:
        """Alias for get_handler_for_type."""
        return self.get_handler_for_type(type_name)

    @abstractmethod
    def get_handler_for_native(self, native_key: Any) -> CommonBaseHandler | None:
        """Retrieve handler corresponding to a native tag, opcode, or stream name."""
        pass


__all__ = ["BaseHandlerRegistry"]
