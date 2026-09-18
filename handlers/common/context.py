"""Conversion and parsing context for document component handlers."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HandlerContext:
    """Carries execution state, options, and shared resources across handlers."""

    simple: bool = False
    relationships: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the extra parameters or options."""
        if key in self.options:
            return self.options[key]
        return self.extra.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context's extra store."""
        self.extra[key] = value

    def child_context(self, **kwargs) -> "HandlerContext":
        """Create a child context inheriting parent values with overrides."""
        merged_options = {**self.options, **kwargs.get("options", {})}
        merged_extra = {**self.extra, **kwargs.get("extra", {})}
        return HandlerContext(
            simple=kwargs.get("simple", self.simple),
            relationships=kwargs.get("relationships", self.relationships),
            metadata=kwargs.get("metadata", self.metadata),
            options=merged_options,
            extra=merged_extra,
        )


__all__ = ["HandlerContext"]
