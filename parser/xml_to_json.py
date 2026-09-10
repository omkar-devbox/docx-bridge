from typing import Any

from utils.xml import parse_xml_string
from handlers.document import DocumentHandler
from handlers.styles import StylesHandler
from handlers.numbering import NumberingHandler
from handlers.relationships import RelationshipsHandler


# --------------------------------
# XML to JSON Parser
# --------------------------------

class XmlToJsonParser:

    # --------------------------------
    # Initialization
    # --------------------------------

    def __init__(self):
        self.doc_handler = DocumentHandler()  # Document parser
        self.styles_handler = StylesHandler()  # Styles parser
        self.numbering_handler = NumberingHandler()  # Numbering parser
        self.relationships_handler = RelationshipsHandler()  # Relationships parser


    # --------------------------------
    # Document Parsing
    # --------------------------------

    def parse_document(
        self,
        xml_content: str | bytes,
        mode: str = "raw",
        simple: bool | None = None,
    ) -> dict[str, Any]:

        is_simple = (
            simple
            if simple is not None
            else mode == "simple"
        )  # Resolve parsing mode

        root = parse_xml_string(xml_content)  # Parse document XML
        return self.doc_handler.to_json(
            root,
            simple=is_simple,
        )  # Convert document XML to JSON


    # --------------------------------
    # Styles Parsing
    # --------------------------------

    def parse_styles(
        self,
        xml_content: str | bytes,
    ) -> dict[str, Any]:

        root = parse_xml_string(xml_content)  # Parse styles XML
        return self.styles_handler.to_json(root)  # Convert styles XML to JSON


    # --------------------------------
    # Numbering Parsing
    # --------------------------------

    def parse_numbering(
        self,
        xml_content: str | bytes,
    ) -> dict[str, Any]:

        root = parse_xml_string(xml_content)  # Parse numbering XML
        return self.numbering_handler.to_json(root)  # Convert numbering XML to JSON


    # --------------------------------
    # Relationships Parsing
    # --------------------------------

    def parse_relationships(
        self,
        xml_content: str | bytes,
        mode: str = "simple",
        simple: bool | None = None,
    ) -> list[dict[str, Any]]:

        is_simple = (
            simple
            if simple is not None
            else mode == "simple"
        )  # Resolve parsing mode

        root = parse_xml_string(xml_content)  # Parse relationships XML
        return self.relationships_handler.to_json(
            root,
            simple=is_simple,
        )  # Convert relationships XML to JSON