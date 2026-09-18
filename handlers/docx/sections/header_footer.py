"""Handler for WordprocessingML header (w:hdr) and footer (w:ftr) parts."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name
from handlers.docx.text import ParagraphHandler
from handlers.docx.tables import TableHandler


class HeaderFooterHandler(BaseHandler):
    """Handles w:hdr and w:ftr conversion to/from structured JSON AST."""

    def __init__(
        self,
        paragraph_handler: ParagraphHandler | None = None,
        table_handler: TableHandler | None = None,
    ):
        self.paragraph_handler = paragraph_handler or ParagraphHandler()
        self.table_handler = table_handler or TableHandler(self.paragraph_handler)

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> dict[str, Any]:
        """Convert a w:hdr or w:ftr root XML element to JSON dictionary."""
        tag = local_name(element.tag)
        is_footer = tag == "ftr" or "footer" in tag.lower()

        content: list[dict[str, Any]] = []

        for child in element:
            if child.tag == qn("w:p"):
                content.append(
                    self.paragraph_handler.to_json(child, simple=simple)
                )
            elif child.tag == qn("w:tbl"):
                content.append(
                    self.table_handler.to_json(child, simple=simple)
                )

        if simple:
            return {
                "type": "footer" if is_footer else "header",
                "content": content,
            }

        return {
            "type": self.tag_to_name(element.tag, "footer" if is_footer else "header"),
            "content": content,
        }

    def to_xml(
        self,
        data: dict[str, Any] | list[Any],
        is_footer: bool = False,
    ) -> ET.Element:
        """Convert structured header/footer JSON data into a w:hdr or w:ftr XML element."""
        if isinstance(data, dict):
            node_type = str(data.get("type", "")).lower()
            if "footer" in node_type or "ftr" in node_type:
                is_footer = True
            content_items = data.get("content", data.get("children", []))
        elif isinstance(data, list):
            content_items = data
        else:
            content_items = []

        root_tag = qn("w:ftr") if is_footer else qn("w:hdr")
        root = ET.Element(root_tag)

        for item in content_items:
            if isinstance(item, str):
                root.append(self.paragraph_handler.to_xml({"text": item}))
            elif isinstance(item, dict):
                item_type = item.get("type", "")
                if item_type in ("table", "tbl", "w:tbl") or "rows" in item:
                    root.append(self.table_handler.to_xml(item))
                else:
                    root.append(self.paragraph_handler.to_xml(item))

        # Ensure at least one empty paragraph if content is empty (strict OpenXML conformance)
        if len(root) == 0:
            root.append(ET.Element(qn("w:p")))

        return root


__all__ = ["HeaderFooterHandler"]
