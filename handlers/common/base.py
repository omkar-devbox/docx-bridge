"""Common abstract base handler interface for document conversions."""

from abc import ABC, abstractmethod
from typing import Any


class CommonBaseHandler(ABC):
    """Abstract base handler for converting document components to/from JSON AST."""

    @abstractmethod
    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert a native document element, stream, or record to JSON AST."""
        pass

    @abstractmethod
    def to_format(self, data: dict[str, Any], **kwargs) -> Any:
        """Reconstruct a native document element, stream, or record from JSON AST."""
        pass


__all__ = ["CommonBaseHandler"]
