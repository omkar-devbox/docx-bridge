import base64
from typing import Any, Dict, List, Optional

from formats.doc.fkp import FkpParser, FormattedParagraph, FormattedRun
from formats.doc.structures import (
    EscherParser,
    HeaderFooterTable,
    ListParser,
    PropertySetStream,
    SectionTable,
    StshParser,
)
from formats.doc.reader import DocReader


class BinaryToJsonParser:
    """Parser to convert legacy Microsoft Word binary format into unified JSON AST."""

    def __init__(self, reader: DocReader):
        self.reader = reader

    def parse_document(self) -> Dict[str, Any]:
        """Parse the binary DOC file into unified JSON AST structure."""
        if self.reader._parsed_data is not None:
            return self.reader._parsed_data

        data: Dict[str, Any] = {}

        # 1. Stylesheet (STSH)
        stsh_fc, stsh_lcb = self.reader.fib.get_pointer("Stshf")
        if stsh_fc >= 0 and stsh_lcb > 0 and stsh_fc + stsh_lcb <= len(self.reader.table_bytes):
            stsh_bytes = self.reader.table_bytes[stsh_fc : stsh_fc + stsh_lcb]
            stsh_res = StshParser.parse(stsh_bytes)
            if stsh_res.get("styles"):
                data["styles"] = stsh_res["styles"]

        # 2. Numbering (LST & LFO)
        lst_fc, lst_lcb = self.reader.fib.get_pointer("PlfLst")
        lfo_fc, lfo_lcb = self.reader.fib.get_pointer("PlfLfo")
        lst_bytes = self.reader.table_bytes[lst_fc : lst_fc + lst_lcb] if lst_fc > 0 and lst_lcb > 0 else b""
        lfo_bytes = self.reader.table_bytes[lfo_fc : lfo_fc + lfo_lcb] if lfo_fc > 0 and lfo_lcb > 0 else b""
        if lst_bytes or lfo_bytes:
            data["numbering"] = ListParser.parse(lst_bytes, lfo_bytes)

        # 3. Text Extraction across subdocuments
        ccp_text = self.reader.fib.rg_lw.ccpText
        if ccp_text == 0 and self.reader.piece_table:
            ccp_text = self.reader.piece_table.get_total_cps()

        main_text = ""
        if self.reader.piece_table:
            main_text = self.reader.piece_table.get_text(self.reader.word_doc_bytes, start_cp=0, end_cp=ccp_text)

        # 4. Paragraph & Run Formatting — read FKPs
        chpx_fc, chpx_lcb = self.reader.fib.get_pointer("PlcfBteChpx")
        papx_fc, papx_lcb = self.reader.fib.get_pointer("PlcfBtePapx")

        runs: List[FormattedRun] = []
        if chpx_fc > 0 and chpx_lcb > 0 and chpx_fc + chpx_lcb <= len(self.reader.table_bytes):
            runs = FkpParser.parse_plcf_bte_chpx(
                self.reader.table_bytes[chpx_fc : chpx_fc + chpx_lcb],
                self.reader.word_doc_bytes,
            )

        paras: List[FormattedParagraph] = []
        if papx_fc > 0 and papx_lcb > 0 and papx_fc + papx_lcb <= len(self.reader.table_bytes):
            paras = FkpParser.parse_plcf_bte_papx(
                self.reader.table_bytes[papx_fc : papx_fc + papx_lcb],
                self.reader.word_doc_bytes,
            )

        # 5. Assemble content items
        content_items = self._build_content(main_text, runs, paras, styles=data.get("styles", {}))

        # 6. Sections
        sed_fc, sed_lcb = self.reader.fib.get_pointer("PlcfSed")
        sections_list: List[Dict[str, Any]] = []
        if sed_fc > 0 and sed_lcb > 0 and sed_fc + sed_lcb <= len(self.reader.table_bytes):
            sections_list = SectionTable.parse(
                self.reader.table_bytes[sed_fc : sed_fc + sed_lcb],
                self.reader.word_doc_bytes,
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

        sections_list[0]["content"] = content_items
        data["sections"] = sections_list

        # 7. Headers & Footers
        ccp_ftn = self.reader.fib.rg_lw.ccpFtn
        ccp_hdd = self.reader.fib.rg_lw.ccpHdd
        hdd_start_cp = ccp_text + ccp_ftn
        hdd_end_cp = hdd_start_cp + ccp_hdd

        if ccp_hdd > 0 and self.reader.piece_table:
            hdd_text = self.reader.piece_table.get_text(self.reader.word_doc_bytes, start_cp=hdd_start_cp, end_cp=hdd_end_cp)
            hdd_fc, hdd_lcb = self.reader.fib.get_pointer("PlcfHdd")
            if hdd_fc > 0 and hdd_lcb > 0 and hdd_fc + hdd_lcb <= len(self.reader.table_bytes):
                hf_data = HeaderFooterTable.parse(
                    self.reader.table_bytes[hdd_fc : hdd_fc + hdd_lcb],
                    hdd_text,
                )
                if hf_data.get("headers"):
                    data["headers"] = hf_data["headers"]
                if hf_data.get("footers"):
                    data["footers"] = hf_data["footers"]

        # 8. Metadata (SummaryInformation)
        if self.reader.cfb.has_stream("\x05SummaryInformation"):
            summary_bytes = self.reader.cfb.read_stream("\x05SummaryInformation")
            meta = PropertySetStream.parse(summary_bytes)
            if self.reader.cfb.has_stream("\x05DocumentSummaryInformation"):
                doc_summary_bytes = self.reader.cfb.read_stream("\x05DocumentSummaryInformation")
                doc_meta = PropertySetStream.parse(doc_summary_bytes)
                meta.update(doc_meta)
            if meta:
                data["metadata"] = meta

        # 9. Media / Images
        images: List[Dict[str, Any]] = []
        
        # Lossless Data stream preservation
        if self.reader.cfb.has_stream("Data"):
            data_bytes = self.reader.cfb.read_stream("Data")
            data["dataStreamRaw"] = base64.b64encode(data_bytes).decode("ascii")
            images.extend(EscherParser.extract_blips(data_bytes))

        # Lossless ObjectPool preservation
        obj_pool_streams = {}
        for stream_name in self.reader.cfb.list_streams():
            if stream_name.startswith("ObjectPool/"):
                obj_pool_streams[stream_name] = base64.b64encode(self.reader.cfb.read_stream(stream_name)).decode("ascii")
        if obj_pool_streams:
            data["objectPoolRaw"] = obj_pool_streams

        dgg_fc, dgg_lcb = self.reader.fib.get_pointer("DggInfo")
        if dgg_fc > 0 and dgg_lcb > 0 and dgg_fc + dgg_lcb <= len(self.reader.table_bytes):
            images.extend(EscherParser.extract_blips(self.reader.table_bytes[dgg_fc : dgg_fc + dgg_lcb]))

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

        self.reader._parsed_data = data
        return data

    def _build_content(
        self,
        text: str,
        runs: List[FormattedRun],
        paras: List[FormattedParagraph],
        styles: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Assemble main text paragraphs and runs with lossless formatting fields."""
        lines = text.split("\r")
        content: List[Dict[str, Any]] = []

        curr_cp = 0
        para_idx = 0

        # Build istd -> style entry mapping
        istd_to_style: Dict[int, str] = {}
        istd_to_entry: Dict[int, Dict[str, Any]] = {}
        if isinstance(styles, dict):
            for s_name, s_item in styles.items():
                if isinstance(s_item, dict) and "istd" in s_item:
                    idx = s_item["istd"]
                    istd_to_style[idx] = s_name
                    istd_to_entry[idx] = s_item

        def _style_props(istd: Optional[int], key: str) -> Dict[str, Any]:
            """Return resolved (effective) props for key from style entry."""
            if istd is None:
                return {}
            entry = istd_to_entry.get(istd)
            if not entry:
                return {}
            # Prefer 'effective' sub-key (fully resolved chain) when available
            effective = entry.get("effective", {})
            if effective and key in effective:
                return dict(effective[key])
            return dict(entry.get(key) or {})

        for line_idx, raw_line in enumerate(lines):
            if not raw_line and line_idx == len(lines) - 1:
                break

            line_len = len(raw_line)
            p_end_cp = curr_cp + line_len

            # Find matching paragraph FormattedParagraph by FC
            fc_info = self.reader.piece_table.cp_to_fc(curr_cp) if self.reader.piece_table else None
            p_fc = fc_info[0] if fc_info else None

            matching_p: Optional[FormattedParagraph] = None
            if p_fc is not None and paras:
                for idx_p, p in enumerate(paras):
                    if p.fc_start <= p_fc < p.fc_end:
                        matching_p = p
                        para_idx = idx_p + 1
                        break
            if matching_p is None and para_idx < len(paras):
                matching_p = paras[para_idx]
                para_idx += 1

            # Direct paragraph props from PAPX (own, not merged)
            direct_p_props: Dict[str, Any] = {}
            papx_raw_b64: str = ""
            istd: Optional[int] = None

            if matching_p is not None:
                direct_p_props = dict(matching_p.props)
                if matching_p.grpprl:
                    papx_raw_b64 = base64.b64encode(matching_p.grpprl).decode("ascii")
                istd = matching_p.istd if matching_p.istd != 0 else direct_p_props.get("styleIndex")

            # Determine style name
            style_name = "Normal"
            if istd is not None and istd in istd_to_style:
                style_name = istd_to_style[istd]
            elif "style" in direct_p_props and direct_p_props["style"]:
                style_name = direct_p_props["style"]

            # ---- Table detection ----
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
                            cell_para: Dict[str, Any] = {
                                "type": "paragraph",
                                "style": style_name,
                                "text": c_text,
                            }
                            if istd is not None:
                                cell_para["styleIndex"] = istd
                            if papx_raw_b64:
                                cell_para["papxRaw"] = papx_raw_b64
                            if direct_p_props:
                                cell_para["directParagraph"] = {
                                    k: v for k, v in direct_p_props.items()
                                    if k not in ("styleIndex", "style")
                                }
                            # Minimal run for cell text
                            cell_run: Dict[str, Any] = {"type": "run", "text": c_text}
                            cell_para["runs"] = [cell_run]
                            row_cells.append({"content": [cell_para]})

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

            # ---- Standard paragraph ----
            # Build effective paragraph props: style chain + direct PAPX overrides
            effective_p: Dict[str, Any] = {}
            style_p = _style_props(istd, "paragraph")
            effective_p.update(style_p)
            # Direct PAPX props override style props
            for k, v in direct_p_props.items():
                if k not in ("styleIndex", "style"):
                    effective_p[k] = v

            p_dict: Dict[str, Any] = {
                "type": "paragraph",
                "style": style_name,
                "text": raw_line,
            }
            if istd is not None:
                p_dict["styleIndex"] = istd

            # Store lossless raw bytes
            if papx_raw_b64:
                p_dict["papxRaw"] = papx_raw_b64

            # Store direct (own) paragraph props for faithful reconstruction
            if direct_p_props:
                p_dict["directParagraph"] = {
                    k: v for k, v in direct_p_props.items()
                    if k not in ("styleIndex", "style")
                }

            # Copy effective paragraph formatting for rendering/display
            for k in ("align", "spacing", "indent", "numbering", "bullet",
                      "keepLines", "keepWithNext", "pageBreakBefore",
                      "borders", "shading", "tabs", "outlineLevel",
                      "inTable", "unknownSprms"):
                if k in effective_p:
                    p_dict[k] = effective_p[k]

            # ---- Build runs for this paragraph ----
            p_runs: List[Dict[str, Any]] = []
            if runs and p_fc is not None and line_len > 0:
                is_comp = fc_info[1] if fc_info else True
                step = 1 if is_comp else 2
                p_fc_end = p_fc + (line_len * step)

                sub_runs = [r for r in runs if max(r.fc_start, p_fc) < min(r.fc_end, p_fc_end)]
                if sub_runs:
                    for r in sub_runs:
                        s_fc = max(r.fc_start, p_fc)
                        e_fc = min(r.fc_end, p_fc_end)
                        c_start = max(0, (s_fc - p_fc) // step)
                        c_end = min(line_len, (e_fc - p_fc) // step)
                        seg_text = raw_line[c_start:c_end]
                        if not seg_text:
                            continue

                        # Direct (own) run props — no style merge
                        direct_r: Dict[str, Any] = {}
                        chpx_raw_b64 = ""
                        for k, v in r.props.items():
                            if k not in ("styleIndex", "style"):
                                direct_r[k] = v
                        if r.grpprl:
                            chpx_raw_b64 = base64.b64encode(r.grpprl).decode("ascii")

                        # Build effective run props for display
                        effective_r: Dict[str, Any] = _style_props(istd, "run")
                        char_istd = r.props.get("styleIndex")
                        if char_istd is not None and char_istd != istd:
                            c_style_run = _style_props(char_istd, "run")
                            effective_r.update(c_style_run)
                        effective_r.update(direct_r)

                        # Resolve char style name if present
                        if char_istd is not None and char_istd in istd_to_style:
                            effective_r["style"] = istd_to_style[char_istd]

                        r_dict: Dict[str, Any] = {"type": "run", "text": seg_text}
                        # Lossless raw bytes
                        if chpx_raw_b64:
                            r_dict["chpxRaw"] = chpx_raw_b64
                        # Direct (own) props for reconstruction
                        if direct_r:
                            r_dict["directRun"] = direct_r
                        # Style reference
                        if char_istd is not None:
                            r_dict["styleIndex"] = char_istd
                        # Effective props for rendering
                        r_dict.update({
                            k: v for k, v in effective_r.items()
                            if k not in ("styleIndex",)
                        })
                        p_runs.append(r_dict)

            if not p_runs:
                p_runs.append({"type": "run", "text": raw_line})

            p_dict["runs"] = p_runs
            content.append(p_dict)
            curr_cp = p_end_cp + 1

        return content
