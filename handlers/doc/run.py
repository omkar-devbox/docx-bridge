"""Legacy Word (.doc) character run and CHPX SPRM handler."""

from typing import Any
from handlers.doc.base import DocBaseHandler
from formats.doc.sprm import decode_character_formatting, encode_character_formatting


class DocRunHandler(DocBaseHandler):
    """Handler for Word 97-2003 character formatting and runs."""

    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert CHPX SPRM dictionary or byte stream to JSON AST run."""
        if isinstance(source, bytes):
            props = decode_character_formatting(source)
            props["type"] = "run"
            props.setdefault("text", "")
            return props

        if isinstance(source, dict):
            run_data: dict[str, Any] = {
                "type": "run",
                "text": source.get("text", ""),
            }
            # Handle sprm keys if present
            if "sprmCFBold" in source:
                run_data["bold"] = bool(source["sprmCFBold"])
            elif "bold" in source:
                run_data["bold"] = bool(source["bold"])

            if "sprmCFItalic" in source:
                run_data["italic"] = bool(source["sprmCFItalic"])
            elif "italic" in source:
                run_data["italic"] = bool(source["italic"])

            if "sprmCKul" in source:
                kul = source["sprmCKul"]
                run_data["underline"] = "single" if kul == 1 else ("double" if kul == 3 else "none")
            elif "underline" in source:
                run_data["underline"] = source["underline"]

            if "sprmCHps" in source:
                run_data["size"] = source["sprmCHps"]
            elif "size" in source:
                run_data["size"] = source["size"]

            if "sprmCColor" in source:
                run_data["color"] = self.color_to_hex(source["sprmCColor"])
            elif "color" in source:
                run_data["color"] = source["color"]

            if "sprmCRgFtc0" in source:
                run_data["font"] = str(source["sprmCRgFtc0"])
            elif "font" in source:
                run_data["font"] = str(source["font"])

            return run_data

        return {
            "type": "run",
            "text": str(source) if source else "",
        }

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize run AST to character SPRMs (CHPX)."""
        font_table = kwargs.get("font_table")
        return encode_character_formatting(data, font_table=font_table)


__all__ = ["DocRunHandler"]
