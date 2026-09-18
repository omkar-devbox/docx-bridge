"""Handler for WordprocessingML compatibility settings (w:compat, w:compatSetting)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class CompatibilityHandler(BaseHandler):
    """Handles parsing and reconstructing w:compat elements."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a w:compat element to a JSON dictionary."""
        compat: dict[str, Any] = {}

        for child in element:
            tag = local_name(child.tag)
            if tag == "compatSetting":
                name = child.attrib.get(qn("w:name"), "")
                val = child.attrib.get(qn("w:val"), "")
                if name:
                    compat[name] = val
            else:
                val = child.attrib.get(qn("w:val"), "1")
                compat[tag] = val not in ("0", "false", "off")

        return compat

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a w:compat element from compatibility settings."""
        el = ET.Element(qn("w:compat"))

        for key, val in data.items():
            if isinstance(val, (int, str)):
                ET.SubElement(
                    el,
                    qn("w:compatSetting"),
                    {
                        qn("w:name"): str(key),
                        qn("w:uri"): "http://schemas.microsoft.com/office/word",
                        qn("w:val"): str(val),
                    },
                )
            elif val:
                ET.SubElement(el, qn(f"w:{key}"))

        return el


__all__ = ["CompatibilityHandler"]
