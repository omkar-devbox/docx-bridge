"""Document domain handlers: document root, body, and properties."""

from handlers.docx.document.document import DocumentHandler
from handlers.docx.document.body import BodyHandler
from handlers.docx.document.properties import PropertiesHandler

__all__ = [
    "DocumentHandler",
    "BodyHandler",
    "PropertiesHandler",
]
