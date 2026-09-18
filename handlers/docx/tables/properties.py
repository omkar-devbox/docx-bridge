"""Handler for table properties (w:tblPr, w:tblGrid)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name, TBLPR_ORDER, sort_children_by_schema
from handlers.docx.formatting.colors import ColorHandler


class TablePropertiesHandler(BaseHandler):
    """Handles parsing and reconstructing w:tblPr and w:tblGrid elements."""

    def __init__(self):
        self.color_handler = ColorHandler()

    def to_json(self, tbl_pr: ET.Element, tbl_grid: ET.Element | None = None) -> dict[str, Any]:
        """Convert w:tblPr and w:tblGrid elements into a JSON properties dictionary."""
        props: dict[str, Any] = {}
        if tbl_pr is not None:
            # Style
            style = tbl_pr.find(qn("w:tblStyle"))
            if style is not None:
                props["style"] = style.attrib.get(qn("w:val"), "")

            # Alignment
            jc = tbl_pr.find(qn("w:jc"))
            if jc is not None:
                props["alignment"] = jc.attrib.get(qn("w:val"), "left")

            # Table Width
            tbl_w = tbl_pr.find(qn("w:tblW"))
            if tbl_w is not None:
                w_val = tbl_w.attrib.get(qn("w:w"))
                w_type = tbl_w.attrib.get(qn("w:type"), "dxa")
                props["width"] = {
                    "value": int(w_val) if w_val and w_val.isdigit() else w_val,
                    "type": w_type,
                }

            # Table Borders
            tbl_borders = tbl_pr.find(qn("w:tblBorders"))
            if tbl_borders is not None:
                bdr_dict: dict[str, Any] = {}
                for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
                    b_el = tbl_borders.find(qn(f"w:{border_name}"))
                    if b_el is not None:
                        b_dict: dict[str, Any] = {}
                        for attr, key in [("w:val", "val"), ("w:sz", "sz"), ("w:space", "space"), ("w:color", "color")]:
                            val = b_el.attrib.get(qn(attr))
                            if val is not None:
                                b_dict[key] = int(val) if val.isdigit() else val
                        bdr_dict[border_name] = b_dict
                if bdr_dict:
                    props["borders"] = bdr_dict

            # Table Shading
            shd = tbl_pr.find(qn("w:shd"))
            if shd is not None:
                props["shading"] = self.color_handler.to_json(shd)

            # Table Cell Margins
            tbl_cell_mar = tbl_pr.find(qn("w:tblCellMar"))
            if tbl_cell_mar is not None:
                mar_dict: dict[str, Any] = {}
                for side in ("top", "left", "bottom", "right"):
                    m_el = tbl_cell_mar.find(qn(f"w:{side}"))
                    if m_el is not None:
                        val = m_el.attrib.get(qn("w:w"))
                        mar_dict[side] = int(val) if val and val.isdigit() else val
                if mar_dict:
                    props["cellMargins"] = mar_dict

        if tbl_grid is not None:
            cols = []
            for col in tbl_grid.findall(qn("w:gridCol")):
                w_val = col.attrib.get(qn("w:w"))
                cols.append(int(w_val) if w_val and w_val.isdigit() else w_val)
            if cols:
                props["grid"] = cols

        return props

    def to_xml(self, props: dict[str, Any]) -> ET.Element:
        """Construct w:tblPr element from JSON properties dictionary."""
        tbl_pr = ET.Element(qn("w:tblPr"))

        # Style
        if "style" in props and props["style"]:
            ET.SubElement(tbl_pr, qn("w:tblStyle"), {qn("w:val"): str(props["style"])})

        # Alignment
        if "alignment" in props and props["alignment"]:
            ET.SubElement(tbl_pr, qn("w:jc"), {qn("w:val"): str(props["alignment"])})

        # Width
        w_data = props.get("width")
        if isinstance(w_data, dict):
            ET.SubElement(
                tbl_pr,
                qn("w:tblW"),
                {
                    qn("w:w"): str(w_data.get("value", 0)),
                    qn("w:type"): str(w_data.get("type", "dxa")),
                },
            )

        # Borders
        borders = props.get("borders")
        if isinstance(borders, dict):
            bdr_el = ET.SubElement(tbl_pr, qn("w:tblBorders"))
            for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
                if border_name in borders and isinstance(borders[border_name], dict):
                    b_info = borders[border_name]
                    attrib = {qn("w:val"): str(b_info.get("val", "single"))}
                    for k, attr in [("sz", "w:sz"), ("space", "w:space"), ("color", "w:color")]:
                        if k in b_info:
                            attrib[qn(attr)] = str(b_info[k])
                    ET.SubElement(bdr_el, qn(f"w:{border_name}"), attrib)

        # Shading
        shd = props.get("shading")
        if shd:
            s_el = self.color_handler.to_xml("shading", shd)
            if s_el is not None:
                tbl_pr.append(s_el)

        # Cell Margins
        margins = props.get("cellMargins")
        if isinstance(margins, dict):
            mar_el = ET.SubElement(tbl_pr, qn("w:tblCellMar"))
            for side in ("top", "left", "bottom", "right"):
                if side in margins and margins[side] is not None:
                    ET.SubElement(
                        mar_el,
                        qn(f"w:{side}"),
                        {
                            qn("w:w"): str(margins[side]),
                            qn("w:type"): "dxa",
                        },
                    )

        sort_children_by_schema(tbl_pr, TBLPR_ORDER)
        return tbl_pr


__all__ = ["TablePropertiesHandler"]
