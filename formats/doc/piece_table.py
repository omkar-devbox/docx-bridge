"""Word CLX and Piece Table (PlcPcd) implementation in pure Python.

Implements the [MS-DOC] 2.9.43 Clx and 2.9.171 PlcPcd specifications.
Handles CP -> FC translation, compressed ANSI text, UTF-16LE Unicode text,
and multi-piece document assembly across all Word subdocuments.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import List, Optional, Tuple

CLXT_PRC = 0x01
CLXT_PLCPCD = 0x02

FC_COMPRESSED_FLAG = 0x40000000
FC_OFFSET_MASK = 0x3FFFFFFF


@dataclass
class PieceDescriptor:
    """A Word 8-byte Piece Descriptor (Pcd)."""

    cp_start: int
    cp_end: int
    fc: int  # Raw 32-bit FcCompressed
    fNoParaLast: int = 0
    prm: int = 0

    @property
    def is_compressed(self) -> bool:
        """True if text is stored as 8-bit ANSI / Windows-1252."""
        return bool(self.fc & FC_COMPRESSED_FLAG)

    @property
    def byte_offset(self) -> int:
        """Byte offset of text in the WordDocument stream."""
        if self.is_compressed:
            return (self.fc & FC_OFFSET_MASK) // 2
        return self.fc & FC_OFFSET_MASK

    @property
    def char_count(self) -> int:
        """Number of characters in this piece."""
        return max(0, self.cp_end - self.cp_start)

    @property
    def byte_length(self) -> int:
        """Byte length of this piece in the WordDocument stream."""
        chars = self.char_count
        return chars if self.is_compressed else chars * 2

    def to_bytes(self) -> bytes:
        """Serialize PCD (8 bytes: fNoParaLast, fc, prm)."""
        return struct.pack("<HIH", self.fNoParaLast, self.fc, self.prm)


class PieceTable:
    """Represents the Piece Table decoded from Clx in the Table stream."""

    def __init__(self, pieces: Optional[List[PieceDescriptor]] = None):
        self.pieces: List[PieceDescriptor] = pieces or []

    @classmethod
    def parse_clx(cls, clx_bytes: bytes) -> PieceTable:
        """Parse Clx byte sequence to extract PlcPcd and Piece Table."""
        offset = 0
        total_len = len(clx_bytes)

        # Skip any PRC (property modifier) records
        while offset < total_len:
            clxt = clx_bytes[offset]
            offset += 1

            if clxt == CLXT_PRC:
                if offset + 2 > total_len:
                    break
                cb = struct.unpack_from("<H", clx_bytes, offset)[0]
                offset += 2 + cb
            elif clxt == CLXT_PLCPCD:
                if offset + 4 > total_len:
                    break
                lcb = struct.unpack_from("<I", clx_bytes, offset)[0]
                offset += 4
                plcpcd_bytes = clx_bytes[offset : offset + lcb]
                return cls.parse_plcpcd(plcpcd_bytes)
            else:
                break

        return cls([])

    @classmethod
    def parse_plcpcd(cls, plcpcd_bytes: bytes) -> PieceTable:
        """Parse PlcPcd: array of (n + 1) CPs followed by n PCDs."""
        if len(plcpcd_bytes) < 4:
            return cls([])

        # Formula: len = (n + 1) * 4 + n * 8 = 4 + 12 * n => n = (len - 4) // 12
        num_pieces = (len(plcpcd_bytes) - 4) // 12
        if num_pieces <= 0:
            return cls([])

        cp_bytes = plcpcd_bytes[: (num_pieces + 1) * 4]
        pcd_bytes = plcpcd_bytes[(num_pieces + 1) * 4 : (num_pieces + 1) * 4 + num_pieces * 8]

        cps = list(struct.unpack(f"<{num_pieces + 1}I", cp_bytes))
        pieces = []

        for i in range(num_pieces):
            pcd_chunk = pcd_bytes[i * 8 : (i + 1) * 8]
            fNoParaLast, fc, prm = struct.unpack("<HIH", pcd_chunk)
            piece = PieceDescriptor(
                cp_start=cps[i],
                cp_end=cps[i + 1],
                fc=fc,
                fNoParaLast=fNoParaLast,
                prm=prm,
            )
            pieces.append(piece)

        return cls(pieces)

    def get_total_cps(self) -> int:
        """Total character count across all pieces."""
        return self.pieces[-1].cp_end if self.pieces else 0

    def get_text(
        self,
        word_doc_bytes: bytes,
        start_cp: int = 0,
        end_cp: Optional[int] = None,
        encoding: str = "windows-1252",
    ) -> str:
        """Extract and decode text across CPs."""
        if not self.pieces:
            return ""

        if end_cp is None:
            end_cp = self.get_total_cps()

        start_cp = max(0, start_cp)
        end_cp = min(self.get_total_cps(), end_cp)
        if start_cp >= end_cp:
            return ""

        chunks: List[str] = []
        for piece in self.pieces:
            # Check overlap
            overlap_start = max(piece.cp_start, start_cp)
            overlap_end = min(piece.cp_end, end_cp)
            if overlap_start >= overlap_end:
                continue

            char_offset_in_piece = overlap_start - piece.cp_start
            char_count = overlap_end - overlap_start

            if piece.is_compressed:
                # 1 byte per character
                byte_start = piece.byte_offset + char_offset_in_piece
                raw_slice = word_doc_bytes[byte_start : byte_start + char_count]
                try:
                    text_part = raw_slice.decode(encoding, errors="replace")
                except Exception:
                    text_part = raw_slice.decode("latin-1", errors="replace")
            else:
                # 2 bytes per character (UTF-16LE)
                byte_start = piece.byte_offset + (char_offset_in_piece * 2)
                raw_slice = word_doc_bytes[byte_start : byte_start + (char_count * 2)]
                text_part = raw_slice.decode("utf-16le", errors="replace")

            chunks.append(text_part)

        return "".join(chunks)

    def cp_to_fc(self, cp: int) -> Optional[Tuple[int, bool]]:
        """Map a Character Position (CP) to (fc_offset, is_compressed)."""
        for piece in self.pieces:
            if piece.cp_start <= cp < piece.cp_end:
                offset_chars = cp - piece.cp_start
                if piece.is_compressed:
                    return piece.byte_offset + offset_chars, True
                return piece.byte_offset + (offset_chars * 2), False
        return None

    def get_piece_for_cp(self, cp: int) -> Optional[PieceDescriptor]:
        """Find the piece descriptor containing the given CP."""
        for piece in self.pieces:
            if piece.cp_start <= cp < piece.cp_end:
                return piece
        return None

    @classmethod
    def build_from_text(
        cls,
        text: str,
        start_fc: int = 512,
        encoding: str = "windows-1252",
    ) -> Tuple[bytes, bytes, PieceTable]:
        """Build WordDocument character bytes, Clx bytes, and PieceTable instance.

        Returns:
            (word_doc_chunk, clx_bytes, piece_table)
        """
        # Decide if text can be compressed (all characters in Windows-1252 / latin-1)
        can_compress = True
        try:
            encoded_bytes = text.encode(encoding)
            cp_len = len(encoded_bytes)
        except UnicodeEncodeError:
            can_compress = False
            encoded_bytes = text.encode("utf-16le")
            cp_len = len(encoded_bytes) // 2
        if can_compress:
            # Word uses bit 30 flag and double-offset for compressed FC:
            # fc = FC_COMPRESSED_FLAG | (start_fc * 2)
            fc = FC_COMPRESSED_FLAG | (start_fc * 2)
        else:
            fc = start_fc

        pcd = PieceDescriptor(
            cp_start=0,
            cp_end=cp_len,
            fc=fc,
            fNoParaLast=0,
            prm=0,
        )

        pt = cls([pcd])
        clx_bytes = pt.to_clx_bytes()
        return encoded_bytes, clx_bytes, pt

    def to_clx_bytes(self) -> bytes:
        """Serialize piece table to complete Clx binary record."""
        plcpcd_bytes = self.to_plcpcd_bytes()
        # clxt (1 byte = 0x02) + lcb (4 bytes) + plcpcd_bytes
        return struct.pack("<BI", CLXT_PLCPCD, len(plcpcd_bytes)) + plcpcd_bytes

    def to_plcpcd_bytes(self) -> bytes:
        """Serialize to PlcPcd bytes: (n+1) CPs + n PCDs."""
        if not self.pieces:
            return struct.pack("<I", 0)

        cps = [p.cp_start for p in self.pieces] + [self.pieces[-1].cp_end]
        cp_bytes = struct.pack(f"<{len(cps)}I", *cps)
        pcd_bytes = b"".join(p.to_bytes() for p in self.pieces)
        return cp_bytes + pcd_bytes


__all__ = [
    "PieceTable",
    "PieceDescriptor",
    "CLXT_PRC",
    "CLXT_PLCPCD",
    "FC_COMPRESSED_FLAG",
    "FC_OFFSET_MASK",
]
