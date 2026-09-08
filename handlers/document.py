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

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert w:document element to JSON dictionary."""
        content: list[dict[str, Any]] = []
        body = element.find(qn("w:body"))

        if body is not None:
            for child in body:
                if child.tag == qn("w:p"):
                    content.append(self.paragraph_handler.to_json(child))
                elif child.tag == qn("w:tbl"):
                    content.append(self.table_handler.to_json(child))
                elif child.tag == qn("w:sectPr"):
                    content.append(self.sections_handler.to_json(child))

        return {
            "type": "document",
            "body": {
                "content": content,
            },
        }

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert JSON document representation to w:document XML element."""
        doc = ET.Element(qn("w:document"))
        body = ET.SubElement(doc, qn("w:body"))

        body_data = data.get("body", {})
        content_items = body_data.get("content", [])

        has_sect_pr = False
        for item in content_items:
            item_type = item.get("type")
            if item_type in ("paragraph", "w:p", self.tag_to_name("w:p")):
                body.append(self.paragraph_handler.to_xml(item))
            elif item_type in ("table", "w:tbl", self.tag_to_name("w:tbl")):
                body.append(self.table_handler.to_xml(item))
            elif item_type in ("section", "section_properties", "sectionProperties", self.tag_to_name("w:sectPr")):
                body.append(self.sections_handler.to_xml(item))
                has_sect_pr = True

        # If document has separate sectionProperties outside content list
        if not has_sect_pr and "sectionProperties" in body_data:
            body.append(self.sections_handler.to_xml(body_data["sectionProperties"]))

        return doc
