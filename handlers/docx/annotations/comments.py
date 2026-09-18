"""Handler for WordprocessingML comments (word/comments.xml)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn
from handlers.docx.text import ParagraphHandler


class CommentsHandler(BaseHandler):
    """Handles word/comments.xml conversion to/from JSON."""

    def __init__(self, paragraph_handler: ParagraphHandler | None = None):
        self.paragraph_handler = paragraph_handler or ParagraphHandler()

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> list[dict[str, Any]]:
        """Convert comments XML element to a list of comment dictionaries."""
        comments: list[dict[str, Any]] = []

        for c_el in element.findall(qn("w:comment")):
            raw_id = c_el.attrib.get(qn("w:id"), "")
            c_id = int(raw_id) if raw_id.isdigit() else raw_id

            author = c_el.attrib.get(qn("w:author"), "")
            date_str = c_el.attrib.get(qn("w:date"), "")
            initials = c_el.attrib.get(qn("w:initials"), "")

            content: list[dict[str, Any]] = []
            for child in c_el:
                if child.tag == qn("w:p"):
                    content.append(self.paragraph_handler.to_json(child, simple=simple))

            entry: dict[str, Any] = {
                "id": c_id,
                "author": author,
                "content": content,
            }
            if date_str:
                entry["date"] = date_str
            if initials:
                entry["initials"] = initials

            comments.append(entry)

        return comments

    def to_xml(
        self,
        comments_data: list[dict[str, Any]] | dict[str, Any],
    ) -> ET.Element:
        """Build word/comments.xml element tree from comments data."""
        root = ET.Element(qn("w:comments"))

        comments_list = (
            comments_data
            if isinstance(comments_data, list)
            else comments_data.get("comments", [])
        )

        for comment in comments_list:
            if not isinstance(comment, dict):
                continue

            attrs = {
                qn("w:id"): str(comment.get("id", "1")),
                qn("w:author"): str(comment.get("author", "Author")),
            }
            if "date" in comment:
                attrs[qn("w:date")] = str(comment["date"])
            if "initials" in comment:
                attrs[qn("w:initials")] = str(comment["initials"])

            c_el = ET.SubElement(root, qn("w:comment"), attrs)

            content_items = comment.get("content", [])
            if not content_items and "text" in comment:
                content_items = [{"text": comment["text"]}]

            for item in content_items:
                if isinstance(item, str):
                    c_el.append(self.paragraph_handler.to_xml({"text": item}))
                elif isinstance(item, dict):
                    c_el.append(self.paragraph_handler.to_xml(item))

            if len(c_el) == 0:
                c_el.append(ET.Element(qn("w:p")))

        return root


__all__ = ["CommentsHandler"]
