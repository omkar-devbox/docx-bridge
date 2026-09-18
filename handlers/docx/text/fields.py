"""Handler for WordprocessingML field elements (w:fldSimple, w:fldChar, w:instrText)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class FieldsHandler(BaseHandler):
    """Handles parsing and reconstructing simple and complex fields."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a field element to JSON AST dictionary."""
        tag = local_name(element.tag)

        if tag == "fldSimple":
            instr = element.attrib.get(qn("w:instr"), "")
            lock = element.attrib.get(qn("w:fldLock"))
            dirty = element.attrib.get(qn("w:dirty"))
            res: dict[str, Any] = {
                "type": "fieldSimple",
                "instruction": instr,
            }
            if lock is not None:
                res["lock"] = lock
            if dirty is not None:
                res["dirty"] = dirty
            return res

        elif tag == "fldChar":
            char_type = element.attrib.get(qn("w:fldCharType"), "")
            lock = element.attrib.get(qn("w:fldLock"))
            dirty = element.attrib.get(qn("w:dirty"))
            res = {
                "type": "fieldCharacter",
                "charType": char_type,
            }
            if lock is not None:
                res["lock"] = lock
            if dirty is not None:
                res["dirty"] = dirty
            return res

        elif tag == "instrText":
            return {
                "type": "instructionText",
                "value": element.text or "",
            }

        return {"type": tag, "value": element.text or ""}

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct the XML element for a field AST dictionary."""
        f_type = data.get("type", "")

        if f_type in ("fieldSimple", "simpleField"):
            el = ET.Element(qn("w:fldSimple"))
            if "instruction" in data:
                el.set(qn("w:instr"), str(data["instruction"]))
            if "lock" in data:
                el.set(qn("w:fldLock"), str(data["lock"]))
            if "dirty" in data:
                el.set(qn("w:dirty"), str(data["dirty"]))
            return el

        elif f_type in ("fieldCharacter", "fldChar"):
            el = ET.Element(qn("w:fldChar"))
            if "charType" in data:
                el.set(qn("w:fldCharType"), str(data["charType"]))
            if "lock" in data:
                el.set(qn("w:fldLock"), str(data["lock"]))
            if "dirty" in data:
                el.set(qn("w:dirty"), str(data["dirty"]))
            return el

        elif f_type in ("instructionText", "instrText"):
            el = ET.Element(qn("w:instrText"))
            el.text = str(data.get("value", ""))
            return el

        return ET.Element(qn(f"w:{f_type}"))


__all__ = ["FieldsHandler"]
