"""Handler for DrawingML Charts (c:chart)."""

from typing import Any
import xml.etree.ElementTree as ET

from config import NAMESPACES
from handlers.docx.base import BaseHandler, qn, local_name


CHART_NS = NAMESPACES.get("c", "http://schemas.openxmlformats.org/drawingml/2006/chart")


class ChartsHandler(BaseHandler):
    """Handles parsing and reconstructing DrawingML chart references."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a chart element to JSON AST dictionary."""
        r_id = element.attrib.get(qn("r:id"), "")
        return {
            "type": "chart",
            "relationshipId": r_id,
        }

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a c:chart element from an AST dictionary."""
        el = ET.Element(f"{{{CHART_NS}}}chart")
        if "relationshipId" in data:
            el.set(qn("r:id"), str(data["relationshipId"]))
        return el


__all__ = ["ChartsHandler", "CHART_NS"]
