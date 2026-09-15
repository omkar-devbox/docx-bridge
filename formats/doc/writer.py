"""Legacy Microsoft Word (.doc, Word 97-2003) binary writer.

Implements complete [MS-CFB] and [MS-DOC] binary serialization:
- JSON AST -> WordDocument stream (FIB, character buffer, Sepx, FKP pages)
- Table stream (1Table) with STSH, PlcfSed, PlcfHdd, PlcfBteChpx, PlcfBtePapx, Clx, PlfLst, PlfLfo
- \x05SummaryInformation OLE Property Set stream
- CFBF structured storage assembly
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
    # Complete Document Serialization
    # --------------------------------

    def build_document(self, data: Dict[str, Any]) -> None:
        """Serialize unified JSON AST into complete Microsoft Word 97-2003 binary streams."""
        # 1. Stylesheet (STSH)
        styles_dict = data.get("styles", {})
        stsh_bytes, style_map = StshParser.build(styles_dict)

        # 2. Extract content, runs, and paragraphs
        sections = data.get("sections", [])
        if not sections and "body" in data:
            sections = [{"content": data["body"]}]
        elif not sections and "content" in data:
            sections = [{"content": data["content"]}]

        # Pre-calculate FIB size
        dummy_fib = Fib()
        fib_size = len(dummy_fib.to_bytes())
        start_fc = fib_size

        # Determine whether text needs UTF-16LE (2 bytes/char) or can be compressed (1 byte/char)
        all_text = []
        for sec in sections:
            for item in sec.get("content", []):
                all_text.append(item.get("text", ""))

        can_compress = True
        try:
            "".join(all_text).encode("windows-1252")
        except UnicodeEncodeError:
            can_compress = False
        char_step = 1 if can_compress else 2

        main_text, formatted_runs, formatted_paras = self._process_content(
            sections,
            style_map,
            start_fc=start_fc,
            char_step=char_step,
        )

        # 3. Headers and Footers subdocument
        headers = data.get("headers", {})
        footers = data.get("footers", {})
        hdd_text, plcf_hdd_bytes = HeaderFooterTable.build(headers, footers)

        # 4. Total text assembly across subdocuments
        # Main text + Footnotes (empty) + Headers/Footers
        ccp_text = len(main_text)
        ccp_ftn = 0
        ccp_hdd = len(hdd_text)

        full_doc_text = main_text + hdd_text

        # 5. Build Piece Table & character buffer
        # Character buffer starts after FIB (offset start_fc)
        text_chunk, clx_bytes, piece_table = PieceTable.build_from_text(
            full_doc_text,
            start_fc=start_fc,
            encoding="windows-1252",
        )

        curr_fc = start_fc + len(text_chunk)

        # 6. Build Sections (SED / SEP)
        sepx_bytes, plcf_sed_bytes = SectionTable.build(
            sections,
            total_cps=ccp_text,
            start_fc=curr_fc,
        )
        curr_fc += len(sepx_bytes)

        # 7. Formatted Disk Pages (FKP) for CHPX & PAPX
        # Align curr_fc to 512-byte boundary
        pad_fkp = (512 - (curr_fc % 512)) % 512
        fkp_padding = b"\x00" * pad_fkp
        curr_fc += pad_fkp

        start_page_num = curr_fc // 512

        # Build CHPX pages
        chpx_pages, plcf_bte_chpx = FkpBuilder.build_chpx_pages(formatted_runs, start_page_num)
        curr_fc += len(chpx_pages)

        # Build PAPX pages
        start_page_num_papx = curr_fc // 512
        papx_pages, plcf_bte_papx = FkpBuilder.build_papx_pages(formatted_paras, start_page_num_papx)
        curr_fc += len(papx_pages)

        # 8. Numbering (LST / LFO)
        num_dict = data.get("numbering", {})
        plf_lst_bytes, plf_lfo_bytes = ListParser.build(num_dict)

        # 9. Assemble 1Table stream
        # Stream layout:
        # STSH -> PlcfSed -> PlcfHdd -> PlcfBteChpx -> PlcfBtePapx -> Clx -> PlfLst -> PlfLfo
        table_stream = bytearray()
        pointers: Dict[str, Tuple[int, int]] = {}

        def add_table_part(name: str, payload: bytes):
            if not payload:
                pointers[name] = (0, 0)
                return
            fc = len(table_stream)
            lcb = len(payload)
            table_stream.extend(payload)
            pointers[name] = (fc, lcb)

        add_table_part("Stshf", stsh_bytes)
        add_table_part("PlcfSed", plcf_sed_bytes)
        if plcf_hdd_bytes and ccp_hdd > 0:
            add_table_part("PlcfHdd", plcf_hdd_bytes)
        add_table_part("PlcfBteChpx", plcf_bte_chpx)
        add_table_part("PlcfBtePapx", plcf_bte_papx)
        add_table_part("Clx", clx_bytes)
        if plf_lst_bytes:
            add_table_part("PlfLst", plf_lst_bytes)
        if plf_lfo_bytes:
            add_table_part("PlfLfo", plf_lfo_bytes)

        # 10. Assemble FIB and WordDocument stream
        fib = Fib()
        fib.base.fWhichTblStm = True  # "1Table"
        fib.base.fcMin = start_fc
        fib.base.fcMac = start_fc + len(text_chunk)
        fib.rg_lw.ccpText = ccp_text
        fib.rg_lw.ccpFtn = ccp_ftn
        fib.rg_lw.ccpHdd = ccp_hdd

        for name, (fc, lcb) in pointers.items():
            fib.set_pointer(name, fc, lcb)

        fib_bytes = fib.to_bytes()

        word_doc_stream = (
            fib_bytes
            + text_chunk
            + sepx_bytes
            + fkp_padding
            + chpx_pages
            + papx_pages
        )

        # 11. Metadata Streams (\x05SummaryInformation & \x05DocumentSummaryInformation)
        meta = data.get("metadata", {})
        summary_info_bytes = PropertySetStream.build_summary_information(meta)
        doc_summary_bytes = PropertySetStream.build_document_summary_information(meta)

        # 12. Register all streams into CFBF
        self.write_stream("WordDocument", word_doc_stream)
        self.write_stream("1Table", bytes(table_stream))
        self.write_stream("\x05SummaryInformation", summary_info_bytes)
        if doc_summary_bytes:
            self.write_stream("\x05DocumentSummaryInformation", doc_summary_bytes)

        # Media stream (Data) if present
        media = data.get("media", {})
        if isinstance(media, dict) and media:
            data_stream = bytearray()
            for m_item in media.values():
                if isinstance(m_item, dict) and "bytes" in m_item:
                    b = m_item["bytes"]
                    if isinstance(b, str):
                        try:
                            b = base64.b64decode(b)
                        except Exception:
                            b = b.encode("latin1")
                    if isinstance(b, (bytes, bytearray)):
                        data_stream.extend(b)
                elif isinstance(m_item, str):
                    try:
                        data_stream.extend(base64.b64decode(m_item))
                    except Exception:
                        pass
                elif isinstance(m_item, (bytes, bytearray)):
                    data_stream.extend(m_item)
            if data_stream:
                self.write_stream("Data", bytes(data_stream))

    def _process_content(
        self,
        sections: List[Dict[str, Any]],
        style_map: Dict[str, int],
        start_fc: int = 1024,
        char_step: int = 1,
    ) -> Tuple[str, List[FormattedRun], List[FormattedParagraph]]:
        """Flatten sections into main text, runs, and paragraphs."""
        lines: List[str] = []
        runs_out: List[FormattedRun] = []
        paras_out: List[FormattedParagraph] = []

        curr_fc = start_fc

        for sec in sections:
            content = sec.get("content", [])
            for item in content:
                item_type = item.get("type", "paragraph")

                if item_type == "table":
                    rows = item.get("rows", [])
                    grpprl_cell = struct.pack("<HB", 0x2416, 1)
                    grpprl_row = struct.pack("<HBHB", 0x2416, 1, 0x2417, 1)

                    for row in rows:
                        if isinstance(row, dict):
                            cells = row.get("cells", [])
                        elif isinstance(row, list):
                            cells = row
                        else:
                            cells = []

                        for cell in cells:
                            if isinstance(cell, dict):
                                c_content = cell.get("content", [])
                            elif isinstance(cell, list):
                                c_content = cell
                            else:
                                c_content = [{"text": str(cell)}]

                            c_paras = []
                            for cp in c_content:
                                if isinstance(cp, dict):
                                    c_paras.append(cp.get("text", ""))
                                else:
                                    c_paras.append(str(cp))
                            cell_text = " ".join(c_paras) + "\x07"
                            c_fc_start = curr_fc
                            c_fc_end = curr_fc + len(cell_text) * char_step
                            lines.append(cell_text)
                            paras_out.append(
                                FormattedParagraph(
                                    fc_start=c_fc_start,
                                    fc_end=c_fc_end,
                                    istd=0,
                                    grpprl=grpprl_cell,
                                    props={"inTable": True},
                                )
                            )
                            runs_out.append(
                                FormattedRun(
                                    fc_start=c_fc_start,
                                    fc_end=c_fc_end,
                                    grpprl=b"",
                                    props={},
                                )
                            )
                            curr_fc = c_fc_end

                        # End of row mark
                        r_fc_start = curr_fc
                        r_fc_end = curr_fc + 1 * char_step
                        lines.append("\x07")
                        paras_out.append(
                            FormattedParagraph(
                                fc_start=r_fc_start,
                                fc_end=r_fc_end,
                                istd=0,
                                grpprl=grpprl_row,
                                props={"inTable": True, "tableTerminator": True},
                            )
                        )
                        runs_out.append(
                            FormattedRun(
                                fc_start=r_fc_start,
                                fc_end=r_fc_end,
                                grpprl=b"",
                                props={},
                            )
                        )
                        curr_fc = r_fc_end

                    # End of table line mark
                    lines.append("\r")
                    p_fc_start = curr_fc
                    p_fc_end = curr_fc + 1 * char_step
                    paras_out.append(
                        FormattedParagraph(
                            fc_start=p_fc_start,
                            fc_end=p_fc_end,
                            istd=0,
                            grpprl=b"",
                            props={},
                        )
                    )
                    runs_out.append(
                        FormattedRun(
                            fc_start=p_fc_start,
                            fc_end=p_fc_end,
                            grpprl=b"",
                            props={},
                        )
                    )
                    curr_fc = p_fc_end
                    continue

                # Paragraph or heading
                p_text = item.get("text", "")
                p_runs = item.get("runs", [])

                if not p_text and p_runs:
                    p_text = "".join(r.get("text", "") for r in p_runs)

                p_line = p_text + "\r"
                p_fc_start = curr_fc
                p_fc_end = curr_fc + len(p_line) * char_step

                # Paragraph formatting
                istd = 0
                p_style = item.get("style")
                if p_style and p_style in style_map:
                    istd = style_map[p_style]
                elif "styleIndex" in item and item["styleIndex"] is not None:
                    istd = int(item["styleIndex"])

                p_props = {}
                for k in ("align", "spacing", "indent", "numbering", "bullet"):
                    if k in item:
                        p_props[k] = item[k]
                if "level" in item and item.get("bullet"):
                    p_props.setdefault("numbering", {})["level"] = item["level"]

                p_grpprl = encode_paragraph_formatting(p_props, style_map)
                paras_out.append(
                    FormattedParagraph(
                        fc_start=p_fc_start,
                        fc_end=p_fc_end,
                        istd=istd,
                        grpprl=p_grpprl,
                        props=p_props,
                    )
                )

                # Character formatting for runs
                if p_runs:
                    run_curr_fc = p_fc_start
                    for r in p_runs:
                        r_text = r.get("text", "")
                        r_len = len(r_text)
                        if r_len == 0:
                            continue
                        r_fc_start = run_curr_fc
                        r_fc_end = run_curr_fc + r_len * char_step
                        r_grpprl = encode_character_formatting(r, style_table=style_map)
                        runs_out.append(
                            FormattedRun(
                                fc_start=r_fc_start,
                                fc_end=r_fc_end,
                                grpprl=r_grpprl,
                                props=r,
                            )
                        )
                        run_curr_fc = r_fc_end
                else:
                    # Inherit run props from flat paragraph properties if any
                    r_props = {}
                    for k in ("bold", "italic", "underline", "size", "font", "color"):
                        if k in item:
                            r_props[k] = item[k]
                    r_grpprl = encode_character_formatting(r_props)
                    runs_out.append(
                        FormattedRun(
                            fc_start=p_fc_start,
                            fc_end=p_fc_end,
                            grpprl=r_grpprl,
                            props=r_props,
                        )
                    )

                lines.append(p_line)
                curr_fc = p_fc_end

        main_text = "".join(lines)
        return main_text, runs_out, paras_out

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

