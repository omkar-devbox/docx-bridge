"""Base handler for legacy Microsoft Word 97-2003 (.doc) binary formats."""

from abc import abstractmethod
import struct
from typing import Any

from handlers.common.base import CommonBaseHandler
from handlers.common.color import bgr_to_hex, hex_to_bgr
from handlers.common.units import dxa_to_pt, pt_to_dxa
from handlers.common.helpers import normalize_alignment
from config import DOC_CONFIG_DATA


class DocBaseHandler(CommonBaseHandler):
    """Abstract base handler for legacy DOC binary components and SPRMs."""

    def __init__(self):
        self.doc_config = DOC_CONFIG_DATA or {}

    @abstractmethod
    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert a binary record, stream, or piece table to JSON AST."""
        pass

    @abstractmethod
    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize JSON AST into binary stream bytes or SPRMs."""
        pass

    def to_format(self, data: dict[str, Any], **kwargs) -> bytes:
        """Format-agnostic wrapper returning binary bytes."""
        return self.to_binary(data, **kwargs)

    # --------------------------------
    # Binary Reader Helpers
    # --------------------------------

    @staticmethod
    def read_uint8(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from("<B", data, offset)[0]

    @staticmethod
    def read_int8(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from("<b", data, offset)[0]

    @staticmethod
    def read_uint16(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from("<H", data, offset)[0]

    @staticmethod
    def read_int16(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from("<h", data, offset)[0]

    @staticmethod
    def read_uint32(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from("<I", data, offset)[0]

    @staticmethod
    def read_int32(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from("<i", data, offset)[0]

    # --------------------------------
    # Shared Normalization Helpers
    # --------------------------------

    @staticmethod
    def color_to_hex(bgr_int: int) -> str:
        """Convert 32-bit BGR integer to Hex RGB string."""
        return bgr_to_hex(bgr_int)

    @staticmethod
    def hex_to_color(hex_str: str) -> int:
        """Convert Hex RGB string to 32-bit BGR integer."""
        return hex_to_bgr(hex_str)

    @staticmethod
    def align_to_json(align_code: int | str) -> str:
        """Convert DOC alignment code (0=left, 1=center, 2=right, 3=both) to JSON."""
        return normalize_alignment(align_code)

    @staticmethod
    def dxa_to_points(dxa_val: int) -> float:
        """Convert dxa twips to points."""
        return dxa_to_pt(dxa_val)


__all__ = ["DocBaseHandler"]
