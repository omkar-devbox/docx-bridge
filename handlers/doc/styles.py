"""Legacy Word (.doc) STSH stylesheet handler."""

from typing import Any
from handlers.doc.base import DocBaseHandler
from formats.doc.structures import StshParser


class DocStylesHandler(DocBaseHandler):
    """Handler for Word 97-2003 STSH (Style Sheet) parsing and serialization."""

    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert STSH binary records to JSON styles AST."""
        if isinstance(source, bytes):
            return StshParser.parse(source)
        if isinstance(source, dict):
            return source
        return {"styles": {}}

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize styles AST to STSH binary structures."""
        stsh_bytes, _ = StshParser.build(data)
        return stsh_bytes


__all__ = ["DocStylesHandler"]
