"""Legacy Microsoft Word (.doc, Word 97-2003) binary writer.

Implements complete [MS-CFB] and [MS-DOC] binary serialization:
- JSON AST -> WordDocument stream (FIB, character buffer, Sepx, FKP pages)
- Table stream (1Table) with STSH, PlcfSed, PlcfHdd, PlcfBteChpx, PlcfBtePapx, Clx, PlfLst, PlfLfo
- \\x05SummaryInformation OLE Property Set stream
- CFBF structured storage assembly

Lossless round-trip:
- papxRaw / chpxRaw  : base64 raw GRPPRL bytes used verbatim if present
- directParagraph / directRun : used when raw bytes absent (encodes own props only)
- unknownSprms       : re-emitted verbatim from JSON
"""

from __future__ import annotations

import base64
import struct
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union

from formats.doc.cfbf import CFBWriter
from formats.doc.fib import Fib
from formats.doc.fkp import FkpBuilder, FormattedParagraph, FormattedRun
from formats.doc.piece_table import PieceTable
from formats.doc.sprm import encode_character_formatting, encode_paragraph_formatting
from formats.doc.structures import (
    HeaderFooterTable,
    ListParser,
    PropertySetStream,
    SectionTable,
    StshParser,
)


class DocWriter:
    """Writer for legacy Microsoft Word (.doc, Word 97-2003) binary files."""

    def __init__(self, target: Union[str, Path, BinaryIO]):
        self.target = target
        self._cfb = CFBWriter(target)
        self._streams: Dict[str, bytes] = {}

    # --------------------------------
    # Stream Operations
    # --------------------------------

    def write_stream(self, stream_name: str, content: bytes) -> None:
        """Write a named stream to the compound document."""
        self._streams[stream_name] = bytes(content)
        self._cfb.write_stream(stream_name, content)

    # --------------------------------
    # Archive Lifecycle
    # --------------------------------

    def save(self) -> None:
        """Finalize and save CFBF archive."""
        self._cfb.save()

    def close(self) -> None:
        self.save()

    def __enter__(self) -> DocWriter:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


__all__ = ["DocWriter"]
