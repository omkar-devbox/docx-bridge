"""Handler for WordprocessingML bookmark elements (w:bookmarkStart, w:bookmarkEnd)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class BookmarksHandler(BaseHandler):
    """Handles parsing and reconstructing bookmark start and end elements."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a bookmark element to a JSON AST dictionary."""
        tag = local_name(element.tag)

        if tag == "bookmarkStart":
            bm_id = element.attrib.get(qn("w:id"), "")
            name = element.attrib.get(qn("w:name"), "")
            res: dict[str, Any] = {
                "type": "bookmarkStart",
                "id": bm_id,
                "name": name,
            }
            for attr in ("colFirst", "colLast"):
                val = element.attrib.get(qn(f"w:{attr}"))
                if val is not None:
                    res[attr] = int(val) if val.isdigit() else val
            return res

        elif tag == "bookmarkEnd":
            bm_id = element.attrib.get(qn("w:id"), "")
            return {
                "type": "bookmarkEnd",
                "id": bm_id,
            }

        return {"type": tag}

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct the XML element for a bookmark AST dictionary."""
        bm_type = data.get("type", "bookmarkStart")

        if bm_type == "bookmarkStart":
            el = ET.Element(qn("w:bookmarkStart"))
            if "id" in data:
                el.set(qn("w:id"), str(data["id"]))
            if "name" in data:
                el.set(qn("w:name"), str(data["name"]))
            for attr in ("colFirst", "colLast"):
                if attr in data:
                    el.set(qn(f"w:{attr}"), str(data[attr]))
            return el

        elif bm_type == "bookmarkEnd":
            el = ET.Element(qn("w:bookmarkEnd"))
            if "id" in data:
                el.set(qn("w:id"), str(data["id"]))
            return el

        return ET.Element(qn(f"w:{bm_type}"))


__all__ = ["BookmarksHandler"]
