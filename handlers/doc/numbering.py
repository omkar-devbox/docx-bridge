"""Legacy Word (.doc) numbering and bullet list handler."""

from typing import Any
from handlers.doc.base import DocBaseHandler
from formats.doc.structures import ListParser


class DocNumberingHandler(DocBaseHandler):
    """Handler for Word 97-2003 List Format Override (LFO) and List (LST) tables."""

    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert binary LST/LFO tables to JSON numbering AST."""
        if isinstance(source, tuple) and len(source) == 2:
            lst_bytes, lfo_bytes = source
            return ListParser.parse(lst_bytes, lfo_bytes)
        if isinstance(source, dict):
            return source
        return {"abstract_num": [], "num": []}

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize numbering AST to binary LST/LFO tables."""
        lst_bytes, lfo_bytes = ListParser.build(data)
        # Pack with lengths
        return lst_bytes + lfo_bytes


__all__ = ["DocNumberingHandler"]
