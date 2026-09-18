"""Handler for abstract numbering definitions (w:abstractNum)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name
from handlers.docx.lists.list_properties import ListPropertiesHandler


class AbstractNumberingHandler(BaseHandler):
    """Handles parsing and reconstructing w:abstractNum elements."""

    def __init__(self, list_properties_handler: ListPropertiesHandler | None = None):
        self.list_properties_handler = list_properties_handler or ListPropertiesHandler()

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a w:abstractNum element to a JSON AST dictionary."""
        abs_id = element.attrib.get(qn("w:abstractNumId"), "0")
        res: dict[str, Any] = {
            "abstractNumId": int(abs_id) if abs_id.isdigit() else abs_id,
            "levels": [],
        }

        # MultiLevelType
        mlt = element.find(qn("w:multiLevelType"))
        if mlt is not None:
            res["multiLevelType"] = mlt.attrib.get(qn("w:val"), "multilevel")

        # NumStyleLink
        nsl = element.find(qn("w:numStyleLink"))
        if nsl is not None:
            res["numStyleLink"] = nsl.attrib.get(qn("w:val"), "")

        # Levels
        for lvl in element.findall(qn("w:lvl")):
            lvl_data = self.list_properties_handler.to_json(lvl)
            if lvl_data:
                res["levels"].append(lvl_data)

        return res

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a w:abstractNum element from an AST dictionary."""
        abs_id = str(data.get("abstractNumId", 0))
        el = ET.Element(qn("w:abstractNum"), {qn("w:abstractNumId"): abs_id})

        # MultiLevelType
        mlt_val = str(data.get("multiLevelType", "hybridMultilevel"))
        ET.SubElement(el, qn("w:multiLevelType"), {qn("w:val"): mlt_val})

        # NumStyleLink
        if "numStyleLink" in data and data["numStyleLink"]:
            ET.SubElement(el, qn("w:numStyleLink"), {qn("w:val"): str(data["numStyleLink"])})

        # Levels
        levels = data.get("levels", [])
        for i, lvl_data in enumerate(levels):
            el.append(self.list_properties_handler.to_xml(lvl_data, ilvl=i))

        return el


__all__ = ["AbstractNumberingHandler"]
