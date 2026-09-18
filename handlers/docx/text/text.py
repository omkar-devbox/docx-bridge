"""Handler for textual elements inside runs: w:t, w:br, w:cr, w:tab, w:sym."""

import re
from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


INVALID_XML_CHARS_RE = re.compile(
    r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]"
)
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


class TextHandler(BaseHandler):
    """Handles parsing and generating w:t, w:br, w:cr, w:tab, w:sym, and hyphen elements."""

    @staticmethod
    def clean_text(text: str | None) -> str:
        """Strip characters invalid in XML 1.0."""
        if not text:
            return ""
        return INVALID_XML_CHARS_RE.sub("", text)

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a text token element (w:t, w:br, etc.) to a JSON AST dict."""
        tag = local_name(element.tag)

        if tag == "t":
            text = self.clean_text(element.text or "")
            space = element.attrib.get(XML_SPACE)
            res: dict[str, Any] = {"type": "text", "value": text}
            if space:
                res["space"] = space
            return res

        elif tag == "br":
            br_type = element.attrib.get(qn("w:type"), "textWrapping")
            clear = element.attrib.get(qn("w:clear"))
            res = {"type": "break", "breakType": br_type}
            if clear:
                res["clear"] = clear
            return res

        elif tag == "cr":
            return {"type": "carriageReturn"}

        elif tag == "tab":
            return {"type": "tab"}

        elif tag == "noBreakHyphen":
            return {"type": "noBreakHyphen"}

        elif tag == "softHyphen":
            return {"type": "softHyphen"}

        elif tag == "sym":
            font = element.attrib.get(qn("w:font"), "")
            char = element.attrib.get(qn("w:char"), "")
            return {"type": "symbol", "font": font, "char": char}

        return {"type": tag, "value": element.text or ""}

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct the corresponding XML element for a text token AST dict."""
        token_type = data.get("type", "text")

        if token_type in ("text", "t"):
            el = ET.Element(qn("w:t"))
            val = str(data.get("value", ""))
            el.text = self.clean_text(val)
            space = data.get("space")
            if space:
                el.set(XML_SPACE, space)
            elif val.startswith(" ") or val.endswith(" ") or "\n" in val:
                el.set(XML_SPACE, "preserve")
            return el

        elif token_type in ("break", "br"):
            el = ET.Element(qn("w:br"))
            br_type = data.get("breakType")
            if br_type:
                el.set(qn("w:type"), br_type)
            clear = data.get("clear")
            if clear:
                el.set(qn("w:clear"), clear)
            return el

        elif token_type in ("carriageReturn", "cr"):
            return ET.Element(qn("w:cr"))

        elif token_type in ("tab", "tabChar"):
            return ET.Element(qn("w:tab"))

        elif token_type in ("noBreakHyphen",):
            return ET.Element(qn("w:noBreakHyphen"))

        elif token_type in ("softHyphen",):
            return ET.Element(qn("w:softHyphen"))

        elif token_type in ("symbol", "sym"):
            el = ET.Element(qn("w:sym"))
            if "font" in data:
                el.set(qn("w:font"), str(data["font"]))
            if "char" in data:
                el.set(qn("w:char"), str(data["char"]))
            return el

        el = ET.Element(qn(f"w:{token_type}"))
        if "value" in data:
            el.text = str(data["value"])
        return el


__all__ = ["TextHandler", "INVALID_XML_CHARS_RE", "XML_SPACE"]
