import base64
import struct
from typing import Any, Dict, List, Optional, Tuple

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
from formats.doc.writer import DocWriter


class JsonToBinaryParser:
    """Parser to convert unified JSON AST back into legacy Microsoft Word binary format."""

    def build_document(self, data: Dict[str, Any], writer: DocWriter) -> None:
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

        # Determine whether text needs UTF-16LE (2 bytes/char) or compressed (1 byte/char)
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

        # 4. Total text assembly
        ccp_text = len(main_text)
        ccp_ftn = 0
        ccp_hdd = len(hdd_text)
        full_doc_text = main_text + hdd_text

        # 5. Build Piece Table & character buffer
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

        # 7. FKP pages — align to 512-byte boundary
        pad_fkp = (512 - (curr_fc % 512)) % 512
        fkp_padding = b"\x00" * pad_fkp
        curr_fc += pad_fkp

        start_page_num = curr_fc // 512
        chpx_pages, plcf_bte_chpx = FkpBuilder.build_chpx_pages(formatted_runs, start_page_num)
        curr_fc += len(chpx_pages)

        start_page_num_papx = curr_fc // 512
        papx_pages, plcf_bte_papx = FkpBuilder.build_papx_pages(formatted_paras, start_page_num_papx)
        curr_fc += len(papx_pages)

        # 8. Numbering (LST / LFO)
        num_dict = data.get("numbering", {})
        plf_lst_bytes, plf_lfo_bytes = ListParser.build(num_dict)

        # 9. Assemble 1Table stream
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

        # 11. Metadata Streams
        meta = data.get("metadata", {})
        summary_info_bytes = PropertySetStream.build_summary_information(meta)
        doc_summary_bytes = PropertySetStream.build_document_summary_information(meta)

        # 12. Register all streams into CFBF via DocWriter
        writer.write_stream("WordDocument", word_doc_stream)
        writer.write_stream("1Table", bytes(table_stream))
        writer.write_stream("\x05SummaryInformation", summary_info_bytes)
        if doc_summary_bytes:
            writer.write_stream("\x05DocumentSummaryInformation", doc_summary_bytes)

        # 13. ObjectPool and Data stream (lossless verbatim preservation)
        obj_pool = data.get("objectPoolRaw", {})
        if isinstance(obj_pool, dict):
            for obj_name, obj_b64 in obj_pool.items():
                try:
                    writer.write_stream(obj_name, base64.b64decode(obj_b64))
                except Exception:
                    pass

        data_raw = data.get("dataStreamRaw", "")
        if data_raw:
            try:
                writer.write_stream("Data", base64.b64decode(data_raw))
            except Exception:
                pass
        else:
            # Fallback to naive media concatenation (lossy)
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
                    writer.write_stream("Data", bytes(data_stream))

    @staticmethod
    def _decode_papx_raw(papx_raw_b64: str) -> Optional[bytes]:
        """Decode a base64 PAPX raw field into GRPPRL bytes."""
        if not papx_raw_b64:
            return None
        try:
            return base64.b64decode(papx_raw_b64)
        except Exception:
            return None

    @staticmethod
    def _decode_chpx_raw(chpx_raw_b64: str) -> Optional[bytes]:
        """Decode a base64 CHPX raw field into GRPPRL bytes."""
        if not chpx_raw_b64:
            return None
        try:
            return base64.b64decode(chpx_raw_b64)
        except Exception:
            return None

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
                    self._process_table(item, style_map, char_step, lines, runs_out, paras_out, curr_fc)
                    # Recalculate curr_fc from the new runs
                    curr_fc = start_fc + sum(len(line.encode("windows-1252", errors="replace")) for line in lines) * char_step
                    # Add end-of-table marker paragraph
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

                # ---- Paragraph or heading ----
                p_text = item.get("text", "")
                p_runs = item.get("runs", [])

                if not p_text and p_runs:
                    p_text = "".join(r.get("text", "") for r in p_runs)

                p_line = p_text + "\r"
                p_fc_start = curr_fc
                p_fc_end = curr_fc + len(p_line) * char_step

                # Resolve istd
                istd = 0
                p_style = item.get("style")
                if p_style and p_style in style_map:
                    istd = style_map[p_style]
                elif "styleIndex" in item and item["styleIndex"] is not None:
                    istd = int(item["styleIndex"])

                # --- Paragraph GRPPRL (lossless priority) ---
                papx_raw = self._decode_papx_raw(item.get("papxRaw", ""))
                if papx_raw is not None:
                    # Lossless path: use stored raw bytes verbatim
                    p_grpprl = papx_raw
                else:
                    # Encoding path: prefer directParagraph (own props) over merged props
                    p_props = dict(item.get("directParagraph") or {})
                    if not p_props:
                        # Backward compat: use top-level props
                        for k in ("align", "spacing", "indent", "numbering", "bullet",
                                  "keepLines", "keepWithNext", "pageBreakBefore",
                                  "borders", "shading", "tabs", "outlineLevel",
                                  "inTable", "unknownSprms"):
                            if k in item:
                                p_props[k] = item[k]
                    p_grpprl = encode_paragraph_formatting(p_props, style_map)

                paras_out.append(
                    FormattedParagraph(
                        fc_start=p_fc_start,
                        fc_end=p_fc_end,
                        istd=istd,
                        grpprl=p_grpprl,
                        props=item.get("directParagraph", {}),
                    )
                )

                # --- Character formatting for runs ---
                if p_runs:
                    run_curr_fc = p_fc_start
                    for r in p_runs:
                        r_text = r.get("text", "")
                        r_len = len(r_text)
                        if r_len == 0:
                            continue
                        r_fc_start = run_curr_fc
                        r_fc_end = run_curr_fc + r_len * char_step

                        # Lossless path: use stored raw CHPX bytes
                        chpx_raw = self._decode_chpx_raw(r.get("chpxRaw", ""))
                        if chpx_raw is not None:
                            r_grpprl = chpx_raw
                        else:
                            # Prefer directRun (own props) over merged/effective props
                            r_props = dict(r.get("directRun") or {})
                            if not r_props:
                                # Backward compat: extract from top-level run keys
                                for k in ("bold", "italic", "underline", "size", "font",
                                          "fontIndex", "color", "highlight", "outline",
                                          "shadow", "smallCaps", "caps", "vanish",
                                          "strike", "styleIndex", "style",
                                          "language", "kerning", "unknownSprms"):
                                    if k in r:
                                        r_props[k] = r[k]
                            r_grpprl = encode_character_formatting(r_props, style_table=style_map)

                        runs_out.append(
                            FormattedRun(
                                fc_start=r_fc_start,
                                fc_end=r_fc_end,
                                grpprl=r_grpprl,
                                props=r.get("directRun", {}),
                            )
                        )
                        run_curr_fc = r_fc_end
                else:
                    # No explicit runs — inherit from flat paragraph properties
                    r_props: Dict[str, Any] = {}
                    for k in ("bold", "italic", "underline", "size", "font",
                              "fontIndex", "color", "highlight", "strike"):
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

    def _process_table(
        self,
        item: Dict[str, Any],
        style_map: Dict[str, int],
        char_step: int,
        lines: List[str],
        runs_out: List[FormattedRun],
        paras_out: List[FormattedParagraph],
        curr_fc: int,
    ) -> int:
        """Process a table item into cell paragraphs and row terminators."""
        rows = item.get("rows", [])
        grpprl_cell = struct.pack("<HB", 0x2416, 1)
        grpprl_row  = struct.pack("<HBHB", 0x2416, 1, 0x2417, 1)

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

                # Collect cell paragraphs and their text
                for cp in c_content:
                    if isinstance(cp, dict):
                        cp_text = cp.get("text", "")
                    else:
                        cp_text = str(cp)

                    cell_text = cp_text + "\x07"
                    c_fc_start = curr_fc
                    c_fc_end = curr_fc + len(cell_text) * char_step
                    lines.append(cell_text)

                    # Paragraph GRPPRL for cell
                    if isinstance(cp, dict) and cp.get("papxRaw"):
                        raw = self._decode_papx_raw(cp["papxRaw"])
                        cell_grpprl = raw if raw is not None else grpprl_cell
                    else:
                        cell_grpprl = grpprl_cell

                    paras_out.append(
                        FormattedParagraph(
                            fc_start=c_fc_start,
                            fc_end=c_fc_end,
                            istd=int(cp.get("styleIndex", 0)) if isinstance(cp, dict) else 0,
                            grpprl=cell_grpprl,
                            props={"inTable": True},
                        )
                    )

                    # Character GRPPRL for cell run
                    if isinstance(cp, dict):
                        cp_runs = cp.get("runs", [])
                        if cp_runs and cp_runs[0].get("chpxRaw"):
                            raw = self._decode_chpx_raw(cp_runs[0]["chpxRaw"])
                            cell_run_grpprl = raw if raw is not None else b""
                        else:
                            cell_run_grpprl = b""
                    else:
                        cell_run_grpprl = b""

                    runs_out.append(
                        FormattedRun(
                            fc_start=c_fc_start,
                            fc_end=c_fc_end,
                            grpprl=cell_run_grpprl,
                            props={},
                        )
                    )
                    curr_fc = c_fc_end

            # Row terminator
            r_fc_start = curr_fc
            r_fc_end = curr_fc + 1 * char_step
            lines.append("\x07")
            paras_out.append(
                FormattedParagraph(
                    fc_start=r_fc_start,
                    fc_end=r_fc_end,
                    istd=0,
                    grpprl=grpprl_row,
                    props={"inTable": True, "tableRowTerminator": True},
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

        return curr_fc
