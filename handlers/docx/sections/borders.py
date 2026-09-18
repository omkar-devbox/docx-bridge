"""Handler for page borders (w:pgBorders)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class PageBordersHandler(BaseHandler):
    """Handles parsing and reconstructing w:pgBorders page border elements."""

    def to_json(self, pg_borders: ET.Element) -> dict[str, Any]:
        """Convert w:pgBorders element to JSON page borders dictionary."""
        borders: dict[str, Any] = {}
        if pg_borders is None:
            return borders

        for side in ("top", "left", "bottom", "right"):
            b_el = pg_borders.find(qn(f"w:{side}"))
            if b_el is not None:
                b_info: dict[str, Any] = {}
                for attr, key in [
                    ("w:val", "val"),
                    ("w:sz", "sz"),
                    ("w:space", "space"),
                    ("w:color", "color"),
                ]:
                    val = b_el.attrib.get(qn(attr))
                    if val is not None:
                        b_info[key] = int(val) if val.isdigit() else val
                borders[side] = b_info

        return borders

    def to_xml(self, borders: dict[str, Any]) -> ET.Element:
        """Construct w:pgBorders element from borders dictionary."""
        pg_borders = ET.Element(qn("w:pgBorders"))

        for side in ("top", "left", "bottom", "right"):
            if side in borders and isinstance(borders[side], dict):
                b_info = borders[side]
                attrib = {qn("w:val"): str(b_info.get("val", "single"))}
                for k, attr in [("sz", "w:sz"), ("space", "w:space"), ("color", "w:color")]:
                    if k in b_info:
                        attrib[qn(attr)] = str(b_info[k])
                ET.SubElement(pg_borders, qn(f"w:{side}"), attrib)

        return pg_borders


__all__ = ["PageBordersHandler"]
