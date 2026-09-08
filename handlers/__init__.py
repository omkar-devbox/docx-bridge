"""Handlers for individual DOCX OpenXML components and parts."""

from typing import Any
from handlers.base import BaseHandler, qn, de_qn, NAMESPACES
from config import (
    XML_TO_JSON_TAGS,
    JSON_TO_XML_TAGS,
    tag_to_name,
    name_to_tag,
    get_tags_for_category,
)
from handlers.document import DocumentHandler
from handlers.paragraph import ParagraphHandler
from handlers.run import RunHandler
from handlers.table import TableHandler
from handlers.styles import StylesHandler
from handlers.numbering import NumberingHandler
from handlers.sections import SectionsHandler
from handlers.media import MediaHandler
from handlers.relationships import RelationshipsHandler


class HandlerRegistry:
    """Registry coordinating handlers for element parsing and reconstruction."""

    def __init__(self):
        self.run_handler = RunHandler()
        self.paragraph_handler = ParagraphHandler(run_handler=self.run_handler)
        self.table_handler = TableHandler(paragraph_handler=self.paragraph_handler)
        self.sections_handler = SectionsHandler()
        self.document_handler = DocumentHandler(
            paragraph_handler=self.paragraph_handler,
            table_handler=self.table_handler,
            sections_handler=self.sections_handler,
        )
        self.styles_handler = StylesHandler()
        self.numbering_handler = NumberingHandler()
        self.media_handler = MediaHandler()
        self.relationships_handler = RelationshipsHandler()

        # Tag to handler mapping (qualified Clark tags)
        self._tag_handlers: dict[str, BaseHandler] = {
            qn("w:document"): self.document_handler,
            qn("w:p"): self.paragraph_handler,
            qn("w:r"): self.run_handler,
            qn("w:tbl"): self.table_handler,
            qn("w:sectPr"): self.sections_handler,
            qn("w:styles"): self.styles_handler,
            qn("w:numbering"): self.numbering_handler,
            qn("w:drawing"): self.media_handler,
        }

        # JSON type name to handler mapping (derived from master-tags.json)
        self._type_handlers: dict[str, BaseHandler] = {
            "document": self.document_handler,
            "paragraph": self.paragraph_handler,
            "run": self.run_handler,
            "table": self.table_handler,
            "section": self.sections_handler,
            "sectionProperties": self.sections_handler,
            "section_properties": self.sections_handler,
            "styles": self.styles_handler,
            "numbering": self.numbering_handler,
            "drawing": self.media_handler,
        }

    def get_handler_for_tag(self, tag: str) -> BaseHandler | None:
        """Find handler corresponding to an XML tag (Clark '{uri}p' or prefixed 'w:p')."""
        if tag in self._tag_handlers:
            return self._tag_handlers[tag]
        # Try resolving via Clark notation
        qualified = qn(tag)
        if qualified in self._tag_handlers:
            return self._tag_handlers[qualified]
        # Try resolving via master-tags.json readable name
        name = tag_to_name(tag)
        return self._type_handlers.get(name)

    def get_handler_for_type(self, type_name: str) -> BaseHandler | None:
        """Find handler corresponding to a JSON type name."""
        if type_name in self._type_handlers:
            return self._type_handlers[type_name]
        # Try resolving via master-tags XML tag
        tag = name_to_tag(type_name)
        return self.get_handler_for_tag(tag)


__all__ = [
    "BaseHandler",
    "DocumentHandler",
    "ParagraphHandler",
    "RunHandler",
    "TableHandler",
    "StylesHandler",
    "NumberingHandler",
    "SectionsHandler",
    "MediaHandler",
    "RelationshipsHandler",
    "HandlerRegistry",
    "qn",
    "de_qn",
    "NAMESPACES",
    "XML_TO_JSON_TAGS",
    "JSON_TO_XML_TAGS",
    "tag_to_name",
    "name_to_tag",
    "get_tags_for_category",
]
