"""Resolver for mapping tags, types, and schema keys to component handlers."""

from typing import Any, Callable
from handlers.common.base import CommonBaseHandler
from handlers.common.errors import HandlerNotFoundError


class HandlerResolver:
    """Resolves elements, XML tags, or AST type keys to registered handlers."""

    def __init__(
        self,
        tag_handlers: dict[str, CommonBaseHandler] | None = None,
        type_handlers: dict[str, CommonBaseHandler] | None = None,
        tag_normalizer: Callable[[str], str] | None = None,
        type_normalizer: Callable[[str], str] | None = None,
    ):
        self._tag_handlers: dict[str, CommonBaseHandler] = dict(tag_handlers or {})
        self._type_handlers: dict[str, CommonBaseHandler] = dict(type_handlers or {})
        self._tag_normalizer = tag_normalizer
        self._type_normalizer = type_normalizer

    def register_tag(self, tag: str, handler: CommonBaseHandler) -> None:
        """Register a handler for an XML tag."""
        self._tag_handlers[tag] = handler

    def register_type(self, type_name: str, handler: CommonBaseHandler) -> None:
        """Register a handler for a JSON type name."""
        self._type_handlers[type_name] = handler

    def resolve_tag(self, tag: str) -> CommonBaseHandler | None:
        """Resolve a handler for a given tag string."""
        if tag in self._tag_handlers:
            return self._tag_handlers[tag]

        if self._tag_normalizer:
            normalized = self._tag_normalizer(tag)
            if normalized in self._tag_handlers:
                return self._tag_handlers[normalized]

        return None

    def resolve_type(self, type_name: str) -> CommonBaseHandler | None:
        """Resolve a handler for a given JSON type name."""
        if type_name in self._type_handlers:
            return self._type_handlers[type_name]

        if self._type_normalizer:
            normalized = self._type_normalizer(type_name)
            if normalized in self._type_handlers:
                return self._type_handlers[normalized]

        return None

    def get_tag_handler_or_raise(self, tag: str) -> CommonBaseHandler:
        """Resolve handler for tag or raise HandlerNotFoundError."""
        handler = self.resolve_tag(tag)
        if handler is None:
            raise HandlerNotFoundError(f"No handler registered for XML tag: {tag}")
        return handler

    def get_type_handler_or_raise(self, type_name: str) -> CommonBaseHandler:
        """Resolve handler for type or raise HandlerNotFoundError."""
        handler = self.resolve_type(type_name)
        if handler is None:
            raise HandlerNotFoundError(f"No handler registered for JSON type: {type_name}")
        return handler


__all__ = ["HandlerResolver"]
