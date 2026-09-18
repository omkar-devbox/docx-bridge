"""Handler for font formatting (w:rFonts) and font definitions (w:fonts, word/fontTable.xml)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class FontHandler(BaseHandler):
    """Handles parsing and reconstructing font attributes and font table definitions."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a font element (w:rFonts or w:font) to JSON AST dictionary."""
        tag = local_name(element.tag)

        if tag == "rFonts":
            fonts: dict[str, Any] = {}
            for attr, key in [
                ("w:ascii", "ascii"),
                ("w:hAnsi", "hAnsi"),
                ("w:eastAsia", "eastAsia"),
                ("w:cs", "cs"),
                ("w:asciiTheme", "asciiTheme"),
                ("w:hAnsiTheme", "hAnsiTheme"),
                ("w:eastAsiaTheme", "eastAsiaTheme"),
                ("w:cstheme", "cstheme"),
            ]:
                val = element.attrib.get(qn(attr))
                if val is not None:
                    fonts[key] = val
            return fonts

        elif tag == "font":
            name = element.attrib.get(qn("w:name"), "")
            font_def: dict[str, Any] = {"name": name}
            for child in element:
                c_tag = local_name(child.tag)
                if c_tag == "pitch":
                    font_def["pitch"] = child.attrib.get(qn("w:val"))
                elif c_tag == "family":
                    font_def["family"] = child.attrib.get(qn("w:val"))
                elif c_tag == "charset":
                    font_def["charset"] = child.attrib.get(qn("w:val"))
                elif c_tag == "panose1":
                    font_def["panose1"] = child.attrib.get(qn("w:val"))
            return font_def

        return {}

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a w:rFonts element from a fonts dictionary or string."""
        el = ET.Element(qn("w:rFonts"))
        if isinstance(data, str):
            el.set(qn("w:ascii"), data)
            el.set(qn("w:hAnsi"), data)
            return el

        for key, attr in [
            ("ascii", "w:ascii"),
            ("hAnsi", "w:hAnsi"),
            ("eastAsia", "w:eastAsia"),
            ("cs", "w:cs"),
            ("asciiTheme", "w:asciiTheme"),
            ("hAnsiTheme", "w:hAnsiTheme"),
            ("eastAsiaTheme", "w:eastAsiaTheme"),
            ("cstheme", "w:cstheme"),
        ]:
            if key in data and data[key] is not None:
                el.set(qn(attr), str(data[key]))

        return el


__all__ = ["FontHandler"]
