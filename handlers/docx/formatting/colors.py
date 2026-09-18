"""Handler for color formatting elements (w:color, w:highlight, w:shd, w15:color)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name
from handlers.common.helpers import bgr_to_hex, hex_to_bgr, normalize_hex_color


class ColorHandler(BaseHandler):
    """Handles parsing and reconstructing color, highlight, and shading properties."""

    @staticmethod
    def normalize_color(color_val: str | None) -> str | None:
        """Normalize color to canonical hex string or keep 'auto'."""
        if not color_val:
            return None
        return normalize_hex_color(color_val)

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a color/shading element to JSON AST dictionary."""
        tag = local_name(element.tag)
        res: dict[str, Any] = {}

        if tag in ("color", "extendedColor"):
            val = element.attrib.get(qn("w:val")) or element.attrib.get(qn("w15:val"))
            if val:
                res["color"] = self.normalize_color(val)
            theme_color = element.attrib.get(qn("w:themeColor"))
            if theme_color:
                res["themeColor"] = theme_color
            theme_tint = element.attrib.get(qn("w:themeTint"))
            if theme_tint:
                res["themeTint"] = theme_tint
            theme_shade = element.attrib.get(qn("w:themeShade"))
            if theme_shade:
                res["themeShade"] = theme_shade

        elif tag == "highlight":
            val = element.attrib.get(qn("w:val"))
            if val:
                res["highlight"] = val

        elif tag == "shd":
            val = element.attrib.get(qn("w:val"), "clear")
            res["val"] = val
            color = element.attrib.get(qn("w:color"))
            if color:
                res["color"] = self.normalize_color(color)
            fill = element.attrib.get(qn("w:fill"))
            if fill:
                res["fill"] = self.normalize_color(fill)
            theme_fill = element.attrib.get(qn("w:themeFill"))
            if theme_fill:
                res["themeFill"] = theme_fill

        return res

    def to_xml(self, prop_or_data: Any, value: Any = None) -> ET.Element | None:
        """Construct the XML element for a given color property or dictionary."""
        if value is not None:
            prop_name = prop_or_data
        elif isinstance(prop_or_data, dict):
            if "color" in prop_or_data:
                prop_name = "color"
                value = prop_or_data.get("color")
            elif "highlight" in prop_or_data:
                prop_name = "highlight"
                value = prop_or_data.get("highlight")
            elif "shading" in prop_or_data or "fill" in prop_or_data:
                prop_name = "shading"
                value = prop_or_data.get("shading", prop_or_data)
            else:
                prop_name = "color"
                value = prop_or_data
        else:
            prop_name = "color"
            value = prop_or_data

        if not value:
            return ET.Element(qn("w:color"), {qn("w:val"): "auto"})

        if prop_name == "color":
            el = ET.Element(qn("w:color"))
            if isinstance(value, dict):
                el.set(qn("w:val"), str(value.get("val", value.get("color", "auto"))))
                if "themeColor" in value:
                    el.set(qn("w:themeColor"), str(value["themeColor"]))
                if "themeTint" in value:
                    el.set(qn("w:themeTint"), str(value["themeTint"]))
                if "themeShade" in value:
                    el.set(qn("w:themeShade"), str(value["themeShade"]))
            else:
                el.set(qn("w:val"), str(value))
            return el

        elif prop_name == "highlight":
            el = ET.Element(qn("w:highlight"))
            el.set(qn("w:val"), str(value))
            return el

        elif prop_name in ("shading", "shd"):
            el = ET.Element(qn("w:shd"))
            if isinstance(value, dict):
                el.set(qn("w:val"), str(value.get("val", "clear")))
                if "color" in value:
                    el.set(qn("w:color"), str(value["color"]))
                if "fill" in value:
                    el.set(qn("w:fill"), str(value["fill"]))
                if "themeFill" in value:
                    el.set(qn("w:themeFill"), str(value["themeFill"]))
            else:
                el.set(qn("w:val"), "clear")
                el.set(qn("w:fill"), str(value))
            return el

        return None


__all__ = [
    "ColorHandler",
    "bgr_to_hex",
    "hex_to_bgr",
    "normalize_hex_color",
]
