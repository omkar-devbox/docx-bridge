"""Handler for run formatting properties (w:rPr)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name, RPR_ORDER, sort_children_by_schema
from handlers.docx.formatting.colors import ColorHandler
from handlers.docx.formatting.fonts import FontHandler


class RunPropertiesHandler(BaseHandler):
    """Handles parsing and reconstructing w:rPr run properties."""

    def __init__(self):
        self.color_handler = ColorHandler()
        self.font_handler = FontHandler()

    def to_json(self, r_pr: ET.Element) -> dict[str, Any]:
        """Convert w:rPr element to JSON properties dictionary."""
        props: dict[str, Any] = {}
        if r_pr is None:
            return props

        # Character Style
        r_style = r_pr.find(qn("w:rStyle"))
        if r_style is not None:
            props["style"] = r_style.attrib.get(qn("w:val"), "")

        # Fonts
        r_fonts = r_pr.find(qn("w:rFonts"))
        if r_fonts is not None:
            props["fonts"] = self.font_handler.to_json(r_fonts)

        # Booleans
        for xml_tag, key in [
            ("b", "bold"),
            ("bCs", "boldCs"),
            ("i", "italic"),
            ("iCs", "italicCs"),
            ("caps", "caps"),
            ("smallCaps", "smallCaps"),
            ("strike", "strike"),
            ("dstrike", "doubleStrike"),
            ("outline", "outline"),
            ("shadow", "shadow"),
            ("emboss", "emboss"),
            ("imprint", "imprint"),
            ("noProof", "noProof"),
            ("vanish", "vanish"),
            ("rtl", "rtl"),
            ("cs", "complexScript"),
        ]:
            el = r_pr.find(qn(f"w:{xml_tag}"))
            if el is not None:
                val = el.attrib.get(qn("w:val"), "1")
                props[key] = val not in ("0", "false", "off")

        # Underline
        u = r_pr.find(qn("w:u"))
        if u is not None:
            val = u.attrib.get(qn("w:val"), "single")
            props["underline"] = val
            u_color = u.attrib.get(qn("w:color"))
            if u_color:
                props["underlineColor"] = u_color

        # Color
        color = r_pr.find(qn("w:color"))
        if color is not None:
            c_dict = self.color_handler.to_json(color)
            if "color" in c_dict:
                props["color"] = c_dict["color"]
            for k in ("themeColor", "themeTint", "themeShade"):
                if k in c_dict:
                    props[k] = c_dict[k]

        # Highlight
        highlight = r_pr.find(qn("w:highlight"))
        if highlight is not None:
            h_dict = self.color_handler.to_json(highlight)
            if "highlight" in h_dict:
                props["highlight"] = h_dict["highlight"]

        # Shading
        shd = r_pr.find(qn("w:shd"))
        if shd is not None:
            props["shading"] = self.color_handler.to_json(shd)

        # Font Sizes (half-points)
        for xml_tag, key in [("sz", "size"), ("szCs", "sizeCs")]:
            el = r_pr.find(qn(f"w:{xml_tag}"))
            if el is not None:
                val = el.attrib.get(qn("w:val"))
                if val is not None:
                    props[key] = int(val) if val.isdigit() else val

        # Vertical Alignment
        va = r_pr.find(qn("w:vertAlign"))
        if va is not None:
            props["verticalAlign"] = va.attrib.get(qn("w:val"), "")

        # Spacing / Position / Kerning
        for xml_tag, key in [("spacing", "spacing"), ("position", "position"), ("kern", "kerning"), ("w", "scaling")]:
            el = r_pr.find(qn(f"w:{xml_tag}"))
            if el is not None:
                val = el.attrib.get(qn("w:val"))
                if val is not None:
                    props[key] = int(val) if val.isdigit() else val

        return props

    def to_xml(self, props: dict[str, Any]) -> ET.Element:
        """Construct w:rPr element from JSON properties dictionary."""
        r_pr = ET.Element(qn("w:rPr"))

        # Style
        if "style" in props and props["style"]:
            ET.SubElement(r_pr, qn("w:rStyle"), {qn("w:val"): str(props["style"])})

        # Fonts
        if "fonts" in props and props["fonts"]:
            r_pr.append(self.font_handler.to_xml(props["fonts"]))

        # Booleans
        for key, xml_tag in [
            ("bold", "b"),
            ("boldCs", "bCs"),
            ("italic", "i"),
            ("italicCs", "iCs"),
            ("caps", "caps"),
            ("smallCaps", "smallCaps"),
            ("strike", "strike"),
            ("doubleStrike", "dstrike"),
            ("outline", "outline"),
            ("shadow", "shadow"),
            ("emboss", "emboss"),
            ("imprint", "imprint"),
            ("noProof", "noProof"),
            ("vanish", "vanish"),
            ("rtl", "rtl"),
            ("complexScript", "cs"),
        ]:
            if props.get(key):
                ET.SubElement(r_pr, qn(f"w:{xml_tag}"))

        # Underline
        if "underline" in props and props["underline"]:
            attrib = {qn("w:val"): str(props["underline"])}
            if "underlineColor" in props:
                attrib[qn("w:color")] = str(props["underlineColor"])
            ET.SubElement(r_pr, qn("w:u"), attrib)

        # Color
        if "color" in props and props["color"]:
            c_el = self.color_handler.to_xml("color", props["color"])
            if c_el is not None:
                r_pr.append(c_el)

        # Highlight
        if "highlight" in props and props["highlight"]:
            h_el = self.color_handler.to_xml("highlight", props["highlight"])
            if h_el is not None:
                r_pr.append(h_el)

        # Shading
        if "shading" in props and props["shading"]:
            s_el = self.color_handler.to_xml("shading", props["shading"])
            if s_el is not None:
                r_pr.append(s_el)

        # Size
        for key, xml_tag in [("size", "sz"), ("sizeCs", "szCs")]:
            if key in props and props[key] is not None:
                ET.SubElement(r_pr, qn(f"w:{xml_tag}"), {qn("w:val"): str(props[key])})

        # Vertical Alignment
        if "verticalAlign" in props and props["verticalAlign"]:
            ET.SubElement(r_pr, qn("w:vertAlign"), {qn("w:val"): str(props["verticalAlign"])})

        # Position / Spacing / Kerning / Scaling
        for key, xml_tag in [("spacing", "spacing"), ("position", "position"), ("kerning", "kern"), ("scaling", "w")]:
            if key in props and props[key] is not None:
                ET.SubElement(r_pr, qn(f"w:{xml_tag}"), {qn("w:val"): str(props[key])})

        sort_children_by_schema(r_pr, RPR_ORDER)
        return r_pr


__all__ = ["RunPropertiesHandler"]
