"""Microsoft Word File Information Block (FIB) parser and serializer.

Implements the [MS-DOC] 2.5.1 FIB specifications for Word 97-2003 binary formats.
Manages stream references, character position partitions, and Table stream pointers.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from config import DOC_CONFIG_DATA

FIB_MAGIC = 0xA5EC

# Default nFib versions
NFIB_WORD97 = 0x00C3
NFIB_WORD2000 = 0x00D9
NFIB_WORD2002 = 0x0101
NFIB_WORD2003 = 0x010C

# Named offsets into fibRgFcLcb (by pair index)
FIB_POINTER_NAMES = {
    "StshfOrig": 0,
    "Stshf": 1,
    "PlcffndRef": 2,
    "PlcffndTxt": 3,
    "PlcfandRef": 4,
    "PlcfandTxt": 5,
    "PlcfSed": 6,
    "PlcPad": 7,
    "PlcfPhe": 8,
    "SttbfGls": 9,
    "PlcfGls": 10,
    "PlcfHdd": 11,
    "PlcfBteChpx": 12,
    "PlcfBtePapx": 13,
    "PlcfSea": 14,
    "SttbfBkmk": 15,
    "PlcfBkf": 16,
    "PlcfBkl": 17,
    "Cmds": 18,
    "Plcmcr": 19,
    "Sttbmcr": 20,
    "PrEnv": 21,
    "Wss": 22,
    "Dop": 25,
    "SttbfAssoc": 26,
    "Clx": 33,
    "PlcfPgp": 28,
    "Plcfuim": 29,
    "Sprm": 30,
    "DefSpls": 31,
    "DggInfo": 32,
    "SttbfRMark": 33,
    "PlcfFldMom": 34,
    "PlcfFldHdr": 35,
    "PlcfFldFtn": 36,
    "PlcfFldAtn": 37,
    "PlcfFldMcr": 38,
    "SttbfFfn": 39,
    "PlcfFldEdn": 42,
    "PlcfendRef": 46,
    "PlcfendTxt": 47,
    "PlfLst": 73,
    "PlfLfo": 74,
    "PlcBteLvc": 75,
}


@dataclass
class FibBase:
    """The first 32 bytes of the WordDocument stream."""

    wIdent: int = FIB_MAGIC
    nFib: int = NFIB_WORD97
    nProduct: int = 0
    lid: int = 0x0409  # English US
    pnNext: int = 0
    fDot: bool = False
    fGls: bool = False
    fComplex: bool = True  # Piece table is present
    fHasPic: bool = False
    cQuickSaves: int = 0
    fEncrypted: bool = False
    fWhichTblStm: bool = True  # True -> "1Table", False -> "0Table"
    fReadOnlyRecommended: bool = False
    fWriteReservation: bool = False
    fExtChar: bool = True
    fLoadOverride: bool = False
    fFarEast: bool = False
    fCrypto: bool = False
    nFibBack: int = 0x00BF
    lKey: int = 0
    envr: int = 0
    fMac: bool = False
    fEmptySpecial: bool = False
    fLoadOverridePage: bool = False
    fFutureSavedUndo: bool = False
    fWord97Saved: bool = True
    fcMin: int = 0x0200  # Default character start offset (512)
    fcMac: int = 0x0200  # Default character end offset

    @property
    def table_stream_name(self) -> str:
        """Name of the table stream specified by fWhichTblStm."""
        return "1Table" if self.fWhichTblStm else "0Table"

    @classmethod
    def parse(cls, data: bytes) -> FibBase:
        if len(data) < 32:
            raise ValueError(f"FIB Base must be at least 32 bytes, got {len(data)}")

        (
            wIdent,
            nFib,
            nProduct,
            lid,
            pnNext,
            flags,
            nFibBack,
            lKey,
            envr,
            flags2,
            fcMin,
            fcMac,
        ) = struct.unpack_from("<HHHHHHHiBB4xII", data, 0)
        if wIdent != FIB_MAGIC:
            raise ValueError(f"Invalid FIB magic number: {hex(wIdent)} (expected {hex(FIB_MAGIC)})")

        return cls(
            wIdent=wIdent,
            nFib=nFib,
            nProduct=nProduct,
            lid=lid,
            pnNext=pnNext,
            fDot=bool(flags & 0x0001),
            fGls=bool(flags & 0x0002),
            fComplex=bool(flags & 0x0004),
            fHasPic=bool(flags & 0x0008),
            cQuickSaves=(flags >> 4) & 0x000F,
            fEncrypted=bool(flags & 0x0100),
            fWhichTblStm=bool(flags & 0x0200),
            fReadOnlyRecommended=bool(flags & 0x0400),
            fWriteReservation=bool(flags & 0x0800),
            fExtChar=bool(flags & 0x1000),
            fLoadOverride=bool(flags & 0x2000),
            fFarEast=bool(flags & 0x4000),
            fCrypto=bool(flags & 0x8000),
            nFibBack=nFibBack,
            lKey=lKey,
            envr=envr,
            fMac=bool(flags2 & 0x01),
            fEmptySpecial=bool(flags2 & 0x02),
            fLoadOverridePage=bool(flags2 & 0x04),
            fFutureSavedUndo=bool(flags2 & 0x08),
            fWord97Saved=bool(flags2 & 0x10),
            fcMin=fcMin,
            fcMac=fcMac,
        )

    def to_bytes(self) -> bytes:
        flags = (
            (1 if self.fDot else 0)
            | ((1 if self.fGls else 0) << 1)
            | ((1 if self.fComplex else 0) << 2)
            | ((1 if self.fHasPic else 0) << 3)
            | ((self.cQuickSaves & 0x0F) << 4)
            | ((1 if self.fEncrypted else 0) << 8)
            | ((1 if self.fWhichTblStm else 0) << 9)
            | ((1 if self.fReadOnlyRecommended else 0) << 10)
            | ((1 if self.fWriteReservation else 0) << 11)
            | ((1 if self.fExtChar else 0) << 12)
            | ((1 if self.fLoadOverride else 0) << 13)
            | ((1 if self.fFarEast else 0) << 14)
            | ((1 if self.fCrypto else 0) << 15)
        )
        flags2 = (
            (1 if self.fMac else 0)
            | ((1 if self.fEmptySpecial else 0) << 1)
            | ((1 if self.fLoadOverridePage else 0) << 2)
            | ((1 if self.fFutureSavedUndo else 0) << 3)
            | ((1 if self.fWord97Saved else 0) << 4)
        )
        return struct.pack(
            "<HHHHHHHiBB4xII",
            self.wIdent,
            self.nFib,
            self.nProduct,
            self.lid,
            self.pnNext,
            flags,
            self.nFibBack,
            self.lKey,
            self.envr,
            flags2,
            self.fcMin,
            self.fcMac,
        )


@dataclass
class FibRgLw:
    """FIB Long Word array holding CP subdocument boundary lengths."""

    cbMac: int = 0
    ccpText: int = 0
    ccpFtn: int = 0
    ccpHdd: int = 0
    ccpMcr: int = 0
    ccpAtn: int = 0
    ccpEdn: int = 0
    ccpTxbx: int = 0
    ccpHdrTxbx: int = 0
    raw_longs: List[int] = field(default_factory=list)

    @classmethod
    def parse(cls, longs: List[int]) -> FibRgLw:
        inst = cls(raw_longs=longs)
        if len(longs) > 0:
            inst.cbMac = longs[0]
        if len(longs) > 3:
            inst.ccpText = longs[3]
        if len(longs) > 4:
            inst.ccpFtn = longs[4]
        if len(longs) > 5:
            inst.ccpHdd = longs[5]
        if len(longs) > 6:
            inst.ccpMcr = longs[6]
        if len(longs) > 7:
            inst.ccpAtn = longs[7]
        if len(longs) > 8:
            inst.ccpEdn = longs[8]
        if len(longs) > 9:
            inst.ccpTxbx = longs[9]
        if len(longs) > 10:
            inst.ccpHdrTxbx = longs[10]
        return inst

    def to_longs(self, count: int = 22) -> List[int]:
        longs = [0] * max(count, 22)
        longs[0] = self.cbMac
        longs[3] = self.ccpText
        longs[4] = self.ccpFtn
        longs[5] = self.ccpHdd
        longs[6] = self.ccpMcr
        longs[7] = self.ccpAtn
        longs[8] = self.ccpEdn
        longs[9] = self.ccpTxbx
        longs[10] = self.ccpHdrTxbx
        for i in range(min(len(self.raw_longs), len(longs))):
            if i not in (0, 3, 4, 5, 6, 7, 8, 9, 10):
                longs[i] = self.raw_longs[i]
        return longs


class Fib:
    """Full File Information Block representation."""

    def __init__(self, base: Optional[FibBase] = None):
        self.base = base or FibBase()
        self.rg_w: List[int] = [0] * 14
        self.rg_lw = FibRgLw()
        self.pointers: Dict[str, Tuple[int, int]] = {}  # name -> (fc, lcb)
        self.raw_pairs: List[Tuple[int, int]] = []

    @classmethod
    def parse(cls, data: bytes) -> Fib:
        """Parse FIB from the start of WordDocument stream."""
        base = FibBase.parse(data[:32])
        inst = cls(base)
        offset = 32

        # 1. csw and fibRgW
        if len(data) >= offset + 2:
            csw = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            if len(data) >= offset + csw * 2:
                inst.rg_w = list(struct.unpack_from(f"<{csw}H", data, offset))
                offset += csw * 2

        # 2. cslw and fibRgLw
        if len(data) >= offset + 2:
            cslw = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            if len(data) >= offset + cslw * 4:
                raw_longs = list(struct.unpack_from(f"<{cslw}I", data, offset))
                inst.rg_lw = FibRgLw.parse(raw_longs)
                offset += cslw * 4

        # 3. cbRgFcLcb and fibRgFcLcb
        if len(data) >= offset + 2:
            cbRgFcLcb = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            num_pairs = cbRgFcLcb
            inst.raw_pairs = []
            for pair_idx in range(num_pairs):
                if offset + 8 <= len(data):
                    fc, lcb = struct.unpack_from("<II", data, offset)
                    inst.raw_pairs.append((fc, lcb))
                    offset += 8
                else:
                    inst.raw_pairs.append((0, 0))

            # Map named pointers
            for name, pair_idx in FIB_POINTER_NAMES.items():
                if pair_idx < len(inst.raw_pairs):
                    inst.pointers[name] = inst.raw_pairs[pair_idx]
                else:
                    inst.pointers[name] = (0, 0)

        return inst

    def get_pointer(self, name: str) -> Tuple[int, int]:
        """Get (fc, lcb) for a pointer name (e.g. 'Clx', 'fcClx', 'Stshf')."""
        clean = name
        if clean.startswith("fc") or clean.startswith("lcb"):
            clean = clean[2:] if clean.startswith("fc") else clean[3:]
        return self.pointers.get(clean, (0, 0))

    def set_pointer(self, name: str, fc: int, lcb: int) -> None:
        """Set (fc, lcb) for a pointer name."""
        clean = name
        if clean.startswith("fc") or clean.startswith("lcb"):
            clean = clean[2:] if clean.startswith("fc") else clean[3:]
        self.pointers[clean] = (fc, lcb)
        if clean in FIB_POINTER_NAMES:
            idx = FIB_POINTER_NAMES[clean]
            while len(self.raw_pairs) <= idx:
                self.raw_pairs.append((0, 0))
            self.raw_pairs[idx] = (fc, lcb)

    def to_bytes(self, num_pairs: int = 93) -> bytes:
        """Serialize full FIB structure to bytes."""
        out = bytearray(self.base.to_bytes())

        # fibRgW
        csw = len(self.rg_w)
        out.extend(struct.pack("<H", csw))
        out.extend(struct.pack(f"<{csw}H", *self.rg_w))

        # fibRgLw
        longs = self.rg_lw.to_longs()
        cslw = len(longs)
        out.extend(struct.pack("<H", cslw))
        out.extend(struct.pack(f"<{cslw}I", *longs))

        # fibRgFcLcb
        # Sync pointers into raw_pairs
        pairs = list(self.raw_pairs)
        if len(pairs) < num_pairs:
            pairs.extend([(0, 0)] * (num_pairs - len(pairs)))

        for name, (fc, lcb) in self.pointers.items():
            if name in FIB_POINTER_NAMES:
                idx = FIB_POINTER_NAMES[name]
                if idx < len(pairs):
                    pairs[idx] = (fc, lcb)

        cbRgFcLcb = len(pairs)
        out.extend(struct.pack("<H", cbRgFcLcb))
        for fc, lcb in pairs:
            out.extend(struct.pack("<II", fc, lcb))

        # Pad FIB to 512-byte boundary
        pad_len = (512 - (len(out) % 512)) % 512
        out.extend(b"\x00" * pad_len)
        return bytes(out)


__all__ = [
    "Fib",
    "FibBase",
    "FibRgLw",
    "FIB_MAGIC",
    "NFIB_WORD97",
    "NFIB_WORD2000",
    "NFIB_WORD2002",
    "NFIB_WORD2003",
    "FIB_POINTER_NAMES",
]
