"""Handler for Office Open XML Math elements (m:oMath, m:oMathPara)."""

from typing import Any
import xml.etree.ElementTree as ET

from config import NAMESPACES
from handlers.docx.base import BaseHandler, qn, local_name


MATH_NS = NAMESPACES.get("m", "http://schemas.openxmlformats.org/officeDocument/2006/math")


class MathHandler(BaseHandler):
    """Handles parsing and reconstructing Office Math (OMML) equations."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert an m:oMath or m:oMathPara element to JSON AST dictionary."""
        tag = local_name(element.tag)
        texts: list[str] = []
        for t_el in element.findall(f".//{{{MATH_NS}}}t"):
            if t_el.text:
                texts.append(t_el.text)

        return {
            "type": "mathParagraph" if tag == "oMathPara" else "mathBlock",
            "text": "".join(texts),
            "xml": ET.tostring(element, encoding="unicode"),
        }

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct an m:oMath or m:oMathPara element from an AST dictionary."""
        xml_str = data.get("xml")
        if xml_str:
            try:
                return ET.fromstring(xml_str)
            except Exception:
                pass

        m_type = data.get("type", "mathBlock")
        tag = f"{{{MATH_NS}}}oMathPara" if m_type == "mathParagraph" else f"{{{MATH_NS}}}oMath"
        el = ET.Element(tag)

        # Basic text run
        text = data.get("text", "")
        if text:
            r = ET.SubElement(el, f"{{{MATH_NS}}}r")
            t = ET.SubElement(r, f"{{{MATH_NS}}}t")
            t.text = str(text)

        return el


__all__ = ["MathHandler", "MATH_NS"]
