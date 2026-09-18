"""Handler for WordprocessingML footnotes (word/footnotes.xml)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn
from handlers.docx.text.paragraph import ParagraphHandler


class FootnotesHandler(BaseHandler):
    """Handles parsing and generating word/footnotes.xml."""

    def __init__(self, paragraph_handler: ParagraphHandler | None = None):
        self.paragraph_handler = paragraph_handler or ParagraphHandler()

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> list[dict[str, Any]]:
        """Parse footnotes XML into a list of footnote dictionaries."""
        footnotes: list[dict[str, Any]] = []

        for note_el in element.findall(qn("w:footnote")):
            note_type = note_el.attrib.get(qn("w:type"), "")
            if note_type in ("separator", "continuationSeparator", "continuationNotice"):
                continue

            raw_id = note_el.attrib.get(qn("w:id"), "")
            note_id = int(raw_id) if raw_id.isdigit() or (raw_id.startswith("-") and raw_id[1:].isdigit()) else raw_id
            if isinstance(note_id, int) and note_id <= 0:
                continue

            content: list[dict[str, Any]] = []
            for child in note_el:
                if child.tag == qn("w:p"):
                    content.append(self.paragraph_handler.to_json(child, simple=simple))

            footnotes.append({
                "id": note_id,
                "content": content,
            })

        return footnotes

    def to_xml(
        self,
        footnotes_data: list[dict[str, Any]] | dict[str, Any],
    ) -> ET.Element:
        """Construct footnotes.xml element tree."""
        root = ET.Element(qn("w:footnotes"))
        notes_list = footnotes_data if isinstance(footnotes_data, list) else footnotes_data.get("footnotes", [])

        has_sep = any(
            str(n.get("id")) in ("-1", "0")
            or n.get("type") in ("separator", "continuationSeparator")
            for n in notes_list
            if isinstance(n, dict)
        )

        if not has_sep:
            sep = ET.SubElement(root, qn("w:footnote"), {qn("w:type"): "separator", qn("w:id"): "-1"})
            p_sep = ET.SubElement(sep, qn("w:p"))
            r_sep = ET.SubElement(p_sep, qn("w:r"))
            ET.SubElement(r_sep, qn("w:separator"))

            cont_sep = ET.SubElement(root, qn("w:footnote"), {qn("w:type"): "continuationSeparator", qn("w:id"): "0"})
            p_csep = ET.SubElement(cont_sep, qn("w:p"))
            r_csep = ET.SubElement(p_csep, qn("w:r"))
            ET.SubElement(r_csep, qn("w:continuationSeparator"))

        for note in notes_list:
            if not isinstance(note, dict):
                continue
            n_id = str(note.get("id", "1"))
            attrs = {qn("w:id"): n_id}
            if "type" in note:
                attrs[qn("w:type")] = str(note["type"])
            note_el = ET.SubElement(root, qn("w:footnote"), attrs)

            content_items = note.get("content", [])
            if not content_items and "text" in note:
                content_items = [{"text": note["text"]}]

            for item in content_items:
                if isinstance(item, str):
                    note_el.append(self.paragraph_handler.to_xml({"text": item}))
                elif isinstance(item, dict):
                    note_el.append(self.paragraph_handler.to_xml(item))

            if len(note_el) == 0:
                note_el.append(ET.Element(qn("w:p")))

        return root


__all__ = ["FootnotesHandler"]
