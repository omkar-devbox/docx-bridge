"""Handler for w:document (main document part)."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn
from handlers.paragraph import ParagraphHandler
from handlers.table import TableHandler
from handlers.sections import SectionsHandler


class DocumentHandler(BaseHandler):
    """Handles w:document and w:body conversion to/from JSON."""

    def __init__(
        self,
        paragraph_handler: ParagraphHandler | None = None,
        table_handler: TableHandler | None = None,
        sections_handler: SectionsHandler | None = None,
    ):
        self.paragraph_handler = paragraph_handler or ParagraphHandler()
        self.table_handler = table_handler or TableHandler(self.paragraph_handler)
        self.sections_handler = sections_handler or SectionsHandler()

    def to_json(self, element: ET.Element, simple: bool = False) -> dict[str, Any]:
        """Convert w:document element to JSON dictionary."""
        content: list[dict[str, Any]] = []
        body = element.find(qn("w:body"))

        if body is not None:
            for child in body:
                if child.tag == qn("w:p"):
                    content.append(self.paragraph_handler.to_json(child, simple=simple))
                elif child.tag == qn("w:tbl"):
                    content.append(self.table_handler.to_json(child, simple=simple))
                elif child.tag == qn("w:sectPr"):
                    content.append(self.sections_handler.to_json(child))

        if simple:
            return {
                "body": content,
            }
        else:
            return {
                "type": "document",
                "body": {
                    "content": content,
                },
            }

    def to_xml(self, data: dict[str, Any] | list[Any]) -> ET.Element:
        """Convert JSON document representation to w:document XML element."""
        doc = ET.Element(qn("w:document"))
        body = ET.SubElement(doc, qn("w:body"))

        # Support flexible data input (direct list, body as list, or body.content as list)
        if isinstance(data, list):
            content_items = data
            body_data: dict[str, Any] = {}
        elif isinstance(data, dict):
            raw_body = data.get("body")
            if isinstance(raw_body, list):
                content_items = raw_body
                body_data = data
            elif isinstance(raw_body, dict):
                body_data = raw_body
                content_items = body_data.get("content", [])
            elif "content" in data and isinstance(data["content"], list):
                content_items = data["content"]
                body_data = data
            else:
                content_items = []
                body_data = {}
        else:
            content_items = []
            body_data = {}

        has_sect_pr = False
        for item in content_items:
            if isinstance(item, str):
                body.append(self.paragraph_handler.to_xml({"text": item}))
                continue
            if not isinstance(item, dict):
                continue

            item_type = item.get("type", "paragraph")
            if item_type in ("heading", "h1", "h2", "h3", "h4", "h5", "h6"):
                p_item = dict(item)
                p_item["type"] = "paragraph"
                if "heading" not in p_item and "style" not in p_item:
                    lvl = item.get("level") or (int(item_type[1]) if item_type.startswith("h") and len(item_type) == 2 and item_type[1].isdigit() else 1)
                    p_item["style"] = f"Heading{lvl}"
                body.append(self.paragraph_handler.to_xml(p_item))
            elif item_type in ("pageBreak", "page_break"):
                p = ET.Element(qn("w:p"))
                r = ET.SubElement(p, qn("w:r"))
                ET.SubElement(r, qn("w:br"), {qn("w:type"): "page"})
                body.append(p)
            elif item_type in ("paragraph", "w:p", self.tag_to_name("w:p"), "p", "bullet", "list_item", "listItem", "list"):
                body.append(self.paragraph_handler.to_xml(item))
            elif item_type in ("table", "w:tbl", self.tag_to_name("w:tbl"), "tbl"):
                body.append(self.table_handler.to_xml(item))
            elif item_type in ("section", "section_properties", "sectionProperties", self.tag_to_name("w:sectPr")):
                body.append(self.sections_handler.to_xml(item))
                has_sect_pr = True
            elif "rows" in item:
                body.append(self.table_handler.to_xml(item))
            elif "text" in item or "runs" in item:
                body.append(self.paragraph_handler.to_xml(item))

        # If document has separate sectionProperties outside content list
        if not has_sect_pr and "sectionProperties" in body_data:
            body.append(self.sections_handler.to_xml(body_data["sectionProperties"]))

        return doc
