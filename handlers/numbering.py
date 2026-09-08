"""Handler for word/numbering.xml."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn


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

                lvl_text = lvl.find(qn("w:lvlText"))
                if lvl_text is not None:
                    lvl_dict["text"] = lvl_text.attrib.get(qn("w:val"), "")

                lvl_jc = lvl.find(qn("w:lvlJc"))
                if lvl_jc is not None:
                    lvl_dict["alignment"] = lvl_jc.attrib.get(qn("w:val"), "left")

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
                if "start" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:start"), {qn("w:val"): str(lvl_data["start"])})
                if "format" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:numFmt"), {qn("w:val"): str(lvl_data["format"])})
                if "text" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:lvlText"), {qn("w:val"): str(lvl_data["text"])})
                if "alignment" in lvl_data:
                    ET.SubElement(lvl_elem, qn("w:lvlJc"), {qn("w:val"): str(lvl_data["alignment"])})

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
