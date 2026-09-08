"""Handler for w:sectPr (section properties) elements."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name


class SectionsHandler(BaseHandler):
    """Handles w:sectPr section properties conversion to/from JSON."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert w:sectPr element to JSON dictionary with master-tags values as keys."""
        type_name = self.tag_to_name("w:sectPr")  # "sectionProperties"
        result: dict[str, Any] = {
            "type": type_name,
        }

        # Page Size (w:pgSz -> pageSize)
        pg_sz = element.find(qn("w:pgSz"))
        if pg_sz is not None:
            w_val = pg_sz.attrib.get(qn("w:w"), "")
            h_val = pg_sz.attrib.get(qn("w:h"), "")
            size_dict = {
                "width": int(w_val) if w_val.isdigit() else w_val,
                "height": int(h_val) if h_val.isdigit() else h_val,
                "orientation": pg_sz.attrib.get(qn("w:orient"), "portrait"),
            }
            result[self.tag_to_name("w:pgSz")] = size_dict

        # Margins (w:pgMar -> pageMargins)
        pg_mar = element.find(qn("w:pgMar"))
        if pg_mar is not None:
            margins: dict[str, Any] = {}
            for attr, key in [
                ("w:top", "top"),
                ("w:right", "right"),
                ("w:bottom", "bottom"),
                ("w:left", "left"),
                ("w:header", "header"),
                ("w:footer", "footer"),
                ("w:gutter", "gutter"),
            ]:
                val = pg_mar.attrib.get(qn(attr))
                if val is not None:
                    margins[key] = int(val) if val.isdigit() else val
            result[self.tag_to_name("w:pgMar")] = margins
            result["margins"] = margins

        # Columns (w:cols -> columns)
        cols = element.find(qn("w:cols"))
        if cols is not None:
            cols_dict: dict[str, Any] = {}
            for k, v in cols.attrib.items():
                cols_dict[local_name(k)] = int(v) if v.isdigit() or (v.startswith("-") and v[1:].isdigit()) else v
            col_list: list[dict[str, Any]] = []
            for c_el in cols.findall(qn("w:col")):
                c_dict = {local_name(k): (int(v) if v.isdigit() else v) for k, v in c_el.attrib.items()}
                col_list.append(c_dict)
            if col_list:
                cols_dict["columns"] = col_list
            result[self.tag_to_name("w:cols")] = cols_dict
            result["columns"] = cols_dict

        # Section Type (w:type -> sectionType)
        sec_type = element.find(qn("w:type"))
        if sec_type is not None:
            result[self.tag_to_name("w:type")] = sec_type.attrib.get(qn("w:val"), "")

        # Headers & Footers
        headers: list[dict[str, str]] = []
        for hdr in element.findall(qn("w:headerReference")):
            headers.append({
                "type": hdr.attrib.get(qn("w:type"), "default"),
                "relationshipId": hdr.attrib.get(qn("r:id"), ""),
            })
        if headers:
            result[self.tag_to_name("w:headerReference")] = headers
            result["headers"] = headers

        footers: list[dict[str, str]] = []
        for ftr in element.findall(qn("w:footerReference")):
            footers.append({
                "type": ftr.attrib.get(qn("w:type"), "default"),
                "relationshipId": ftr.attrib.get(qn("r:id"), ""),
            })
        if footers:
            result[self.tag_to_name("w:footerReference")] = footers
            result["footers"] = footers

        return result

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert JSON section properties representation to w:sectPr XML element."""
        sect_pr = ET.Element(qn("w:sectPr"))

        # Headers
        header_list = data.get("headerReference") or data.get("headers", [])
        for hdr in header_list:
            attrs = {qn("w:type"): hdr.get("type", "default")}
            if hdr.get("relationshipId"):
                attrs[qn("r:id")] = hdr["relationshipId"]
            ET.SubElement(sect_pr, qn("w:headerReference"), attrs)

        # Footers
        footer_list = data.get("footerReference") or data.get("footers", [])
        for ftr in footer_list:
            attrs = {qn("w:type"): ftr.get("type", "default")}
            if ftr.get("relationshipId"):
                attrs[qn("r:id")] = ftr["relationshipId"]
            ET.SubElement(sect_pr, qn("w:footerReference"), attrs)

        # Section Type
        sec_type_val = data.get("sectionType") or data.get("type")
        if sec_type_val and sec_type_val not in ("section", "sectionProperties"):
            ET.SubElement(sect_pr, qn("w:type"), {qn("w:val"): str(sec_type_val)})

        # Page Size
        sz = data.get("pageSize")
        if sz:
            sz_attrs: dict[str, str] = {}
            if "width" in sz:
                sz_attrs[qn("w:w")] = str(sz["width"])
            if "height" in sz:
                sz_attrs[qn("w:h")] = str(sz["height"])
            if sz.get("orientation") and sz["orientation"] != "portrait":
                sz_attrs[qn("w:orient")] = str(sz["orientation"])
            ET.SubElement(sect_pr, qn("w:pgSz"), sz_attrs)

        # Margins
        mar = data.get("pageMargins") or data.get("margins")
        if mar:
            mar_attrs: dict[str, str] = {}
            for key, attr in [
                ("top", "w:top"),
                ("right", "w:right"),
                ("bottom", "w:bottom"),
                ("left", "w:left"),
                ("header", "w:header"),
                ("footer", "w:footer"),
                ("gutter", "w:gutter"),
            ]:
                if key in mar:
                    mar_attrs[qn(attr)] = str(mar[key])
            ET.SubElement(sect_pr, qn("w:pgMar"), mar_attrs)

        # Columns
        cols = data.get("columns") or data.get(self.tag_to_name("w:cols"))
        if cols:
            cols_attrs: dict[str, str] = {}
            for k, v in cols.items():
                if k != "columns":
                    cols_attrs[qn(f"w:{k}")] = str(v)
            cols_el = ET.SubElement(sect_pr, qn("w:cols"), cols_attrs)
            for c_info in cols.get("columns", []):
                c_attrs = {qn(f"w:{k}"): str(v) for k, v in c_info.items()}
                ET.SubElement(cols_el, qn("w:col"), c_attrs)

        return sect_pr
