"""Legacy Word (.doc) table and TAPX SPRM handler."""

from typing import Any
from handlers.doc.base import DocBaseHandler
from handlers.doc.paragraph import DocParagraphHandler


class DocTableHandler(DocBaseHandler):
    """Handler for Word 97-2003 table structures and cells."""

    def __init__(self, paragraph_handler: DocParagraphHandler | None = None):
        super().__init__()
        self.paragraph_handler = paragraph_handler or DocParagraphHandler()

    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert TAPX table descriptor to JSON AST table."""
        if isinstance(source, dict):
            table_data: dict[str, Any] = {
                "type": "table",
                "properties": {},
                "rows": [],
            }
            if "sprmTJc" in source:
                table_data["properties"]["alignment"] = self.align_to_json(source["sprmTJc"])
            elif "alignment" in source.get("properties", {}):
                table_data["properties"]["alignment"] = source["properties"]["alignment"]

            if "sprmTDxaLeft" in source:
                table_data["properties"]["indent"] = source["sprmTDxaLeft"]
            elif "indent" in source.get("properties", {}):
                table_data["properties"]["indent"] = source["properties"]["indent"]

            for row in source.get("rows", []):
                processed_row = {"cells": []}
                for cell in row.get("cells", []):
                    c_paras = []
                    for cp in cell.get("content", []):
                        c_paras.append(self.paragraph_handler.to_json(cp))
                    processed_row["cells"].append({"content": c_paras})
                table_data["rows"].append(processed_row)

            return table_data

        return {"type": "table", "rows": []}

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize table AST to table SPRMs (TAPX)."""
        # Table rows are serialized with \x07 markers and inTable SPRM in DocWriter
        return b""


__all__ = ["DocTableHandler"]
