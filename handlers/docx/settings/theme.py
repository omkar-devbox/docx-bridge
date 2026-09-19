"""Handler for Office Theme definitions (word/theme/theme1.xml, a:theme)."""

from typing import Any
import xml.etree.ElementTree as ET

from config import NAMESPACES
from handlers.docx.base import BaseHandler, qn, local_name


THEME_NS = NAMESPACES.get("a", "http://schemas.openxmlformats.org/drawingml/2006/main")


class ThemeHandler(BaseHandler):
    """Handles parsing and reconstructing word/theme/theme1.xml theme elements."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert an a:theme element to a JSON theme AST dictionary."""
        theme_name = element.attrib.get("name", "Office Theme")
        res: dict[str, Any] = {
            "type": "theme",
            "name": theme_name,
        }

        # Color scheme
        clr_scheme = element.find(f".//{{{THEME_NS}}}clrScheme")
        if clr_scheme is not None:
            colors: dict[str, str] = {}
            for child in clr_scheme:
                c_tag = local_name(child.tag)
                srgb = child.find(f"{{{THEME_NS}}}srgbClr")
                if srgb is not None:
                    colors[c_tag] = srgb.attrib.get("val", "")
                sys_clr = child.find(f"{{{THEME_NS}}}sysClr")
                if sys_clr is not None:
                    colors[c_tag] = sys_clr.attrib.get("lastClr", "")
            if colors:
                res["colorScheme"] = colors

        # Font scheme
        font_scheme = element.find(f".//{{{THEME_NS}}}fontScheme")
        if font_scheme is not None:
            fonts: dict[str, Any] = {}
            major = font_scheme.find(f"{{{THEME_NS}}}majorFont")
            if major is not None:
                latin = major.find(f"{{{THEME_NS}}}latin")
                if latin is not None:
                    fonts["majorLatin"] = latin.attrib.get("typeface", "")
            minor = font_scheme.find(f"{{{THEME_NS}}}minorFont")
            if minor is not None:
                latin = minor.find(f"{{{THEME_NS}}}latin")
                if latin is not None:
                    fonts["minorLatin"] = latin.attrib.get("typeface", "")
            if fonts:
                res["fontScheme"] = fonts

        return res

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct an a:theme element from a theme AST dictionary."""
        theme = ET.Element(f"{{{THEME_NS}}}theme", {"name": str(data.get("name", "Office Theme"))})
        elements = ET.SubElement(theme, f"{{{THEME_NS}}}themeElements")

        # Color Scheme
        clr_scheme = ET.SubElement(elements, f"{{{THEME_NS}}}clrScheme", {"name": "Office"})
        colors = data.get("colorScheme", {})
        for name, val in colors.items():
            slot = ET.SubElement(clr_scheme, f"{{{THEME_NS}}}{name}")
            ET.SubElement(slot, f"{{{THEME_NS}}}srgbClr", {"val": str(val)})

        # Font Scheme
        font_scheme = ET.SubElement(elements, f"{{{THEME_NS}}}fontScheme", {"name": "Office"})
        major = ET.SubElement(font_scheme, f"{{{THEME_NS}}}majorFont")
        ET.SubElement(major, f"{{{THEME_NS}}}latin", {"typeface": str(data.get("fontScheme", {}).get("majorLatin", "Calibri Light"))})
        minor = ET.SubElement(font_scheme, f"{{{THEME_NS}}}minorFont")
        ET.SubElement(minor, f"{{{THEME_NS}}}latin", {"typeface": str(data.get("fontScheme", {}).get("minorLatin", "Calibri"))})

        # Format Scheme
        ET.SubElement(elements, f"{{{THEME_NS}}}fmtScheme", {"name": "Office"})

        return theme


__all__ = ["ThemeHandler", "THEME_NS"]
