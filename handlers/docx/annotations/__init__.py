"""Annotations domain handlers: comments, footnotes, endnotes."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler
from handlers.docx.annotations.comments import CommentsHandler
from handlers.docx.annotations.footnotes import FootnotesHandler
from handlers.docx.annotations.endnotes import EndnotesHandler
from handlers.docx.text.paragraph import ParagraphHandler


class NotesHandler(BaseHandler):
    """Coordinates footnotes and endnotes parsing and generation."""

    def __init__(self, paragraph_handler: ParagraphHandler | None = None):
        self.paragraph_handler = paragraph_handler or ParagraphHandler()
        self.footnotes_handler = FootnotesHandler(paragraph_handler=self.paragraph_handler)
        self.endnotes_handler = EndnotesHandler(paragraph_handler=self.paragraph_handler)

    def to_json(
        self,
        element: ET.Element,
        is_endnotes: bool = False,
        simple: bool = False,
    ) -> list[dict[str, Any]]:
        """Parse footnotes or endnotes XML into a list of note dictionaries."""
        if is_endnotes:
            return self.endnotes_handler.to_json(element, simple=simple)
        return self.footnotes_handler.to_json(element, simple=simple)

    def to_xml(
        self,
        notes_data: list[dict[str, Any]] | dict[str, Any],
        is_endnotes: bool = False,
    ) -> ET.Element:
        """Construct footnotes.xml or endnotes.xml element tree."""
        if is_endnotes:
            return self.endnotes_handler.to_xml(notes_data)
        return self.footnotes_handler.to_xml(notes_data)


__all__ = [
    "CommentsHandler",
    "FootnotesHandler",
    "EndnotesHandler",
    "NotesHandler",
]
