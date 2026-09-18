"""Advanced domain handlers: content controls, revisions, math, charts, smartart."""

from handlers.docx.advanced.content_controls import ContentControlsHandler
from handlers.docx.advanced.revisions import RevisionsHandler
from handlers.docx.advanced.math import MathHandler
from handlers.docx.advanced.charts import ChartsHandler
from handlers.docx.advanced.smartart import SmartArtHandler

__all__ = [
    "ContentControlsHandler",
    "RevisionsHandler",
    "MathHandler",
    "ChartsHandler",
    "SmartArtHandler",
]
