"""Handler for list level formatting properties (w:start, w:numFmt, w:lvlText, w:lvlJc, w:suff)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class ListPropertiesHandler(BaseHandler):
    """Handles parsing and reconstructing numbering level properties."""

    def to_json(self, lvl: ET.Element) -> dict[str, Any]:
        """Convert a w:lvl element into a JSON list level properties dictionary."""
        props: dict[str, Any] = {}
        if lvl is None:
            return props

        ilvl = lvl.attrib.get(qn("w:ilvl"), "0")
        props["level"] = int(ilvl) if ilvl.isdigit() else ilvl

        # Start
        start = lvl.find(qn("w:start"))
        if start is not None:
            val = start.attrib.get(qn("w:val"), "1")
            props["start"] = int(val) if val.isdigit() else val

        # Number format (w:numFmt)
        num_fmt = lvl.find(qn("w:numFmt"))
        if num_fmt is not None:
            props["format"] = num_fmt.attrib.get(qn("w:val"), "decimal")

        # Level text (w:lvlText)
        lvl_text = lvl.find(qn("w:lvlText"))
        if lvl_text is not None:
            props["text"] = lvl_text.attrib.get(qn("w:val"), "")

        # Level justification / alignment (w:lvlJc)
        lvl_jc = lvl.find(qn("w:lvlJc"))
        if lvl_jc is not None:
            props["alignment"] = lvl_jc.attrib.get(qn("w:val"), "left")

        # Suffix (w:suff)
        suff = lvl.find(qn("w:suff"))
        if suff is not None:
            props["suffix"] = suff.attrib.get(qn("w:val"), "tab")

        # Restart level (w:lvlRestart)
        restart = lvl.find(qn("w:lvlRestart"))
        if restart is not None:
            val = restart.attrib.get(qn("w:val"))
            if val is not None:
                props["restart"] = int(val) if val.isdigit() else val

        return props

    def to_xml(self, data: dict[str, Any], ilvl: int = 0) -> ET.Element:
        """Construct a w:lvl element from level data dictionary."""
        lvl = ET.Element(qn("w:lvl"), {qn("w:ilvl"): str(data.get("level", ilvl))})

        # Start
        start_val = str(data.get("start", 1))
        ET.SubElement(lvl, qn("w:start"), {qn("w:val"): start_val})

        # Number format
        fmt_val = str(data.get("format", "decimal"))
        ET.SubElement(lvl, qn("w:numFmt"), {qn("w:val"): fmt_val})

        # Suffix
        if "suffix" in data:
            ET.SubElement(lvl, qn("w:suff"), {qn("w:val"): str(data["suffix"])})

        # Level text
        txt_val = str(data.get("text", f"%{int(ilvl) + 1}."))
        ET.SubElement(lvl, qn("w:lvlText"), {qn("w:val"): txt_val})

        # Level justification
        jc_val = str(data.get("alignment", "left"))
        ET.SubElement(lvl, qn("w:lvlJc"), {qn("w:val"): jc_val})

        # Restart
        if "restart" in data:
            ET.SubElement(lvl, qn("w:lvlRestart"), {qn("w:val"): str(data["restart"])})

        return lvl


__all__ = ["ListPropertiesHandler"]
