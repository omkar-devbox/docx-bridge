"""Handler for word/styles.xml."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name
from utils.xml import parse_xml_string


class StylesHandler(BaseHandler):
    """Handles word/styles.xml element conversion to/from JSON."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert styles XML root element to JSON dictionary."""
        result: dict[str, Any] = {}

        # Capture w:docDefaults if present
        doc_defaults = element.find(qn("w:docDefaults"))
        if doc_defaults is not None:
            result["docDefaultsXml"] = ET.tostring(doc_defaults, encoding="utf-8").decode("utf-8")

        # Capture w:latentStyles if present
        latent_styles = element.find(qn("w:latentStyles"))
        if latent_styles is not None:
            result["latentStylesXml"] = ET.tostring(latent_styles, encoding="utf-8").decode("utf-8")

        styles_list: list[dict[str, Any]] = []

        for style_elem in element.findall(qn("w:style")):
            style_id = style_elem.attrib.get(qn("w:styleId"), "")
            style_type = style_elem.attrib.get(qn("w:type"), "paragraph")
            default_val = style_elem.attrib.get(qn("w:default"))

            entry: dict[str, Any] = {
                "id": style_id,
                "type": style_type,
            }
            if default_val is not None:
                entry["default"] = default_val in ("1", "true")

            name_elem = style_elem.find(qn("w:name"))
            if name_elem is not None:
                entry["name"] = name_elem.attrib.get(qn("w:val"), "")

            based_on = style_elem.find(qn("w:basedOn"))
            if based_on is not None:
                entry["basedOn"] = based_on.attrib.get(qn("w:val"), "")

            next_style = style_elem.find(qn("w:next"))
            if next_style is not None:
                entry["next"] = next_style.attrib.get(qn("w:val"), "")

            link_style = style_elem.find(qn("w:link"))
            if link_style is not None:
                entry["link"] = link_style.attrib.get(qn("w:val"), "")

            if style_elem.find(qn("w:qFormat")) is not None:
                entry["primaryStyle"] = True

            if style_elem.find(qn("w:semiHidden")) is not None:
                entry["semiHidden"] = True

            if style_elem.find(qn("w:unhideWhenUsed")) is not None:
                entry["unhideWhenUsed"] = True

            ui_prio = style_elem.find(qn("w:uiPriority"))
            if ui_prio is not None:
                p_val = ui_prio.attrib.get(qn("w:val"), "")
                entry["uiPriority"] = int(p_val) if p_val.isdigit() else p_val

            # Preserve formatting child XML elements (rPr, pPr, tblPr, etc.)
            formatting_children = []
            for child in style_elem:
                c_tag = local_name(child.tag)
                if c_tag in ("rPr", "pPr", "tblPr", "tcPr", "trPr", "tblStylePr"):
                    formatting_children.append(ET.tostring(child, encoding="utf-8").decode("utf-8"))
            if formatting_children:
                entry["formattingXml"] = formatting_children

            styles_list.append(entry)

        result["styles"] = styles_list
        return result

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert styles JSON representation to w:styles XML element."""
        root = ET.Element(qn("w:styles"))

        # 1. Append docDefaults first if present (required by WordprocessingML schema)
        if isinstance(data, dict) and data.get("docDefaultsXml"):
            root.append(parse_xml_string(data["docDefaultsXml"]))

        # 2. Append latentStyles second if present
        if isinstance(data, dict) and data.get("latentStylesXml"):
            root.append(parse_xml_string(data["latentStylesXml"]))

        # 3. Append styles
        styles_data = data.get("styles", []) if isinstance(data, dict) else data
        for s in styles_data:
            attrs: dict[str, str] = {
                qn("w:type"): s.get("type", "paragraph"),
                qn("w:styleId"): s.get("id", ""),
            }
            if s.get("default"):
                attrs[qn("w:default")] = "1"

            style_elem = ET.SubElement(root, qn("w:style"), attrs)

            if s.get("name"):
                ET.SubElement(style_elem, qn("w:name"), {qn("w:val"): str(s["name"])})

            if s.get("basedOn"):
                ET.SubElement(style_elem, qn("w:basedOn"), {qn("w:val"): str(s["basedOn"])})

            if s.get("next"):
                ET.SubElement(style_elem, qn("w:next"), {qn("w:val"): str(s["next"])})

            if s.get("link"):
                ET.SubElement(style_elem, qn("w:link"), {qn("w:val"): str(s["link"])})

            if s.get("uiPriority") is not None:
                ET.SubElement(style_elem, qn("w:uiPriority"), {qn("w:val"): str(s["uiPriority"])})

            if s.get("semiHidden"):
                ET.SubElement(style_elem, qn("w:semiHidden"))

            if s.get("unhideWhenUsed"):
                ET.SubElement(style_elem, qn("w:unhideWhenUsed"))

            if s.get("primaryStyle"):
                ET.SubElement(style_elem, qn("w:qFormat"))

            if s.get("formattingXml"):
                for xml_str in s["formattingXml"]:
                    style_elem.append(parse_xml_string(xml_str))

        return root
