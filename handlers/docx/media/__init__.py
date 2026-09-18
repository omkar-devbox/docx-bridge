"""Media domain handlers: media, image, drawing, relationships."""

from handlers.docx.media.media import MediaHandler
from handlers.docx.media.image import ImageHandler
from handlers.docx.media.drawing import DrawingHandler
from handlers.docx.media.relationships import MediaRelationshipsHandler

__all__ = [
    "MediaHandler",
    "ImageHandler",
    "DrawingHandler",
    "MediaRelationshipsHandler",
]
