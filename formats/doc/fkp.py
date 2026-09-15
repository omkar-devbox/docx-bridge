"""Formatted Disk Page (FKP) parser and builder for CHPX and PAPX.

Implements [MS-DOC] 2.9.36 ChpxFkp, 2.9.176 PapxFkp, 2.8.25 PlcfBteChpx, and 2.8.26 PlcfBtePapx.
Maps File Character Positions (FC) to character runs and paragraph formatting.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from formats.doc.sprm import (
    decode_character_formatting,
    decode_paragraph_formatting,
    encode_character_formatting,
    encode_paragraph_formatting,
)

PAGE_SIZE = 512


@dataclass
class FormattedRun:
    """A character run with FC bounds and decoded formatting."""

    fc_start: int
    fc_end: int
    grpprl: bytes = b""
    props: dict = field(default_factory=dict)


@dataclass
class FormattedParagraph:
    """A paragraph with FC bounds, style index, and decoded formatting."""

    fc_start: int
    fc_end: int
    istd: int = 0
    grpprl: bytes = b""
    props: dict = field(default_factory=dict)


class FkpParser:
    """Parses ChpxFkp and PapxFkp pages from WordDocument stream."""

    @staticmethod
    def parse_chpx_fkp(page_bytes: bytes) -> List[FormattedRun]:
        """Parse a 512-byte ChpxFkp disk page."""
        if len(page_bytes) < PAGE_SIZE:
            return []

        crun = page_bytes[511]
        if crun == 0:
            return []

        # Read (crun + 1) FCs
        fcs = list(struct.unpack_from(f"<{crun + 1}I", page_bytes, 0))
        # Offsets table (1 byte per run)
        offset_table_start = (crun + 1) * 4
        offsets = list(page_bytes[offset_table_start : offset_table_start + crun])

        runs: List[FormattedRun] = []
        for i in range(crun):
            off = offsets[i] * 2  # word offset to byte offset or direct offset
            # Try direct offset if word offset exceeds page
            if off >= 511 or off == 0:
                off = offsets[i]
            if off >= 511:
                continue

            cb = page_bytes[off]
            grpprl = page_bytes[off + 1 : off + 1 + cb]
            props = decode_character_formatting(grpprl)

            runs.append(
                FormattedRun(
                    fc_start=fcs[i],
                    fc_end=fcs[i + 1],
                    grpprl=grpprl,
                    props=props,
                )
            )

        return runs

    @staticmethod
    def parse_papx_fkp(page_bytes: bytes) -> List[FormattedParagraph]:
        """Parse a 512-byte PapxFkp disk page."""
        if len(page_bytes) < PAGE_SIZE:
            return []

        cpara = page_bytes[511]
        if cpara == 0:
            return []

        fcs = list(struct.unpack_from(f"<{cpara + 1}I", page_bytes, 0))
        offset_table_start = (cpara + 1) * 4

        # In Word 97-2003, each entry in rgbx is a 13-byte BxPap (1 byte bOffset + 12 byte Phe)
        # In minimal/test formats it might be 1 byte. Determine whether 13-byte or 1-byte layout is used.
        is_13_byte = (offset_table_start + cpara * 13 <= 511)
        if is_13_byte and cpara > 1:
            b0 = page_bytes[offset_table_start]
            b1 = page_bytes[offset_table_start + 1]
            # In 13-byte layout, byte 1 is phe (typically 0), and b0*2 >= offset_table_start + cpara * 13
            if b0 * 2 < offset_table_start + cpara * 13 or (b1 != 0 and b1 * 2 < 511 and b0 * 2 < 511):
                is_13_byte = False
        bx_step = 13 if is_13_byte else 1

        paragraphs: List[FormattedParagraph] = []

        for i in range(cpara):
            bx_off = offset_table_start + i * bx_step
            if bx_off >= 511:
                break
            bx = page_bytes[bx_off]
            off = bx * 2
            if off >= 511 or off == 0:
                off = bx
            if off >= 511:
                continue

            cb = page_bytes[off]
            # If cb is 0, length byte is at off + 1 (in 2-byte word units)
            data_start = off + 1
            actual_cb = cb
            if cb == 0 and off + 2 < 511:
                actual_cb = page_bytes[off + 1] * 2
                data_start = off + 2

            if data_start + actual_cb > 511:
                actual_cb = max(0, 511 - data_start)

            papx_bytes = page_bytes[data_start : data_start + actual_cb]
            istd = 0
            grpprl = papx_bytes
            if len(papx_bytes) >= 2:
                istd = struct.unpack_from("<H", papx_bytes, 0)[0]
                grpprl = papx_bytes[2:]

            props = decode_paragraph_formatting(grpprl)
            props["styleIndex"] = istd

            paragraphs.append(
                FormattedParagraph(
                    fc_start=fcs[i],
                    fc_end=fcs[i + 1],
                    istd=istd,
                    grpprl=grpprl,
                    props=props,
                )
            )

        return paragraphs

    @classmethod
    def parse_plcf_bte_chpx(
        cls,
        plcf_bytes: bytes,
        word_doc_bytes: bytes,
    ) -> List[FormattedRun]:
        """Parse PlcfBteChpx bin-table and extract all character runs."""
        if len(plcf_bytes) < 8:
            return []

        # Formula: n FCs + 1 final FC + n PNs => (n + 1)*4 + n*4 = 4 + 8*n
        n = (len(plcf_bytes) - 4) // 8
        if n <= 0:
            return []

        pn_start = (n + 1) * 4
        pns = struct.unpack_from(f"<{n}I", plcf_bytes, pn_start)

        all_runs: List[FormattedRun] = []
        for pn in pns:
            page_offset = pn * PAGE_SIZE
            page_data = word_doc_bytes[page_offset : page_offset + PAGE_SIZE]
            all_runs.extend(cls.parse_chpx_fkp(page_data))

        return all_runs

    @classmethod
    def parse_plcf_bte_papx(
        cls,
        plcf_bytes: bytes,
        word_doc_bytes: bytes,
    ) -> List[FormattedParagraph]:
        """Parse PlcfBtePapx bin-table and extract all formatted paragraphs."""
        if len(plcf_bytes) < 8:
            return []

        n = (len(plcf_bytes) - 4) // 8
        if n <= 0:
            return []

        pn_start = (n + 1) * 4
        pns = struct.unpack_from(f"<{n}I", plcf_bytes, pn_start)

        all_paras: List[FormattedParagraph] = []
        for pn in pns:
            page_offset = pn * PAGE_SIZE
            page_data = word_doc_bytes[page_offset : page_offset + PAGE_SIZE]
            all_paras.extend(cls.parse_papx_fkp(page_data))

        return all_paras


class FkpBuilder:
    """Builds 512-byte ChpxFkp / PapxFkp pages and PlcfBteChpx / PlcfBtePapx tables."""

    @staticmethod
    def build_chpx_fkp(runs: List[FormattedRun]) -> Tuple[bytes, int]:
        """Serialize as many FormattedRun as fit into a 512-byte ChpxFkp disk page."""
        page = bytearray(PAGE_SIZE)
        if not runs:
            return bytes(page), 0

        k = 0
        payloads: List[Tuple[int, bytes]] = []
        total_payload_len = 0
        for r in runs:
            cb = len(r.grpprl)
            pl_len = (1 + cb + 1) & ~1
            new_k = k + 1
            table_size = (new_k + 1) * 4 + new_k * 1
            if table_size + total_payload_len + pl_len > 511:
                break
            k = new_k
            payloads.append((cb, r.grpprl))
            total_payload_len += pl_len

        if k == 0 and runs:
            k = 1
            payloads = [(len(runs[0].grpprl), runs[0].grpprl)]

        crun = k
        page[511] = crun
        fcs = [r.fc_start for r in runs[:crun]] + [runs[crun - 1].fc_end]
        struct.pack_into(f"<{crun + 1}I", page, 0, *fcs)

        offset_table_start = (crun + 1) * 4
        curr_top = 511

        for i, (cb, grpprl) in enumerate(payloads):
            curr_top = (curr_top - (1 + cb)) & ~1
            page[curr_top] = cb
            page[curr_top + 1 : curr_top + 1 + cb] = grpprl
            word_offset = curr_top // 2
            page[offset_table_start + i] = min(255, word_offset)

        return bytes(page), crun

    @staticmethod
    def build_papx_fkp(paras: List[FormattedParagraph]) -> Tuple[bytes, int]:
        """Serialize as many FormattedParagraph as fit into a 512-byte PapxFkp disk page."""
        page = bytearray(PAGE_SIZE)
        if not paras:
            return bytes(page), 0

        k = 0
        payloads: List[Tuple[int, bytes]] = []
        total_payload_len = 0
        for p in paras:
            pl = struct.pack("<H", p.istd) + p.grpprl
            cb = len(pl)
            pl_len = (1 + cb + 1) & ~1
            new_k = k + 1
            table_size = (new_k + 1) * 4 + new_k * 13
            if table_size + total_payload_len + pl_len > 511:
                break
            k = new_k
            payloads.append((cb, pl))
            total_payload_len += pl_len

        if k == 0 and paras:
            k = 1
            pl = struct.pack("<H", paras[0].istd) + paras[0].grpprl
            payloads = [(len(pl), pl)]

        cpara = k
        page[511] = cpara
        fcs = [p.fc_start for p in paras[:cpara]] + [paras[cpara - 1].fc_end]
        struct.pack_into(f"<{cpara + 1}I", page, 0, *fcs)

        offset_table_start = (cpara + 1) * 4
        curr_top = 511

        for i, (cb, payload) in enumerate(payloads):
            curr_top = (curr_top - (1 + cb)) & ~1
            page[curr_top] = cb
            page[curr_top + 1 : curr_top + 1 + cb] = payload
            word_offset = curr_top // 2
            page[offset_table_start + i * 13] = min(255, word_offset)

        return bytes(page), cpara

    @classmethod
    def build_chpx_pages(
        cls,
        runs: List[FormattedRun],
        start_page_num: int,
    ) -> Tuple[bytes, bytes]:
        """Build ChpxFkp pages and corresponding PlcfBteChpx bin-table bytes.

        Returns:
            (fkp_pages_bytes, plcf_bte_bytes)
        """
        if not runs:
            return b"", b""

        pages: List[bytes] = []
        page_nums: List[int] = []
        page_bounds: List[int] = []

        idx = 0
        while idx < len(runs):
            page_data, count = cls.build_chpx_fkp(runs[idx:])
            pn = start_page_num + len(pages)
            pages.append(page_data)
            page_nums.append(pn)
            page_bounds.append(runs[idx].fc_start)
            idx += max(1, count)

        page_bounds.append(runs[-1].fc_end)

        # Build PlcfBte: (n + 1) FCs + n PNs
        plcf = bytearray()
        plcf.extend(struct.pack(f"<{len(page_bounds)}I", *page_bounds))
        plcf.extend(struct.pack(f"<{len(page_nums)}I", *page_nums))

        return b"".join(pages), bytes(plcf)

    @classmethod
    def build_papx_pages(
        cls,
        paras: List[FormattedParagraph],
        start_page_num: int,
    ) -> Tuple[bytes, bytes]:
        """Build PapxFkp pages and corresponding PlcfBtePapx bin-table bytes.

        Returns:
            (fkp_pages_bytes, plcf_bte_bytes)
        """
        if not paras:
            return b"", b""

        pages: List[bytes] = []
        page_nums: List[int] = []
        page_bounds: List[int] = []

        idx = 0
        while idx < len(paras):
            page_data, count = cls.build_papx_fkp(paras[idx:])
            pn = start_page_num + len(pages)
            pages.append(page_data)
            page_nums.append(pn)
            page_bounds.append(paras[idx].fc_start)
            idx += max(1, count)

        page_bounds.append(paras[-1].fc_end)

        plcf = bytearray()
        plcf.extend(struct.pack(f"<{len(page_bounds)}I", *page_bounds))
        plcf.extend(struct.pack(f"<{len(page_nums)}I", *page_nums))

        return b"".join(pages), bytes(plcf)


__all__ = [
    "FormattedRun",
    "FormattedParagraph",
    "FkpParser",
    "FkpBuilder",
    "PAGE_SIZE",
]
