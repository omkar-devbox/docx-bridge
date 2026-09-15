"""Legacy Word (.doc) paragraph and PAPX SPRM handler."""

from typing import Any
from handlers.doc.base import DocBaseHandler
from handlers.doc.run import DocRunHandler
from formats.doc.sprm import decode_paragraph_formatting, encode_paragraph_formatting


class DocParagraphHandler(DocBaseHandler):
    """Handler for Word 97-2003 paragraph formatting and content."""

    def __init__(self, run_handler: DocRunHandler | None = None):
        super().__init__()
        self.run_handler = run_handler or DocRunHandler()

    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert PAPX SPRM dictionary or byte stream to JSON AST paragraph."""
        if isinstance(source, bytes):
            props = decode_paragraph_formatting(source)
            props["type"] = "paragraph"
            props.setdefault("runs", [])
            return props

        if isinstance(source, dict):
            p_data: dict[str, Any] = {
                "type": "paragraph",
                "runs": [],
            }
            # Alignment
            if "sprmPJc" in source:
                p_data["align"] = self.align_to_json(source["sprmPJc"])
            elif "align" in source:
                p_data["align"] = self.align_to_json(source["align"])

            # Spacing
            spacing = {}
            if "sprmPDyaBefore" in source:
                spacing["before"] = source["sprmPDyaBefore"]
            if "sprmPDyaAfter" in source:
                spacing["after"] = source["sprmPDyaAfter"]
            if "sprmPDyaLine" in source:
                spacing["line"] = source["sprmPDyaLine"]
            if not spacing and "spacing" in source and isinstance(source["spacing"], dict):
                spacing = source["spacing"]
            if spacing:
                p_data["spacing"] = spacing

            # Indentation
            indent = {}
            if "sprmPDxaLeft" in source:
                indent["left"] = source["sprmPDxaLeft"]
            if "sprmPDxaRight" in source:
                indent["right"] = source["sprmPDxaRight"]
            if "sprmPDxaLeft1" in source:
                indent["firstLine"] = source["sprmPDxaLeft1"]
            if not indent and "indent" in source:
                if isinstance(source["indent"], dict):
                    indent = source["indent"]
                else:
                    indent = {"left": source["indent"]}
            if indent:
                p_data["indent"] = indent

            # Numbering
            if "sprmPIlfo" in source:
                p_data["numbering"] = {
                    "id": source["sprmPIlfo"],
                    "level": source.get("sprmPIlvl", 0),
                }
            elif "numbering" in source:
                p_data["numbering"] = source["numbering"]

            # Style
            if "sprmPIstd" in source:
                p_data["styleIndex"] = source["sprmPIstd"]
            elif "style" in source:
                p_data["style"] = source["style"]

            # Text / runs
            if "runs" in source and isinstance(source["runs"], list):
                for r in source["runs"]:
                    p_data["runs"].append(self.run_handler.to_json(r))
            elif "text" in source:
                p_data["text"] = source["text"]
                p_data["runs"].append({"type": "run", "text": source["text"]})

            return p_data

        return {
            "type": "paragraph",
            "runs": [{"type": "run", "text": str(source)}],
        }

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize paragraph AST to paragraph SPRMs (PAPX)."""
        style_table = kwargs.get("style_table")
        return encode_paragraph_formatting(data, style_table=style_table)


__all__ = ["DocParagraphHandler"]
