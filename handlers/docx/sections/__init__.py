"""Sections domain handlers: section, page, margins, header_footer, borders."""

from handlers.docx.sections.section import SectionsHandler, SectionHandler
from handlers.docx.sections.page import PageHandler
from handlers.docx.sections.margins import MarginsHandler
from handlers.docx.sections.header_footer import HeaderFooterHandler
from handlers.docx.sections.borders import PageBordersHandler

__all__ = [
    "SectionsHandler",
    "SectionHandler",
    "PageHandler",
    "MarginsHandler",
    "HeaderFooterHandler",
    "PageBordersHandler",
]
