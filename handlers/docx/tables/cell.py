"""Handler for table cells (w:tc, w:tcPr)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name, TCPR_ORDER, sort_children_by_schema
from handlers.docx.formatting.colors import ColorHandler


class TableCellHandler(BaseHandler):
    """Handles parsing and reconstructing w:tc and w:tcPr elements."""

    def __init__(self, paragraph_handler: Any = None):
        self.paragraph_handler = paragraph_handler
        self.color_handler = ColorHandler()

    def to_json(self, element: ET.Element, simple: bool = False) -> dict[str, Any]:
        """Convert a w:tc element to a JSON cell AST dictionary."""
        cell_dict: dict[str, Any] = {"type": "tableCell"}
        tc_pr = element.find(qn("w:tcPr"))

        if tc_pr is not None:
            props: dict[str, Any] = {}

            # Cell Width
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is not None:
                w_val = tc_w.attrib.get(qn("w:w"))
                props["width"] = {
                    "value": int(w_val) if w_val and w_val.isdigit() else w_val,
                    "type": tc_w.attrib.get(qn("w:type"), "dxa"),
                }

            # Grid Span
            grid_span = tc_pr.find(qn("w:gridSpan"))
            if grid_span is not None:
                val = grid_span.attrib.get(qn("w:val"))
                if val is not None:
                    props["gridSpan"] = int(val) if val.isdigit() else val

            # Vertical Merge
            v_merge = tc_pr.find(qn("w:vMerge"))
            if v_merge is not None:
                props["verticalMerge"] = v_merge.attrib.get(qn("w:val"), "continue")

            # Vertical Alignment
            v_align = tc_pr.find(qn("w:vAlign"))
            if v_align is not None:
                props["verticalAlign"] = v_align.attrib.get(qn("w:val"), "top")

            # Shading
            shd = tc_pr.find(qn("w:shd"))
            if shd is not None:
                props["shading"] = self.color_handler.to_json(shd)

            # Borders
            tc_borders = tc_pr.find(qn("w:tcBorders"))
            if tc_borders is not None:
                bdr_dict: dict[str, Any] = {}
                for side in ("top", "left", "bottom", "right"):
                    b_el = tc_borders.find(qn(f"w:{side}"))
                    if b_el is not None:
                        s_info: dict[str, Any] = {}
                        for attr, k in [("w:val", "val"), ("w:sz", "sz"), ("w:color", "color")]:
                            v = b_el.attrib.get(qn(attr))
                            if v is not None:
                                s_info[k] = int(v) if v.isdigit() else v
                        bdr_dict[side] = s_info
                if bdr_dict:
                    props["borders"] = bdr_dict

            if props:
                cell_dict["properties"] = props

        # Paragraphs / content inside cell
        paragraphs: list[dict[str, Any]] = []
        for child in element:
            c_tag = local_name(child.tag)
            if c_tag == "p" and self.paragraph_handler:
                p_data = self.paragraph_handler.to_json(child, simple=simple)
                if p_data:
                    paragraphs.append(p_data)
        if paragraphs:
            cell_dict["content"] = paragraphs

        return cell_dict

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a w:tc element from a JSON cell AST dictionary."""
        tc = ET.Element(qn("w:tc"))
        props = data.get("properties", {})

        if props:
            tc_pr = ET.SubElement(tc, qn("w:tcPr"))

            # Width
            w_info = props.get("width")
            if isinstance(w_info, dict):
                ET.SubElement(
                    tc_pr,
                    qn("w:tcW"),
                    {
                        qn("w:w"): str(w_info.get("value", 0)),
                        qn("w:type"): str(w_info.get("type", "dxa")),
                    },
                )

            # Grid Span
            if "gridSpan" in props and props["gridSpan"]:
                ET.SubElement(tc_pr, qn("w:gridSpan"), {qn("w:val"): str(props["gridSpan"])})

            # Vertical Merge
            if "verticalMerge" in props:
                val = str(props["verticalMerge"])
                if val == "continue":
                    ET.SubElement(tc_pr, qn("w:vMerge"))
                else:
                    ET.SubElement(tc_pr, qn("w:vMerge"), {qn("w:val"): val})

            # Vertical Alignment
            if "verticalAlign" in props:
                ET.SubElement(tc_pr, qn("w:vAlign"), {qn("w:val"): str(props["verticalAlign"])})

            # Shading
            shd = props.get("shading")
            if shd:
                s_el = self.color_handler.to_xml("shading", shd)
                if s_el is not None:
                    tc_pr.append(s_el)

            # Borders
            borders = props.get("borders")
            if isinstance(borders, dict):
                b_el = ET.SubElement(tc_pr, qn("w:tcBorders"))
                for side in ("top", "left", "bottom", "right"):
                    if side in borders and isinstance(borders[side], dict):
                        b_info = borders[side]
                        attrib = {qn("w:val"): str(b_info.get("val", "single"))}
                        for k, attr in [("sz", "w:sz"), ("color", "w:color")]:
                            if k in b_info:
                                attrib[qn(attr)] = str(b_info[k])
                        ET.SubElement(b_el, qn(f"w:{side}"), attrib)

            sort_children_by_schema(tc_pr, TCPR_ORDER)

        # Content paragraphs
        content = data.get("content", [])
        for block in content:
            if block.get("type") == "paragraph" and self.paragraph_handler:
                tc.append(self.paragraph_handler.to_xml(block))

        # Guarantee at least one empty paragraph in cell per OpenXML spec
        if not list(tc.findall(qn("w:p"))):
            p = ET.SubElement(tc, qn("w:p"))
            p_pr = ET.SubElement(p, qn("w:pPr"))

        return tc


__all__ = ["TableCellHandler"]
