"""DOCX package handling: reading and writing DOCX archives."""

from .reader import DocxReader
from .writer import DocxWriter

__all__ = ["DocxReader", "DocxWriter"]
