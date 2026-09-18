"""Handler for page geometry, size, orientation, columns, and grid (w:pgSz, w:cols, w:docGrid)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn
from config import PAGE_SIZES_DATA, DEFAULT_ORIENTATION


class PageHandler(BaseHandler):
    """Handles parsing and reconstructing page size, columns, and section layout settings."""

    def to_json(self, sect_pr: ET.Element) -> dict[str, Any]:
        """Convert page setup elements in w:sectPr to a JSON dictionary."""
        page_dict: dict[str, Any] = {}

        # Page Size (w:pgSz)
        pg_sz = sect_pr.find(qn("w:pgSz"))
        if pg_sz is not None:
            w_val = pg_sz.attrib.get(qn("w:w"))
            h_val = pg_sz.attrib.get(qn("w:h"))
            orient = pg_sz.attrib.get(qn("w:orient"), DEFAULT_ORIENTATION)
            sz_dict: dict[str, Any] = {
                "width": int(w_val) if w_val and w_val.isdigit() else w_val,
                "height": int(h_val) if h_val and h_val.isdigit() else h_val,
                "orientation": orient,
            }
            code = pg_sz.attrib.get(qn("w:code"))
            if code:
                sz_dict["code"] = int(code) if code.isdigit() else code
            page_dict["size"] = sz_dict

        # Columns (w:cols)
        cols = sect_pr.find(qn("w:cols"))
        if cols is not None:
            num = cols.attrib.get(qn("w:num"), "1")
            space = cols.attrib.get(qn("w:space"))
            c_dict: dict[str, Any] = {
                "count": int(num) if num.isdigit() else num,
            }
            if space:
                c_dict["space"] = int(space) if space.isdigit() else space
            page_dict["columns"] = c_dict

        # Doc Grid (w:docGrid)
        doc_grid = sect_pr.find(qn("w:docGrid"))
        if doc_grid is not None:
            g_type = doc_grid.attrib.get(qn("w:type"), "default")
            page_dict["grid"] = {"type": g_type}

        # Section Type (w:type)
        s_type = sect_pr.find(qn("w:type"))
        if s_type is not None:
            page_dict["sectionType"] = s_type.attrib.get(qn("w:val"), "nextPage")

        # Title Page (w:titlePg)
        title_pg = sect_pr.find(qn("w:titlePg"))
        if title_pg is not None:
            page_dict["titlePage"] = True

        # Page Number Type (w:pgNumType)
        pg_num = sect_pr.find(qn("w:pgNumType"))
        if pg_num is not None:
            pn_dict: dict[str, Any] = {}
            start = pg_num.attrib.get(qn("w:start"))
            if start:
                pn_dict["start"] = int(start) if start.isdigit() else start
            fmt = pg_num.attrib.get(qn("w:fmt"))
            if fmt:
                pn_dict["format"] = fmt
            page_dict["pageNumber"] = pn_dict

        return page_dict

    def append_page_elements(self, sect_pr: ET.Element, page_data: dict[str, Any]) -> None:
        """Append page geometry elements to w:sectPr."""
        # Section Type
        if "sectionType" in page_data:
            ET.SubElement(sect_pr, qn("w:type"), {qn("w:val"): str(page_data["sectionType"])})

        # Page Size
        sz_data = page_data.get("size", {})
        sz_attrib = {}
        if "width" in sz_data:
            sz_attrib[qn("w:w")] = str(sz_data["width"])
        elif "a4" in PAGE_SIZES_DATA:
            sz_attrib[qn("w:w")] = str(PAGE_SIZES_DATA["a4"]["width"])
        if "height" in sz_data:
            sz_attrib[qn("w:h")] = str(sz_data["height"])
        elif "a4" in PAGE_SIZES_DATA:
            sz_attrib[qn("w:h")] = str(PAGE_SIZES_DATA["a4"]["height"])
        if "orientation" in sz_data and sz_data["orientation"] != DEFAULT_ORIENTATION:
            sz_attrib[qn("w:orient")] = str(sz_data["orientation"])
        if sz_attrib:
            ET.SubElement(sect_pr, qn("w:pgSz"), sz_attrib)

        # Columns
        cols_data = page_data.get("columns", {})
        if cols_data:
            c_attrib = {qn("w:num"): str(cols_data.get("count", 1))}
            if "space" in cols_data:
                c_attrib[qn("w:space")] = str(cols_data["space"])
            ET.SubElement(sect_pr, qn("w:cols"), c_attrib)

        # Title Page
        if page_data.get("titlePage"):
            ET.SubElement(sect_pr, qn("w:titlePg"))

        # Doc Grid
        grid_data = page_data.get("grid", {})
        if grid_data:
            ET.SubElement(sect_pr, qn("w:docGrid"), {qn("w:type"): str(grid_data.get("type", "default"))})

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a w:sectPr element containing page geometry settings."""
        sect_pr = ET.Element(qn("w:sectPr"))
        self.append_page_elements(sect_pr, data)
        return sect_pr


__all__ = ["PageHandler"]
