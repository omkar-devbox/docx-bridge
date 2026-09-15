"""DOC package handling: reading and writing legacy Word 97-2003 binary files."""

from .reader import DocReader
from .writer import DocWriter

__all__ = ["DocReader", "DocWriter"]
