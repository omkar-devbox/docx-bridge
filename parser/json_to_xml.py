"""JSON to XML parser reconstructing OpenXML trees from structured JSON."""

from typing import Any
from xml.sax.saxutils import quoteattr
from utils.xml import serialize_xml
from handlers.document import DocumentHandler
from handlers.styles import StylesHandler
from handlers.numbering import NumberingHandler
from handlers.relationships import RelationshipsHandler


class JsonToXmlParser:
    """Reconstructs WordprocessingML XML documents from JSON representation."""

    def __init__(self):
        self.doc_handler = DocumentHandler()
        self.styles_handler = StylesHandler()
        self.numbering_handler = NumberingHandler()
        self.relationships_handler = RelationshipsHandler()

    def build_document_xml(self, data: dict[str, Any]) -> bytes:
        """Convert JSON document tree to serialized word/document.xml bytes."""
        root = self.doc_handler.to_xml(data)
        return serialize_xml(root)

    def build_styles_xml(self, data: dict[str, Any]) -> bytes:
        """Convert JSON styles tree to serialized word/styles.xml bytes."""
        root = self.styles_handler.to_xml(data)
        return serialize_xml(root)

    def build_numbering_xml(self, data: dict[str, Any]) -> bytes:
        """Convert JSON numbering tree to serialized word/numbering.xml bytes."""
        root = self.numbering_handler.to_xml(data)
        return serialize_xml(root)

    def build_relationships_xml(self, data: list[dict[str, Any]] | dict[str, Any]) -> bytes:
        """Convert JSON relationships to serialized XML bytes adhering to OPC standard."""
        rel_list = data if isinstance(data, list) else data.get("relationships", [])
        lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        ]
        for rel in rel_list:
            r_id = quoteattr(str(rel.get("id", "")))
            r_type = quoteattr(str(rel.get("type", "")))
            r_target = quoteattr(str(rel.get("target", "")))
            attrs = [f"Id={r_id}", f"Type={r_type}", f"Target={r_target}"]
            if rel.get("targetMode"):
                r_tm = quoteattr(str(rel.get("targetMode")))
                attrs.append(f"TargetMode={r_tm}")
            lines.append(f"  <Relationship {' '.join(attrs)}/>")
        lines.append('</Relationships>')
        return "\n".join(lines).encode("utf-8")