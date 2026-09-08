"""Handler for w:r (run) elements."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name


class RunHandler(BaseHandler):
    """Handles w:r run element conversion to/from JSON."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert w:r element to JSON dictionary with master-tags values as keys."""
        run_properties: dict[str, Any] = {}
        r_pr = element if element.tag == qn("w:rPr") else element.find(qn("w:rPr"))

        if r_pr is not None:
            # Bold (w:b -> bold)
            b = r_pr.find(qn("w:b"))
            if b is not None:
                val = b.attrib.get(qn("w:val"), "true")
                run_properties[self.tag_to_name("w:b")] = val not in ("0", "false")

            # Complex Script Bold (w:bCs)
            b_cs = r_pr.find(qn("w:bCs"))
            if b_cs is not None:
                val = b_cs.attrib.get(qn("w:val"), "true")
                run_properties["boldCs"] = val not in ("0", "false")

            # Italic (w:i -> italic)
            i = r_pr.find(qn("w:i"))
            if i is not None:
                val = i.attrib.get(qn("w:val"), "true")
                run_properties[self.tag_to_name("w:i")] = val not in ("0", "false")

            # Complex Script Italic (w:iCs)
            i_cs = r_pr.find(qn("w:iCs"))
            if i_cs is not None:
                val = i_cs.attrib.get(qn("w:val"), "true")
                run_properties["italicCs"] = val not in ("0", "false")

            # Underline (w:u -> underline)
            u = r_pr.find(qn("w:u"))
            if u is not None:
                run_properties[self.tag_to_name("w:u")] = u.attrib.get(qn("w:val"), "single")

            # Strikethrough (w:strike -> strikethrough)
            strike = r_pr.find(qn("w:strike"))
            if strike is not None:
                run_properties[self.tag_to_name("w:strike")] = True
                run_properties["strike"] = True

            # Color (w:color -> color)
            color = r_pr.find(qn("w:color"))
            if color is not None:
                run_properties[self.tag_to_name("w:color")] = color.attrib.get(qn("w:val"), "")

            # Font Size (w:sz -> fontSize)
            sz = r_pr.find(qn("w:sz"))
            if sz is not None:
                val = sz.attrib.get(qn("w:val"), "")
                run_properties[self.tag_to_name("w:sz")] = int(val) if val.isdigit() else val

            # Complex Script Font Size (w:szCs)
            sz_cs = r_pr.find(qn("w:szCs"))
            if sz_cs is not None:
                val = sz_cs.attrib.get(qn("w:val"), "")
                run_properties["fontSizeCs"] = int(val) if val.isdigit() else val

            # Font Family (w:rFonts -> fontFamily)
            r_fonts = r_pr.find(qn("w:rFonts"))
            if r_fonts is not None:
                font_dict: dict[str, str] = {local_name(k): v for k, v in r_fonts.attrib.items()}
                if font_dict:
                    primary_font = (
                        font_dict.get("ascii")
                        or font_dict.get("hAnsi")
                        or font_dict.get("asciiTheme")
                        or font_dict.get("hAnsiTheme")
                        or list(font_dict.values())[0]
                    )
                    run_properties[self.tag_to_name("w:rFonts")] = primary_font
                    run_properties["fontFamily"] = primary_font
                    run_properties["fonts"] = font_dict

            # Style (w:rStyle -> style)
            r_style = r_pr.find(qn("w:rStyle"))
            if r_style is not None:
                run_properties["style"] = r_style.attrib.get(qn("w:val"), "")

            # Vertical Alignment (w:vertAlign -> verticalAlignment)
            vert_align = r_pr.find(qn("w:vertAlign"))
            if vert_align is not None:
                run_properties[self.tag_to_name("w:vertAlign")] = vert_align.attrib.get(qn("w:val"), "")

            # Highlight (w:highlight -> highlight)
            highlight = r_pr.find(qn("w:highlight"))
            if highlight is not None:
                run_properties[self.tag_to_name("w:highlight")] = highlight.attrib.get(qn("w:val"), "")

            # Shading (w:shd)
            shd = r_pr.find(qn("w:shd"))
            if shd is not None:
                shd_dict: dict[str, Any] = {local_name(k): v for k, v in shd.attrib.items()}
                run_properties[self.tag_to_name("w:shd")] = shd_dict
                run_properties["shading"] = shd_dict

            # Vanish (w:vanish)
            if r_pr.find(qn("w:vanish")) is not None:
                run_properties["vanish"] = True

            # NoProof (w:noProof)
            if r_pr.find(qn("w:noProof")) is not None:
                run_properties["noProof"] = True

            # Language (w:lang)
            lang_el = r_pr.find(qn("w:lang"))
            if lang_el is not None:
                l_dict = {local_name(k): v for k, v in lang_el.attrib.items()}
                run_properties["language"] = l_dict

        # Text content (w:t -> text)
        texts: list[str] = []
        for t in element.findall(qn("w:t")):
            if t.text:
                texts.append(t.text)
        text_content = "".join(texts)

        # Breaks (w:br -> break)
        breaks: list[dict[str, str]] = []
        for br in element.findall(qn("w:br")):
            br_type = br.attrib.get(qn("w:type"), "textWrapping")
            breaks.append({"type": br_type})

        # Carriage return (w:cr)
        has_cr = element.find(qn("w:cr")) is not None

        # Tabs (w:tab -> tab)
        has_tab = element.find(qn("w:tab")) is not None

        # Drawings (w:drawing, including drawings inside mc:AlternateContent)
        drawings: list[dict[str, Any]] = []
        for d in element.iter(qn("w:drawing")):
            from handlers.media import MediaHandler
            drawings.append(MediaHandler().to_json(d))

        # VML Pictures / Shapes (w:pict)
        pictures: list[dict[str, Any]] = []
        for pict in element.findall(qn("w:pict")):
            pictures.append({"xml": ET.tostring(pict, encoding="utf-8").decode("utf-8")})

        result: dict[str, Any] = {
            "type": self.tag_to_name("w:r"),
            "runProperties": run_properties,
            "properties": run_properties,
            "text": text_content,
        }
        if breaks:
            result["breaks"] = breaks
        if has_cr:
            result["hasCarriageReturn"] = True
        if has_tab:
            result["hasTab"] = True
        if drawings:
            result["drawings"] = drawings
        if pictures:
            result["pictures"] = pictures

        return result

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert JSON run representation to w:r XML element."""
        r = ET.Element(qn("w:r"))
        props = data.get("runProperties") or data.get("properties", {})

        if props:
            r_pr = ET.SubElement(r, qn("w:rPr"))

            if props.get("style"):
                ET.SubElement(r_pr, qn("w:rStyle"), {qn("w:val"): str(props["style"])})

            fonts_data = props.get("fonts")
            if fonts_data and isinstance(fonts_data, dict):
                f_attrs = {qn(f"w:{k}"): str(v) for k, v in fonts_data.items()}
                ET.SubElement(r_pr, qn("w:rFonts"), f_attrs)
            elif props.get("fontFamily"):
                ET.SubElement(r_pr, qn("w:rFonts"), {
                    qn("w:ascii"): str(props["fontFamily"]),
                    qn("w:hAnsi"): str(props["fontFamily"]),
                    qn("w:cs"): str(props["fontFamily"]),
                })

            if props.get("bold"):
                ET.SubElement(r_pr, qn("w:b"))

            if props.get("boldCs"):
                ET.SubElement(r_pr, qn("w:bCs"))

            if props.get("italic"):
                ET.SubElement(r_pr, qn("w:i"))

            if props.get("italicCs"):
                ET.SubElement(r_pr, qn("w:iCs"))

            if props.get("underline"):
                u_val = props["underline"]
                val_str = "single" if isinstance(u_val, bool) else str(u_val)
                ET.SubElement(r_pr, qn("w:u"), {qn("w:val"): val_str})

            if props.get("strikethrough") or props.get("strike"):
                ET.SubElement(r_pr, qn("w:strike"))

            if props.get("color"):
                ET.SubElement(r_pr, qn("w:color"), {qn("w:val"): str(props["color"])})

            if props.get("fontSize") is not None:
                ET.SubElement(r_pr, qn("w:sz"), {qn("w:val"): str(props["fontSize"])})

            if props.get("fontSizeCs") is not None:
                ET.SubElement(r_pr, qn("w:szCs"), {qn("w:val"): str(props["fontSizeCs"])})

            if props.get("highlight"):
                ET.SubElement(r_pr, qn("w:highlight"), {qn("w:val"): str(props["highlight"])})

            if props.get("shading"):
                shd_attrs = {qn(f"w:{k}"): str(v) for k, v in props["shading"].items()}
                ET.SubElement(r_pr, qn("w:shd"), shd_attrs)

            if props.get("vanish"):
                ET.SubElement(r_pr, qn("w:vanish"))

            if props.get("noProof"):
                ET.SubElement(r_pr, qn("w:noProof"))

            if props.get("language"):
                l_attrs = {qn(f"w:{k}"): str(v) for k, v in props["language"].items()}
                ET.SubElement(r_pr, qn("w:lang"), l_attrs)

            if props.get("verticalAlignment"):
                ET.SubElement(r_pr, qn("w:vertAlign"), {qn("w:val"): str(props["verticalAlignment"])})

        # Tabs before or after text
        if data.get("hasTab"):
            ET.SubElement(r, qn("w:tab"))

        # Carriage return (w:cr)
        if data.get("hasCarriageReturn"):
            ET.SubElement(r, qn("w:cr"))

        # Text
        text = data.get("text", "")
        if text:
            t = ET.SubElement(r, qn("w:t"))
            t.text = text
            # Preserve whitespace if text starts or ends with whitespace
            if text.startswith(" ") or text.endswith(" ") or "\t" in text:
                t.set(qn("xml:space"), "preserve")

        # Breaks
        for br in data.get("breaks", []):
            br_attrs = {}
            if br.get("type") and br["type"] != "textWrapping":
                br_attrs[qn("w:type")] = br["type"]
            ET.SubElement(r, qn("w:br"), br_attrs)

        # Drawings
        for d_data in data.get("drawings", []):
            from handlers.media import MediaHandler
            r.append(MediaHandler().to_xml(d_data))

        # VML Pictures / Shapes (w:pict)
        for p_data in data.get("pictures", []):
            if "xml" in p_data:
                from utils.xml import parse_xml_string
                r.append(parse_xml_string(p_data["xml"]))

        return r
