"""Handler for SmartArt diagrams (dgm:relIds, diagram data)."""

from typing import Any
import xml.etree.ElementTree as ET

from config import NAMESPACES
from handlers.docx.base import BaseHandler, qn, local_name


DGM_NS = NAMESPACES.get("dgm", "http://schemas.openxmlformats.org/drawingml/2006/diagram")


class SmartArtHandler(BaseHandler):
    """Handles parsing and reconstructing SmartArt diagram references."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a SmartArt diagram element to JSON AST dictionary."""
        dm_id = element.attrib.get(qn("r:dm"), "")
        lo_id = element.attrib.get(qn("r:lo"), "")
        qs_id = element.attrib.get(qn("r:qs"), "")
        cs_id = element.attrib.get(qn("r:cs"), "")

        return {
            "type": "smartArt",
            "dataModelRelId": dm_id,
            "layoutRelId": lo_id,
            "styleRelId": qs_id,
            "colorRelId": cs_id,
        }

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a dgm:relIds element from an AST dictionary."""
        el = ET.Element(f"{{{DGM_NS}}}relIds")
        if "dataModelRelId" in data:
            el.set(qn("r:dm"), str(data["dataModelRelId"]))
        if "layoutRelId" in data:
            el.set(qn("r:lo"), str(data["layoutRelId"]))
        if "styleRelId" in data:
            el.set(qn("r:qs"), str(data["styleRelId"]))
        if "colorRelId" in data:
            el.set(qn("r:cs"), str(data["colorRelId"]))
        return el


__all__ = ["SmartArtHandler", "DGM_NS"]
