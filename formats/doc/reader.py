"""Legacy Microsoft Word (.doc, Word 97-2003) binary reader.

Implements complete [MS-CFB] and [MS-DOC] reading:
- CFBF container stream extraction
- FIB, Piece Table, and text extraction across all subdocuments
- FKP CHPX (character runs) and PAPX (paragraphs) formatting
- STSH styles, LST/LFO numbering, SED/SEP sections, and headers/footers
- OLE Property Set metadata and OfficeArt media extraction
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from formats.doc.cfbf import CFBReader
from formats.doc.fib import Fib
from formats.doc.fkp import FkpParser, FormattedParagraph, FormattedRun
from formats.doc.piece_table import PieceTable
from formats.doc.structures import (
    EscherParser,
    HeaderFooterTable,
    ListParser,
    PropertySetStream,
    SectionTable,
    StshParser,
)


class DocReader:
    """Reader for legacy Microsoft Word (.doc, Word 97-2003) binary files."""

    def __init__(self, source: Union[str, Path, BinaryIO, bytes]):
        self.source = source
        self.cfb = CFBReader(source)
        self.fib: Optional[Fib] = None
        self.piece_table: Optional[PieceTable] = None
        self.word_doc_bytes: bytes = b""
        self.table_bytes: bytes = b""
        self._parsed_data: Optional[Dict[str, Any]] = None

        self._load_core()

    def _load_core(self) -> None:
        """Load and parse core Word streams."""
        if not self.cfb.has_stream("WordDocument"):
            raise ValueError("Invalid DOC file: 'WordDocument' stream is missing.")

        self.word_doc_bytes = self.cfb.read_stream("WordDocument")
        self.fib = Fib.parse(self.word_doc_bytes)

        table_stream_name = self.fib.base.table_stream_name
        if self.cfb.has_stream(table_stream_name):
            self.table_bytes = self.cfb.read_stream(table_stream_name)
        elif self.cfb.has_stream("0Table"):
            self.table_bytes = self.cfb.read_stream("0Table")
        elif self.cfb.has_stream("1Table"):
            self.table_bytes = self.cfb.read_stream("1Table")

        # Load Piece Table from Clx
        clx_fc, clx_lcb = self.fib.get_pointer("Clx")
        if clx_fc >= 0 and clx_lcb > 0 and clx_fc + clx_lcb <= len(self.table_bytes):
            clx_bytes = self.table_bytes[clx_fc : clx_fc + clx_lcb]
            self.piece_table = PieceTable.parse_clx(clx_bytes)

        if not self.piece_table or not self.piece_table.pieces:
            for fc, lcb in self.fib.raw_pairs:
                if lcb > 0 and fc + lcb <= len(self.table_bytes):
                    candidate = self.table_bytes[fc : fc + lcb]
                    if len(candidate) > 4 and candidate[0] in (0x01, 0x02):
                        pt = PieceTable.parse_clx(candidate)
                        if pt.pieces:
                            self.piece_table = pt
                            break

        if not self.piece_table or not self.piece_table.pieces:
            # Fallback: simple text between fcMin and fcMac
            fcMin = self.fib.base.fcMin
            fcMac = min(self.fib.base.fcMac, len(self.word_doc_bytes))
            if fcMac > fcMin:
                raw_text = self.word_doc_bytes[fcMin:fcMac].decode("windows-1252", errors="replace")
                _, _, self.piece_table = PieceTable.build_from_text(raw_text, start_fc=fcMin)

    # --------------------------------
    # Stream Operations
    # --------------------------------

    def read_stream(self, stream_name: str) -> bytes:
        """Read a named stream from the compound document."""
        return self.cfb.read_stream(stream_name)

    def list_streams(self) -> List[str]:
        """List all stream names."""
        return self.cfb.list_streams()

    # --------------------------------
    # High-level Document AST Extraction
    # --------------------------------

    def parse_document(self) -> Dict[str, Any]:
        """Parse the binary DOC file into unified JSON AST structure."""
        if self._parsed_data is not None:
            return self._parsed_data

        data: Dict[str, Any] = {}

        # 1. Stylesheet (STSH)
        stsh_fc, stsh_lcb = self.fib.get_pointer("Stshf")
        if stsh_fc >= 0 and stsh_lcb > 0 and stsh_fc + stsh_lcb <= len(self.table_bytes):
            stsh_bytes = self.table_bytes[stsh_fc : stsh_fc + stsh_lcb]
            stsh_res = StshParser.parse(stsh_bytes)
            if stsh_res.get("styles"):
                data["styles"] = stsh_res["styles"]

        # 2. Numbering (LST & LFO)
        lst_fc, lst_lcb = self.fib.get_pointer("PlfLst")
        lfo_fc, lfo_lcb = self.fib.get_pointer("PlfLfo")
        lst_bytes = self.table_bytes[lst_fc : lst_fc + lst_lcb] if lst_fc > 0 and lst_lcb > 0 else b""
        lfo_bytes = self.table_bytes[lfo_fc : lfo_fc + lfo_lcb] if lfo_fc > 0 and lfo_lcb > 0 else b""
        if lst_bytes or lfo_bytes:
            data["numbering"] = ListParser.parse(lst_bytes, lfo_bytes)

        # 3. Text Extraction across subdocuments
        ccp_text = self.fib.rg_lw.ccpText
        if ccp_text == 0 and self.piece_table:
            ccp_text = self.piece_table.get_total_cps()

        main_text = ""
        if self.piece_table:
            main_text = self.piece_table.get_text(self.word_doc_bytes, start_cp=0, end_cp=ccp_text)

        # 4. Paragraph & Run Formatting
        # Read FKPs
        chpx_fc, chpx_lcb = self.fib.get_pointer("PlcfBteChpx")
        papx_fc, papx_lcb = self.fib.get_pointer("PlcfBtePapx")

        runs: List[FormattedRun] = []
        if chpx_fc > 0 and chpx_lcb > 0 and chpx_fc + chpx_lcb <= len(self.table_bytes):
            runs = FkpParser.parse_plcf_bte_chpx(
                self.table_bytes[chpx_fc : chpx_fc + chpx_lcb],
                self.word_doc_bytes,
            )

        paras: List[FormattedParagraph] = []
        if papx_fc > 0 and papx_lcb > 0 and papx_fc + papx_lcb <= len(self.table_bytes):
            paras = FkpParser.parse_plcf_bte_papx(
                self.table_bytes[papx_fc : papx_fc + papx_lcb],
                self.word_doc_bytes,
            )

        # Split text into paragraphs by \r or \n
        content_items = self._build_content(main_text, runs, paras, styles=data.get("styles", {}))

        # 5. Sections
        sed_fc, sed_lcb = self.fib.get_pointer("PlcfSed")
        sections_list: List[Dict[str, Any]] = []
        if sed_fc > 0 and sed_lcb > 0 and sed_fc + sed_lcb <= len(self.table_bytes):
            sections_list = SectionTable.parse(
                self.table_bytes[sed_fc : sed_fc + sed_lcb],
                self.word_doc_bytes,
            )

        if not sections_list:
            sections_list = [
                {
                    "page": {
                        "size": "letter",
                        "orientation": "portrait",
                        "margins": {
                            "top": 1440,
                            "bottom": 1440,
                            "left": 1440,
                            "right": 1440,
                        },
                    }
                }
            ]

        # Attach content to first section (matching unified AST)
        sections_list[0]["content"] = content_items
        data["sections"] = sections_list

        # 6. Headers & Footers
        ccp_ftn = self.fib.rg_lw.ccpFtn
        ccp_hdd = self.fib.rg_lw.ccpHdd
        hdd_start_cp = ccp_text + ccp_ftn
        hdd_end_cp = hdd_start_cp + ccp_hdd

        if ccp_hdd > 0 and self.piece_table:
            hdd_text = self.piece_table.get_text(self.word_doc_bytes, start_cp=hdd_start_cp, end_cp=hdd_end_cp)
            hdd_fc, hdd_lcb = self.fib.get_pointer("PlcfHdd")
            if hdd_fc > 0 and hdd_lcb > 0 and hdd_fc + hdd_lcb <= len(self.table_bytes):
                hf_data = HeaderFooterTable.parse(
                    self.table_bytes[hdd_fc : hdd_fc + hdd_lcb],
                    hdd_text,
                )
                if hf_data.get("headers"):
                    data["headers"] = hf_data["headers"]
                if hf_data.get("footers"):
                    data["footers"] = hf_data["footers"]

        # 7. Metadata (SummaryInformation)
        if self.cfb.has_stream("\x05SummaryInformation"):
            summary_bytes = self.cfb.read_stream("\x05SummaryInformation")
            meta = PropertySetStream.parse(summary_bytes)
            if self.cfb.has_stream("\x05DocumentSummaryInformation"):
                doc_summary_bytes = self.cfb.read_stream("\x05DocumentSummaryInformation")
                doc_meta = PropertySetStream.parse(doc_summary_bytes)
                meta.update(doc_meta)
            if meta:
                data["metadata"] = meta

        # 8. Media / Images
        images: List[Dict[str, Any]] = []
        if self.cfb.has_stream("Data"):
            data_bytes = self.cfb.read_stream("Data")
            images.extend(EscherParser.extract_blips(data_bytes))

        # Also search WordDocument stream for BLIPs
        dgg_fc, dgg_lcb = self.fib.get_pointer("DggInfo")
        if dgg_fc > 0 and dgg_lcb > 0 and dgg_fc + dgg_lcb <= len(self.table_bytes):
            images.extend(EscherParser.extract_blips(self.table_bytes[dgg_fc : dgg_fc + dgg_lcb]))

        if images:
            media_dict = {}
            for img in images:
                img_data = img["data"]
                b64_str = (
                    base64.b64encode(img_data).decode("ascii")
                    if isinstance(img_data, (bytes, bytearray))
                    else str(img_data)
                )
                media_dict[img["name"]] = {
                    "bytes": b64_str,
                    "contentType": f"image/{img['type']}",
                }
            data["media"] = media_dict

        self._parsed_data = data
        return data

    def _build_content(
        self,
        text: str,
        runs: List[FormattedRun],
        paras: List[FormattedParagraph],
        styles: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Assemble main text paragraphs and runs with exact style matching."""
        lines = text.split("\r")
        content: List[Dict[str, Any]] = []

        curr_cp = 0
        para_idx = 0

        # Build istd -> style name mapping
        istd_to_style: Dict[int, str] = {}
        if isinstance(styles, dict):
            for s_name, s_item in styles.items():
                if isinstance(s_item, dict) and "istd" in s_item:
                    istd_to_style[s_item["istd"]] = s_name

        for line_idx, raw_line in enumerate(lines):
            if not raw_line and line_idx == len(lines) - 1:
                # Trailing empty line at end of document
                break

            line_len = len(raw_line)
            p_end_cp = curr_cp + line_len

            # Find matching paragraph formatting
            p_props: Dict[str, Any] = {}
            fc_info = self.piece_table.cp_to_fc(curr_cp) if self.piece_table else None
            p_fc = fc_info[0] if fc_info else None

            matching_p = None
            if p_fc is not None and paras:
                for idx_p, p in enumerate(paras):
                    if p.fc_start <= p_fc < p.fc_end:
                        matching_p = p
                        para_idx = idx_p + 1
                        break
            if matching_p is None and para_idx < len(paras):
                matching_p = paras[para_idx]
                para_idx += 1

            if matching_p is not None:
                p_props = dict(matching_p.props)

            # Determine exact style name
            style_name = "Normal"
            istd = p_props.get("styleIndex")
            if istd is None and matching_p is not None:
                istd = getattr(matching_p, "istd", None)
            if istd is not None and istd in istd_to_style:
                style_name = istd_to_style[istd]
            elif "style" in p_props and p_props["style"]:
                style_name = p_props["style"]

            # Table detection: char \x07 is cell end in Word DOC
            if "\x07" in raw_line:
                if "\x07\x07" in raw_line:
                    raw_rows = [r for r in raw_line.split("\x07\x07") if r.strip("\x07")]
                else:
                    raw_rows = [raw_line]

                extracted_rows = []
                for r_str in raw_rows:
                    cells_raw = [c for c in r_str.split("\x07") if c]
                    if cells_raw:
                        row_cells = []
                        for c_text in cells_raw:
                            cell_para = {
                                "type": "paragraph",
                                "style": style_name,
                                "text": c_text,
                                "runs": [{"type": "run", "text": c_text}],
                            }
                            if istd is not None:
                                cell_para["styleIndex"] = istd
                            row_cells.append({
                                "content": [cell_para]
                            })
                        if row_cells:
                            extracted_rows.append({"cells": row_cells})

                if extracted_rows:
                    if content and content[-1].get("type") == "table":
                        content[-1]["rows"].extend(extracted_rows)
                    else:
                        content.append({
                            "type": "table",
                            "properties": {},
                            "rows": extracted_rows,
                        })
                curr_cp = p_end_cp + 1
                continue

            # Standard paragraph
            p_dict: Dict[str, Any] = {
                "type": "paragraph",
                "style": style_name,
                "text": raw_line,
            }
            if istd is not None:
                p_dict["styleIndex"] = istd

            # Copy paragraph formatting
            for k in ("align", "spacing", "indent", "numbering", "bullet"):
                if k in p_props:
                    p_dict[k] = p_props[k]

            # Build runs for this paragraph
            p_runs: List[Dict[str, Any]] = []
            if runs and p_fc is not None and line_len > 0:
                is_comp = fc_info[1] if fc_info else True
                step = 1 if is_comp else 2
                p_fc_end = p_fc + (line_len * step)

                sub_runs = [r for r in runs if max(r.fc_start, p_fc) < min(r.fc_end, p_fc_end)]
                if sub_runs:
                    raw_segments: List[Tuple[str, Dict[str, Any]]] = []
                    for r in sub_runs:
                        s_fc = max(r.fc_start, p_fc)
                        e_fc = min(r.fc_end, p_fc_end)
                        c_start = max(0, (s_fc - p_fc) // step)
                        c_end = min(line_len, (e_fc - p_fc) // step)
                        seg_text = raw_line[c_start:c_end]
                        if seg_text:
                            r_props = dict(r.props)
                            if "styleIndex" in r_props and r_props["styleIndex"] in istd_to_style:
                                r_props["style"] = istd_to_style[r_props["styleIndex"]]
                            raw_segments.append((seg_text, r_props))

                    # Merge consecutive runs with identical props
                    merged_runs: List[Dict[str, Any]] = []
                    for seg_text, seg_props in raw_segments:
                        if merged_runs and merged_runs[-1]["props"] == seg_props:
                            merged_runs[-1]["text"] += seg_text
                        else:
                            merged_runs.append({"text": seg_text, "props": seg_props})

                    for m in merged_runs:
                        r_dict = {"type": "run", "text": m["text"]}
                        r_dict.update(m["props"])
                        p_runs.append(r_dict)

            if not p_runs:
                p_runs.append({"type": "run", "text": raw_line})

            p_dict["runs"] = p_runs
            content.append(p_dict)
            curr_cp = p_end_cp + 1

        return content

    # --------------------------------
    # Archive Lifecycle
    # --------------------------------

    def close(self) -> None:
        self.cfb.close()

    def __enter__(self) -> DocReader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


__all__ = ["DocReader"]
