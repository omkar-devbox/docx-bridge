"""Formatting domain handlers: styles, paragraph properties, run properties, colors, fonts."""

from handlers.docx.formatting.styles import StylesHandler
from handlers.docx.formatting.paragraph_properties import ParagraphPropertiesHandler
from handlers.docx.formatting.run_properties import RunPropertiesHandler
from handlers.docx.formatting.colors import ColorHandler
from handlers.docx.formatting.fonts import FontHandler

__all__ = [
    "StylesHandler",
    "ParagraphPropertiesHandler",
    "RunPropertiesHandler",
    "ColorHandler",
    "FontHandler",
]
