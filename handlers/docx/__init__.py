"""OpenXML (DOCX) handlers for WordprocessingML document components."""

from typing import Any
from handlers.docx.base import (
    BaseHandler,
    DocxBaseHandler,
    qn,
    de_qn,
    local_name,
    sort_children_by_schema,
    NAMESPACES,
)
from config import (
    XML_TO_JSON_TAGS,
    JSON_TO_XML_TAGS,
    tag_to_name,
    name_to_tag,
    get_tags_for_category,
)
from handlers.docx.document import DocumentHandler
from handlers.docx.paragraph import ParagraphHandler
from handlers.docx.run import RunHandler
from handlers.docx.table import TableHandler
from handlers.docx.styles import StylesHandler
from handlers.docx.numbering import NumberingHandler
from handlers.docx.sections import SectionsHandler
from handlers.docx.media import MediaHandler
from handlers.docx.relationships import RelationshipsHandler
from handlers.docx.header_footer import HeaderFooterHandler
from handlers.docx.properties import PropertiesHandler
from handlers.docx.notes import NotesHandler
from handlers.docx.comments import CommentsHandler
from handlers.docx.settings import SettingsHandler


class DocxHandlerRegistry:
    """Registry coordinating OpenXML handlers for element parsing and reconstruction."""

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
        self.header_footer_handler = HeaderFooterHandler(
            paragraph_handler=self.paragraph_handler,
            table_handler=self.table_handler,
        )
        self.properties_handler = PropertiesHandler()
        self.notes_handler = NotesHandler(paragraph_handler=self.paragraph_handler)
        self.comments_handler = CommentsHandler(paragraph_handler=self.paragraph_handler)
        self.settings_handler = SettingsHandler()

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
            qn("w:hdr"): self.header_footer_handler,
            qn("w:ftr"): self.header_footer_handler,
            qn("w:footnotes"): self.notes_handler,
            qn("w:endnotes"): self.notes_handler,
            qn("w:comments"): self.comments_handler,
            qn("w:settings"): self.settings_handler,
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
            "header": self.header_footer_handler,
            "footer": self.header_footer_handler,
            "footnotes": self.notes_handler,
            "endnotes": self.notes_handler,
            "comments": self.comments_handler,
            "settings": self.settings_handler,
            "metadata": self.properties_handler,
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

    # Convenience aliases
    get_by_tag = get_handler_for_tag
    get_by_type = get_handler_for_type


HandlerRegistry = DocxHandlerRegistry


__all__ = [
    "BaseHandler",
    "DocxBaseHandler",
    "DocumentHandler",
    "ParagraphHandler",
    "RunHandler",
    "TableHandler",
    "StylesHandler",
    "NumberingHandler",
    "SectionsHandler",
    "MediaHandler",
    "RelationshipsHandler",
    "HeaderFooterHandler",
    "PropertiesHandler",
    "NotesHandler",
    "CommentsHandler",
    "SettingsHandler",
    "DocxHandlerRegistry",
    "HandlerRegistry",
    "qn",
    "de_qn",
    "local_name",
    "sort_children_by_schema",
    "NAMESPACES",
    "XML_TO_JSON_TAGS",
    "JSON_TO_XML_TAGS",
    "tag_to_name",
    "name_to_tag",
    "get_tags_for_category",
]
