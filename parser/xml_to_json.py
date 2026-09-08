"""XML to JSON parser coordinating handlers across DOCX document parts."""

from typing import Any
from utils.xml import parse_xml_string
from handlers.document import DocumentHandler
from handlers.styles import StylesHandler
from handlers.numbering import NumberingHandler
from handlers.relationships import RelationshipsHandler


class XmlToJsonParser:
    """Parses DOCX WordprocessingML XML trees into a structured JSON dictionary."""

    def __init__(self):
        self.doc_handler = DocumentHandler()
        self.styles_handler = StylesHandler()
        self.numbering_handler = NumberingHandler()
        self.relationships_handler = RelationshipsHandler()

    def parse_document(self, xml_content: str | bytes) -> dict[str, Any]:
        """Parse main word/document.xml content."""
        root = parse_xml_string(xml_content)
        return self.doc_handler.to_json(root)

    def parse_styles(self, xml_content: str | bytes) -> dict[str, Any]:
        """Parse word/styles.xml content."""
        root = parse_xml_string(xml_content)
        return self.styles_handler.to_json(root)

    def parse_numbering(self, xml_content: str | bytes) -> dict[str, Any]:
        """Parse word/numbering.xml content."""
        root = parse_xml_string(xml_content)
        return self.numbering_handler.to_json(root)

    def parse_relationships(self, xml_content: str | bytes) -> list[dict[str, Any]]:
        """Parse word/_rels/document.xml.rels content."""
        root = parse_xml_string(xml_content)
        return self.relationships_handler.to_json(root)