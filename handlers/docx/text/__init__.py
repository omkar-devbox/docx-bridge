"""Text domain handlers: paragraph, run, text tokens, fields, bookmarks."""

from handlers.docx.text.paragraph import ParagraphHandler
from handlers.docx.text.run import RunHandler
from handlers.docx.text.text import TextHandler
from handlers.docx.text.fields import FieldsHandler
from handlers.docx.text.bookmarks import BookmarksHandler

__all__ = [
    "ParagraphHandler",
    "RunHandler",
    "TextHandler",
    "FieldsHandler",
    "BookmarksHandler",
]
