"""Handler for track changes and revisions (w:ins, w:del, w:rPrChange, w:pPrChange)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class RevisionsHandler(BaseHandler):
    """Handles parsing and reconstructing track changes / revision elements."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a revision element (w:ins, w:del, etc.) to JSON AST dictionary."""
        tag = local_name(element.tag)
        r_id = element.attrib.get(qn("w:id"), "")
        author = element.attrib.get(qn("w:author"), "")
        date_str = element.attrib.get(qn("w:date"), "")

        res: dict[str, Any] = {
            "type": tag,
            "id": int(r_id) if r_id.isdigit() else r_id,
            "author": author,
        }
        if date_str:
            res["date"] = date_str

        # Deleted text
        del_text = element.find(qn("w:delText"))
        if del_text is not None:
            res["text"] = del_text.text or ""

        return res

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a revision element from a revision AST dictionary."""
        r_type = data.get("type", "ins")
        el = ET.Element(qn(f"w:{r_type}"))

        if "id" in data:
            el.set(qn("w:id"), str(data["id"]))
        if "author" in data:
            el.set(qn("w:author"), str(data["author"]))
        if "date" in data:
            el.set(qn("w:date"), str(data["date"]))

        if "text" in data and r_type in ("del", "delete"):
            d_t = ET.SubElement(el, qn("w:delText"))
            d_t.text = str(data["text"])

        return el


__all__ = ["RevisionsHandler"]
