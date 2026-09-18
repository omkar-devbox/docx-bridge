"""OpenXML (DOCX) handlers for WordprocessingML document components."""

from typing import Any
import xml.etree.ElementTree as ET

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

# Subpackages
from handlers.docx import document
from handlers.docx import text
from handlers.docx import formatting
from handlers.docx import tables
from handlers.docx import sections
from handlers.docx import lists
from handlers.docx import media
from handlers.docx import annotations
from handlers.docx import advanced
from handlers.docx import package
from handlers.docx import settings

# Document domain
from handlers.docx.document import DocumentHandler, BodyHandler, PropertiesHandler

# Text domain
from handlers.docx.text import (
    ParagraphHandler,
    RunHandler,
    TextHandler,
    FieldsHandler,
    BookmarksHandler,
)

# Formatting domain
from handlers.docx.formatting import (
    StylesHandler,
    ParagraphPropertiesHandler,
    RunPropertiesHandler,
    ColorHandler,
    FontHandler,
)

# Tables domain
from handlers.docx.tables import (
    TableHandler,
    TableRowHandler,
    TableCellHandler,
    TablePropertiesHandler,
)

# Sections domain
from handlers.docx.sections import (
    SectionsHandler,
    SectionHandler,
    PageHandler,
    MarginsHandler,
    HeaderFooterHandler,
    PageBordersHandler,
)

# Lists domain
from handlers.docx.lists import (
    NumberingHandler,
    AbstractNumberingHandler,
    ListPropertiesHandler,
)

# Media domain
from handlers.docx.media import (
    MediaHandler,
    ImageHandler,
    DrawingHandler,
    MediaRelationshipsHandler,
)

# Annotations domain
from handlers.docx.annotations import (
    CommentsHandler,
    FootnotesHandler,
    EndnotesHandler,
    NotesHandler,
)

# Advanced domain
from handlers.docx.advanced import (
    ContentControlsHandler,
    RevisionsHandler,
    MathHandler,
    ChartsHandler,
    SmartArtHandler,
)

# Package domain
from handlers.docx.package import (
    ContentTypesHandler,
    RelationshipsHandler,
    PackageHandler,
)

# Settings domain
from handlers.docx.settings import (
    SettingsHandler,
    CompatibilityHandler,
    ThemeHandler,
)


class DocxHandlerRegistry:
    """Registry coordinating OpenXML handlers for element parsing and reconstruction."""

    def __init__(self):
        # Text
        self.text_handler = TextHandler()
        self.fields_handler = FieldsHandler()
        self.bookmarks_handler = BookmarksHandler()
        self.run_handler = RunHandler()
        self.paragraph_handler = ParagraphHandler(run_handler=self.run_handler)

        # Formatting
        self.color_handler = ColorHandler()
        self.font_handler = FontHandler()
        self.paragraph_properties_handler = ParagraphPropertiesHandler()
        self.run_properties_handler = RunPropertiesHandler()
        self.styles_handler = StylesHandler()

        # Tables
        self.cell_handler = TableCellHandler(paragraph_handler=self.paragraph_handler)
        self.row_handler = TableRowHandler(cell_handler=self.cell_handler)
        self.table_properties_handler = TablePropertiesHandler()
        self.table_handler = TableHandler(paragraph_handler=self.paragraph_handler)

        # Sections
        self.margins_handler = MarginsHandler()
        self.page_handler = PageHandler()
        self.borders_handler = PageBordersHandler()
        self.sections_handler = SectionsHandler()
        self.header_footer_handler = HeaderFooterHandler(
            paragraph_handler=self.paragraph_handler,
            table_handler=self.table_handler,
        )

        # Document
        self.body_handler = BodyHandler(
            paragraph_handler=self.paragraph_handler,
            table_handler=self.table_handler,
            sections_handler=self.sections_handler,
        )
        self.document_handler = DocumentHandler(
            paragraph_handler=self.paragraph_handler,
            table_handler=self.table_handler,
            sections_handler=self.sections_handler,
        )
        self.properties_handler = PropertiesHandler()

        # Lists
        self.list_properties_handler = ListPropertiesHandler()
        self.abstract_numbering_handler = AbstractNumberingHandler(
            list_properties_handler=self.list_properties_handler
        )
        self.numbering_handler = NumberingHandler()

        # Media
        self.drawing_handler = DrawingHandler()
        self.image_handler = ImageHandler()
        self.media_relationships_handler = MediaRelationshipsHandler()
        self.media_handler = MediaHandler()

        # Annotations
        self.comments_handler = CommentsHandler(paragraph_handler=self.paragraph_handler)
        self.footnotes_handler = FootnotesHandler(paragraph_handler=self.paragraph_handler)
        self.endnotes_handler = EndnotesHandler(paragraph_handler=self.paragraph_handler)
        self.notes_handler = NotesHandler(paragraph_handler=self.paragraph_handler)

        # Advanced
        self.content_controls_handler = ContentControlsHandler()
        self.revisions_handler = RevisionsHandler()
        self.math_handler = MathHandler()
        self.charts_handler = ChartsHandler()
        self.smartart_handler = SmartArtHandler()

        # Package
        self.content_types_handler = ContentTypesHandler()
        self.relationships_handler = RelationshipsHandler()
        self.package_handler = PackageHandler(
            content_types_handler=self.content_types_handler,
            relationships_handler=self.relationships_handler,
        )

        # Settings
        self.compatibility_handler = CompatibilityHandler()
        self.theme_handler = ThemeHandler()
        self.settings_handler = SettingsHandler()

        # Tag to handler mapping (qualified Clark tags)
        self._tag_handlers: dict[str, BaseHandler] = {
            qn("w:document"): self.document_handler,
            qn("w:body"): self.body_handler,
            qn("w:p"): self.paragraph_handler,
            qn("w:r"): self.run_handler,
            qn("w:t"): self.text_handler,
            qn("w:br"): self.text_handler,
            qn("w:cr"): self.text_handler,
            qn("w:tab"): self.text_handler,
            qn("w:sym"): self.text_handler,
            qn("w:fldSimple"): self.fields_handler,
            qn("w:fldChar"): self.fields_handler,
            qn("w:instrText"): self.fields_handler,
            qn("w:bookmarkStart"): self.bookmarks_handler,
            qn("w:bookmarkEnd"): self.bookmarks_handler,
            qn("w:pPr"): self.paragraph_properties_handler,
            qn("w:rPr"): self.run_properties_handler,
            qn("w:tbl"): self.table_handler,
            qn("w:tr"): self.row_handler,
            qn("w:tc"): self.cell_handler,
            qn("w:tblPr"): self.table_properties_handler,
            qn("w:sectPr"): self.sections_handler,
            qn("w:pgSz"): self.page_handler,
            qn("w:pgMar"): self.margins_handler,
            qn("w:pgBorders"): self.borders_handler,
            qn("w:styles"): self.styles_handler,
            qn("w:numbering"): self.numbering_handler,
            qn("w:abstractNum"): self.abstract_numbering_handler,
            qn("w:drawing"): self.media_handler,
            qn("w:hdr"): self.header_footer_handler,
            qn("w:ftr"): self.header_footer_handler,
            qn("w:footnotes"): self.notes_handler,
            qn("w:endnotes"): self.notes_handler,
            qn("w:comments"): self.comments_handler,
            qn("w:settings"): self.settings_handler,
            qn("w:sdt"): self.content_controls_handler,
            qn("w:ins"): self.revisions_handler,
            qn("w:del"): self.revisions_handler,
        }

        # JSON type name to handler mapping
        self._type_handlers: dict[str, BaseHandler] = {
            "document": self.document_handler,
            "body": self.body_handler,
            "paragraph": self.paragraph_handler,
            "run": self.run_handler,
            "text": self.text_handler,
            "break": self.text_handler,
            "tab": self.text_handler,
            "fieldSimple": self.fields_handler,
            "fieldCharacter": self.fields_handler,
            "instructionText": self.fields_handler,
            "bookmarkStart": self.bookmarks_handler,
            "bookmarkEnd": self.bookmarks_handler,
            "paragraphProperties": self.paragraph_properties_handler,
            "runProperties": self.run_properties_handler,
            "table": self.table_handler,
            "tableRow": self.row_handler,
            "tableCell": self.cell_handler,
            "tableProperties": self.table_properties_handler,
            "section": self.sections_handler,
            "sectionProperties": self.sections_handler,
            "section_properties": self.sections_handler,
            "page": self.page_handler,
            "margins": self.margins_handler,
            "pageBorders": self.borders_handler,
            "styles": self.styles_handler,
            "numbering": self.numbering_handler,
            "abstractNum": self.abstract_numbering_handler,
            "drawing": self.media_handler,
            "image": self.image_handler,
            "header": self.header_footer_handler,
            "footer": self.header_footer_handler,
            "footnotes": self.notes_handler,
            "endnotes": self.notes_handler,
            "footnote": self.footnotes_handler,
            "endnote": self.endnotes_handler,
            "comments": self.comments_handler,
            "settings": self.settings_handler,
            "metadata": self.properties_handler,
            "contentControl": self.content_controls_handler,
            "revision": self.revisions_handler,
            "mathBlock": self.math_handler,
            "mathParagraph": self.math_handler,
            "chart": self.charts_handler,
            "smartArt": self.smartart_handler,
            "package": self.package_handler,
            "theme": self.theme_handler,
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
    # Subpackages
    "document",
    "text",
    "formatting",
    "tables",
    "sections",
    "lists",
    "media",
    "annotations",
    "advanced",
    "package",
    "settings",
    # Base
    "BaseHandler",
    "DocxBaseHandler",
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
    # Document
    "DocumentHandler",
    "BodyHandler",
    "PropertiesHandler",
    # Text
    "ParagraphHandler",
    "RunHandler",
    "TextHandler",
    "FieldsHandler",
    "BookmarksHandler",
    # Formatting
    "StylesHandler",
    "ParagraphPropertiesHandler",
    "RunPropertiesHandler",
    "ColorHandler",
    "FontHandler",
    # Tables
    "TableHandler",
    "TableRowHandler",
    "TableCellHandler",
    "TablePropertiesHandler",
    # Sections
    "SectionsHandler",
    "SectionHandler",
    "PageHandler",
    "MarginsHandler",
    "HeaderFooterHandler",
    "PageBordersHandler",
    # Lists
    "NumberingHandler",
    "AbstractNumberingHandler",
    "ListPropertiesHandler",
    # Media
    "MediaHandler",
    "ImageHandler",
    "DrawingHandler",
    "MediaRelationshipsHandler",
    # Annotations
    "CommentsHandler",
    "FootnotesHandler",
    "EndnotesHandler",
    "NotesHandler",
    # Advanced
    "ContentControlsHandler",
    "RevisionsHandler",
    "MathHandler",
    "ChartsHandler",
    "SmartArtHandler",
    # Package
    "ContentTypesHandler",
    "RelationshipsHandler",
    "PackageHandler",
    # Settings
    "SettingsHandler",
    "CompatibilityHandler",
    "ThemeHandler",
    # Registry
    "DocxHandlerRegistry",
    "HandlerRegistry",
]
