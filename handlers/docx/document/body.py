"""Handler for w:body elements in WordprocessingML documents."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class BodyHandler(BaseHandler):
    """Handles parsing and reconstructing w:body elements and dispatching children."""

    def __init__(
        self,
        paragraph_handler: Any = None,
        table_handler: Any = None,
        sections_handler: Any = None,
    ):
        self.paragraph_handler = paragraph_handler
        self.table_handler = table_handler
        self.sections_handler = sections_handler

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> list[dict[str, Any]]:
        """Parse w:body element children into a list of block AST dictionaries."""
        blocks: list[dict[str, Any]] = []

        for child in element:
            tag = local_name(child.tag)

            if tag == "p":
                if self.paragraph_handler:
                    p_data = self.paragraph_handler.to_json(child, simple=simple)
                    if p_data:
                        blocks.append(p_data)
            elif tag == "tbl":
                if self.table_handler:
                    tbl_data = self.table_handler.to_json(child, simple=simple)
                    if tbl_data:
                        blocks.append(tbl_data)
            elif tag == "sectPr":
                if self.sections_handler and not simple:
                    sect_data = self.sections_handler.to_json(child)
                    if sect_data:
                        blocks.append(sect_data)

        return blocks

    def to_xml(
        self,
        blocks: list[dict[str, Any]],
        section_properties: dict[str, Any] | None = None,
    ) -> ET.Element:
        """Construct w:body element from a list of block AST dictionaries."""
        body = ET.Element(qn("w:body"))

        for block in blocks:
            b_type = block.get("type")
            if b_type == "paragraph" and self.paragraph_handler:
                body.append(self.paragraph_handler.to_xml(block))
            elif b_type == "table" and self.table_handler:
                body.append(self.table_handler.to_xml(block))
            elif b_type in ("section", "sectionProperties") and self.sections_handler:
                body.append(self.sections_handler.to_xml(block))

        if section_properties and self.sections_handler:
            body.append(self.sections_handler.to_xml(section_properties))

        return body


__all__ = ["BodyHandler"]
