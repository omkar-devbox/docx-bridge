"""Legacy Word (.doc) section descriptor (SED/SEP) handler."""

from typing import Any
from handlers.doc.base import DocBaseHandler
from formats.doc.sprm import decode_section_formatting, encode_section_formatting


class DocSectionsHandler(DocBaseHandler):
    """Handler for Word 97-2003 SED/SEP section formatting and page geometry."""

    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert SED/SEP section descriptors to JSON AST section properties."""
        if isinstance(source, bytes):
            return decode_section_formatting(source)

        if isinstance(source, dict):
            sec: dict[str, Any] = {
                "page": {
                    "margins": {},
                }
            }
            margins = sec["page"]["margins"]
            if "sprmSDyaTop" in source:
                margins["top"] = source["sprmSDyaTop"]
            if "sprmSDyaBottom" in source:
                margins["bottom"] = source["sprmSDyaBottom"]
            if "sprmSDxaLeft" in source:
                margins["left"] = source["sprmSDxaLeft"]
            if "sprmSDxaRight" in source:
                margins["right"] = source["sprmSDxaRight"]

            # Direct page structure if already in AST format
            if "page" in source:
                return source

            return sec

        return {"page": {"margins": {}}}

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize section AST to binary SED/SEP descriptors."""
        return encode_section_formatting(data)


__all__ = ["DocSectionsHandler"]
