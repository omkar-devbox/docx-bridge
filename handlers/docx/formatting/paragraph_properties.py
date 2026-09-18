"""Handler for paragraph formatting properties (w:pPr)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name, PPR_ORDER, sort_children_by_schema
from handlers.docx.formatting.colors import ColorHandler


class ParagraphPropertiesHandler(BaseHandler):
    """Handles parsing and reconstructing w:pPr paragraph properties."""

    def __init__(self):
        self.color_handler = ColorHandler()

    def to_json(self, p_pr: ET.Element) -> dict[str, Any]:
        """Convert w:pPr element to JSON properties dictionary."""
        props: dict[str, Any] = {}
        if p_pr is None:
            return props

        # Paragraph Style (w:pStyle -> style)
        p_style = p_pr.find(qn("w:pStyle"))
        if p_style is not None:
            props["style"] = p_style.attrib.get(qn("w:val"), "")

        # Alignment (w:jc -> alignment)
        jc = p_pr.find(qn("w:jc"))
        if jc is not None:
            props["alignment"] = jc.attrib.get(qn("w:val"), "")

        # Spacing (w:spacing -> spacing)
        spacing = p_pr.find(qn("w:spacing"))
        if spacing is not None:
            sp_dict: dict[str, Any] = {}
            for attr, key in [
                ("w:before", "before"),
                ("w:after", "after"),
                ("w:line", "line"),
                ("w:lineRule", "lineRule"),
            ]:
                val = spacing.attrib.get(qn(attr))
                if val is not None:
                    sp_dict[key] = int(val) if val.isdigit() else val
            if sp_dict:
                props["spacing"] = sp_dict

        # Indentation (w:ind -> indentation)
        ind = p_pr.find(qn("w:ind"))
        if ind is not None:
            ind_dict: dict[str, Any] = {}
            for attr, key in [
                ("w:left", "left"),
                ("w:right", "right"),
                ("w:firstLine", "firstLine"),
                ("w:hanging", "hanging"),
            ]:
                val = ind.attrib.get(qn(attr))
                if val is not None:
                    ind_dict[key] = int(val) if val.isdigit() else val
            if ind_dict:
                props["indentation"] = ind_dict

        # Numbering reference (w:numPr -> numbering)
        num_pr = p_pr.find(qn("w:numPr"))
        if num_pr is not None:
            num_dict: dict[str, Any] = {}
            ilvl = num_pr.find(qn("w:ilvl"))
            if ilvl is not None:
                val = ilvl.attrib.get(qn("w:val"))
                if val is not None:
                    num_dict["ilvl"] = int(val) if val.isdigit() else val
            num_id = num_pr.find(qn("w:numId"))
            if num_id is not None:
                val = num_id.attrib.get(qn("w:val"))
                if val is not None:
                    num_dict["numId"] = int(val) if val.isdigit() else val
            if num_dict:
                props["numbering"] = num_dict

        # Outline Level (w:outlineLvl)
        outline = p_pr.find(qn("w:outlineLvl"))
        if outline is not None:
            val = outline.attrib.get(qn("w:val"))
            if val is not None:
                props["outlineLvl"] = int(val) if val.isdigit() else val

        # Layout boolean flags
        for xml_tag, key in [
            ("keepNext", "keepNext"),
            ("keepLines", "keepLines"),
            ("pageBreakBefore", "pageBreakBefore"),
            ("widowControl", "widowControl"),
            ("bidi", "bidi"),
        ]:
            el = p_pr.find(qn(f"w:{xml_tag}"))
            if el is not None:
                val = el.attrib.get(qn("w:val"), "1")
                props[key] = val not in ("0", "false", "off")

        # Paragraph Borders (w:pBdr)
        pbdr = p_pr.find(qn("w:pBdr"))
        if pbdr is not None:
            bdr_dict: dict[str, Any] = {}
            for side in ("top", "left", "bottom", "right", "between", "bar"):
                s_el = pbdr.find(qn(f"w:{side}"))
                if s_el is not None:
                    side_dict: dict[str, Any] = {}
                    for attr, a_key in [("w:val", "val"), ("w:sz", "sz"), ("w:space", "space"), ("w:color", "color")]:
                        v = s_el.attrib.get(qn(attr))
                        if v is not None:
                            side_dict[a_key] = int(v) if v.isdigit() else v
                    bdr_dict[side] = side_dict
            if bdr_dict:
                props["borders"] = bdr_dict

        # Shading (w:shd)
        shd = p_pr.find(qn("w:shd"))
        if shd is not None:
            props["shading"] = self.color_handler.to_json(shd)

        return props

    def to_xml(self, props: dict[str, Any]) -> ET.Element:
        """Construct w:pPr element from JSON properties dictionary."""
        p_pr = ET.Element(qn("w:pPr"))

        # Style
        if "style" in props and props["style"]:
            ET.SubElement(p_pr, qn("w:pStyle"), {qn("w:val"): str(props["style"])})

        # Keep Next
        if props.get("keepNext"):
            ET.SubElement(p_pr, qn("w:keepNext"))

        # Keep Lines
        if props.get("keepLines"):
            ET.SubElement(p_pr, qn("w:keepLines"))

        # Page Break Before
        if props.get("pageBreakBefore"):
            ET.SubElement(p_pr, qn("w:pageBreakBefore"))

        # Numbering
        num = props.get("numbering")
        if isinstance(num, dict):
            num_el = ET.SubElement(p_pr, qn("w:numPr"))
            if "ilvl" in num:
                ET.SubElement(num_el, qn("w:ilvl"), {qn("w:val"): str(num["ilvl"])})
            if "numId" in num:
                ET.SubElement(num_el, qn("w:numId"), {qn("w:val"): str(num["numId"])})

        # Widow Control
        if "widowControl" in props:
            val = "1" if props["widowControl"] else "0"
            ET.SubElement(p_pr, qn("w:widowControl"), {qn("w:val"): val})

        # Shading
        shd = props.get("shading")
        if shd:
            shd_el = self.color_handler.to_xml("shading", shd)
            if shd_el is not None:
                p_pr.append(shd_el)

        # Borders
        bdr = props.get("borders")
        if isinstance(bdr, dict):
            pbdr_el = ET.SubElement(p_pr, qn("w:pBdr"))
            for side in ("top", "left", "bottom", "right", "between", "bar"):
                if side in bdr and isinstance(bdr[side], dict):
                    s_data = bdr[side]
                    attrib = {qn("w:val"): str(s_data.get("val", "single"))}
                    for k, attr in [("sz", "w:sz"), ("space", "w:space"), ("color", "w:color")]:
                        if k in s_data:
                            attrib[qn(attr)] = str(s_data[k])
                    ET.SubElement(pbdr_el, qn(f"w:{side}"), attrib)

        # Spacing
        spacing = props.get("spacing")
        if isinstance(spacing, dict):
            sp_attrib = {}
            for key, attr in [("before", "w:before"), ("after", "w:after"), ("line", "w:line"), ("lineRule", "w:lineRule")]:
                if key in spacing:
                    sp_attrib[qn(attr)] = str(spacing[key])
            if sp_attrib:
                ET.SubElement(p_pr, qn("w:spacing"), sp_attrib)

        # Indentation
        ind = props.get("indentation")
        if isinstance(ind, dict):
            ind_attrib = {}
            for key, attr in [("left", "w:left"), ("right", "w:right"), ("firstLine", "w:firstLine"), ("hanging", "w:hanging")]:
                if key in ind:
                    ind_attrib[qn(attr)] = str(ind[key])
            if ind_attrib:
                ET.SubElement(p_pr, qn("w:ind"), ind_attrib)

        # Alignment
        align = props.get("alignment")
        if align:
            ET.SubElement(p_pr, qn("w:jc"), {qn("w:val"): str(align)})

        # Outline Level
        outline = props.get("outlineLvl")
        if outline is not None:
            ET.SubElement(p_pr, qn("w:outlineLvl"), {qn("w:val"): str(outline)})

        # Sort according to schema order
        sort_children_by_schema(p_pr, PPR_ORDER)
        return p_pr


__all__ = ["ParagraphPropertiesHandler"]
