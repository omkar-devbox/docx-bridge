"""Handler for word/numbering.xml."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name


class NumberingHandler(BaseHandler):
    """Handles word/numbering.xml element conversion to/from JSON."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert numbering XML element to JSON dictionary."""
        abstract_num_list: list[dict[str, Any]] = []
        for abs_elem in element.findall(qn("w:abstractNum")):
            abs_id = abs_elem.attrib.get(qn("w:abstractNumId"), "")
            levels: list[dict[str, Any]] = []

            for lvl in abs_elem.findall(qn("w:lvl")):
                ilvl = lvl.attrib.get(qn("w:ilvl"), "0")
                lvl_dict: dict[str, Any] = {
                    "level": int(ilvl) if ilvl.isdigit() else ilvl,
                }

                start = lvl.find(qn("w:start"))
                if start is not None:
                    s_val = start.attrib.get(qn("w:val"), "1")
                    lvl_dict["start"] = int(s_val) if s_val.isdigit() else s_val

                num_fmt = lvl.find(qn("w:numFmt"))
                if num_fmt is not None:
                    lvl_dict["format"] = num_fmt.attrib.get(qn("w:val"), "decimal")

                restart = lvl.find(qn("w:lvlRestart"))
                if restart is not None:
                    r_val = restart.attrib.get(qn("w:val"), "1")
                    lvl_dict["restart"] = int(r_val) if r_val.isdigit() else r_val

                p_style = lvl.find(qn("w:pStyle"))
                if p_style is not None:
                    lvl_dict["style"] = p_style.attrib.get(qn("w:val"), "")

                suff = lvl.find(qn("w:suff"))
                if suff is not None:
                    lvl_dict["suffix"] = suff.attrib.get(qn("w:val"), "tab")

                lvl_text = lvl.find(qn("w:lvlText"))
                if lvl_text is not None:
                    lvl_dict["text"] = lvl_text.attrib.get(qn("w:val"), "")

                lvl_jc = lvl.find(qn("w:lvlJc"))
                if lvl_jc is not None:
                    lvl_dict["alignment"] = lvl_jc.attrib.get(qn("w:val"), "left")

                # Paragraph properties inside level (indentation, tabs)
                p_pr = lvl.find(qn("w:pPr"))
                if p_pr is not None:
                    ind = p_pr.find(qn("w:ind"))
                    if ind is not None:
                        ind_dict: dict[str, Any] = {}
                        for attr, key in [
                            ("w:left", "left"),
                            ("w:hanging", "hanging"),
                            ("w:firstLine", "firstLine"),
                            ("w:right", "right"),
                        ]:
                            val = ind.attrib.get(qn(attr))
                            if val is not None:
                                ind_dict[key] = int(val) if val.isdigit() or (val.startswith("-") and val[1:].isdigit()) else val
                        if ind_dict:
                            lvl_dict["indent"] = ind_dict

                    tabs_el = p_pr.find(qn("w:tabs"))
                    if tabs_el is not None:
                        tab_list: list[dict[str, Any]] = []
                        for tb in tabs_el.findall(qn("w:tab")):
                            t_dict: dict[str, Any] = {}
                            for k, v in tb.attrib.items():
                                t_dict[local_name(k)] = int(v) if v.isdigit() or (v.startswith("-") and v[1:].isdigit()) else v
                            tab_list.append(t_dict)
                        if tab_list:
                            lvl_dict["tabs"] = tab_list

                # Run properties inside level (font, size, etc.)
                r_pr = lvl.find(qn("w:rPr"))
                if r_pr is not None:
                    r_fonts = r_pr.find(qn("w:rFonts"))
                    if r_fonts is not None:
                        f_dict: dict[str, str] = {}
                        for attr, key in [
                            ("w:ascii", "ascii"),
                            ("w:hAnsi", "hAnsi"),
                            ("w:eastAsia", "eastAsia"),
                            ("w:cs", "cs"),
                            ("w:hint", "hint"),
                        ]:
                            val = r_fonts.attrib.get(qn(attr))
                            if val:
                                f_dict[key] = val
                        if f_dict:
                            lvl_dict["fonts"] = f_dict

                levels.append(lvl_dict)

            abstract_num_list.append({
                "id": abs_id,
                "levels": levels,
            })

        num_list: list[dict[str, Any]] = []
        for num in element.findall(qn("w:num")):
            num_id = num.attrib.get(qn("w:numId"), "")
            abs_ref = num.find(qn("w:abstractNumId"))
            abstract_id = (
                abs_ref.attrib.get(qn("w:val"), "")
                if abs_ref is not None
                else ""
            )
            num_list.append({"numId": num_id, "abstractNumId": abstract_id})

        return {
            "abstractNumbering": abstract_num_list,
            "numbering": num_list,
        }

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert numbering JSON representation to w:numbering XML element."""
        root = ET.Element(qn("w:numbering"))

        for abs_data in data.get("abstractNumbering", []):
            abs_elem = ET.SubElement(
                root,
                qn("w:abstractNum"),
                {qn("w:abstractNumId"): str(abs_data.get("id", "0"))},
            )
            for lvl_data in abs_data.get("levels", []):
                lvl_elem = ET.SubElement(
                    abs_elem,
                    qn("w:lvl"),
                    {qn("w:ilvl"): str(lvl_data.get("level", "0"))},
                )
                # Strictly ordered child elements according to OpenXML schema
                if "start" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:start"), {qn("w:val"): str(lvl_data["start"])})
                if "format" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:numFmt"), {qn("w:val"): str(lvl_data["format"])})
                if "restart" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:lvlRestart"), {qn("w:val"): str(lvl_data["restart"])})
                if "style" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:pStyle"), {qn("w:val"): str(lvl_data["style"])})
                if "suffix" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:suff"), {qn("w:val"): str(lvl_data["suffix"])})
                if "text" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:lvlText"), {qn("w:val"): str(lvl_data["text"])})
                if "alignment" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:lvlJc"), {qn("w:val"): str(lvl_data["alignment"])})

                # w:pPr
                ind_data = lvl_data.get("indent")
                tabs_data = lvl_data.get("tabs")
                if ind_data or tabs_data:
                    p_pr = ET.SubElement(lvl_elem, qn("w:pPr"))
                    if tabs_data:
                        tabs_el = ET.SubElement(p_pr, qn("w:tabs"))
                        for t in tabs_data:
                            t_attrs = {qn(f"w:{k}"): str(v) for k, v in t.items()}
                            ET.SubElement(tabs_el, qn("w:tab"), t_attrs)
                    if ind_data:
                        ind_attrs = {qn(f"w:{k}"): str(v) for k, v in ind_data.items()}
                        ET.SubElement(p_pr, qn("w:ind"), ind_attrs)

                # w:rPr
                fonts_data = lvl_data.get("fonts")
                if fonts_data:
                    r_pr = ET.SubElement(lvl_elem, qn("w:rPr"))
                    f_attrs = {qn(f"w:{k}"): str(v) for k, v in fonts_data.items()}
                    ET.SubElement(r_pr, qn("w:rFonts"), f_attrs)

        for item in data.get("numbering", []):
            num = ET.SubElement(
                root,
                qn("w:num"),
                {qn("w:numId"): str(item.get("numId", ""))},
            )
            ET.SubElement(
                num,
                qn("w:abstractNumId"),
                {qn("w:val"): str(item.get("abstractNumId", ""))},
            )

        return root

    @staticmethod
    def build_default_numbering() -> dict[str, Any]:
        """Generate comprehensive standard multi-level numbering presets.

        Presets:
        - numId 1: Standard Multi-Level Bullet (•, ◦, ▪, –, •, ◦, ▪, –, •)
        - numId 2: Arrow / Chevron Multi-Level (>, », ›, ➢, ➔, →, >, », ›)
        - numId 3: Decimal Multi-Level (%1., %1.%2., %1.%2.%3., ...)
        - numId 4: Dot Multi-Level (., .., ..., ...., ...)
        - numId 5: Dash / Hyphen Multi-Level (–, —, –, —, ...)
        """
        bullet_levels = [
            ("•", {"ascii": "Symbol", "hAnsi": "Symbol"}),
            ("◦", {"ascii": "Courier New", "hAnsi": "Courier New"}),
            ("▪", {"ascii": "Wingdings", "hAnsi": "Wingdings"}),
            ("–", {}),
            ("•", {"ascii": "Symbol", "hAnsi": "Symbol"}),
            ("◦", {"ascii": "Courier New", "hAnsi": "Courier New"}),
            ("▪", {"ascii": "Wingdings", "hAnsi": "Wingdings"}),
            ("–", {}),
            ("•", {"ascii": "Symbol", "hAnsi": "Symbol"}),
        ]

        arrow_levels = [">", "»", "›", "➢", "➔", "→", ">", "»", "›"]
        dot_levels = [".", "..", "...", "....", ".", "..", "...", "....", "."]
        dash_levels = ["–", "—", "–", "—", "–", "—", "–", "—", "–"]

        # Abstract 1: Standard Bullet
        abs_bullet_levels = []
        for i in range(9):
            text, fonts = bullet_levels[i]
            lvl: dict[str, Any] = {
                "level": i,
                "start": 1,
                "format": "bullet",
                "text": text,
                "alignment": "left",
                "indent": {"left": 720 * (i + 1), "hanging": 360},
            }
            if fonts:
                lvl["fonts"] = fonts
            abs_bullet_levels.append(lvl)

        # Abstract 2: Arrow Bullet (>, », ›, ...)
        abs_arrow_levels = []
        for i in range(9):
            abs_arrow_levels.append({
                "level": i,
                "start": 1,
                "format": "bullet",
                "text": arrow_levels[i],
                "alignment": "left",
                "indent": {"left": 720 * (i + 1), "hanging": 360},
            })

        # Abstract 3: Decimal Multi-Level (%1., %1.%2., ...)
        abs_dec_levels = []
        for i in range(9):
            fmt_text = ".".join([f"%{j+1}" for j in range(i + 1)]) + "."
            abs_dec_levels.append({
                "level": i,
                "start": 1,
                "format": "decimal",
                "text": fmt_text,
                "alignment": "left",
                "indent": {"left": 720 * (i + 1), "hanging": 360},
            })

        # Abstract 4: Dot Bullet (., .., ...)
        abs_dot_levels = []
        for i in range(9):
            abs_dot_levels.append({
                "level": i,
                "start": 1,
                "format": "bullet",
                "text": dot_levels[i],
                "alignment": "left",
                "indent": {"left": 720 * (i + 1), "hanging": 360},
            })

        # Abstract 5: Dash Bullet (–, —, ...)
        abs_dash_levels = []
        for i in range(9):
            abs_dash_levels.append({
                "level": i,
                "start": 1,
                "format": "bullet",
                "text": dash_levels[i],
                "alignment": "left",
                "indent": {"left": 720 * (i + 1), "hanging": 360},
            })

        abstract_numbering = [
            {"id": "1", "levels": abs_bullet_levels},
            {"id": "2", "levels": abs_arrow_levels},
            {"id": "3", "levels": abs_dec_levels},
            {"id": "4", "levels": abs_dot_levels},
            {"id": "5", "levels": abs_dash_levels},
        ]

        numbering_instances = [
            {"numId": "1", "abstractNumId": "1"},
            {"numId": "2", "abstractNumId": "2"},
            {"numId": "3", "abstractNumId": "3"},
            {"numId": "4", "abstractNumId": "4"},
            {"numId": "5", "abstractNumId": "5"},
        ]

        return {
            "abstractNumbering": abstract_numbering,
            "numbering": numbering_instances,
        }

    @staticmethod
    def build_custom_bullet_abstract_num(symbol: str, abs_id: int | str) -> dict[str, Any]:
        """Generate an abstractNum definition for an arbitrary custom bullet symbol."""
        levels = []
        for i in range(9):
            levels.append({
                "level": i,
                "start": 1,
                "format": "bullet",
                "text": symbol,
                "alignment": "left",
                "indent": {"left": 720 * (i + 1), "hanging": 360},
            })
        return {
            "id": str(abs_id),
            "levels": levels,
        }
