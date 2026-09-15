from typing import Any

from utils.xml import parse_xml_string
from handlers.docx import DocxHandlerRegistry


# --------------------------------
# XML to JSON Parser
# --------------------------------

class XmlToJsonParser:

    # --------------------------------
    # Initialization
    # --------------------------------

    def __init__(self, registry: DocxHandlerRegistry | None = None):
        self.registry = registry or DocxHandlerRegistry()
        self.doc_handler = self.registry.document_handler
        self.styles_handler = self.registry.styles_handler
        self.numbering_handler = self.registry.numbering_handler
        self.relationships_handler = self.registry.relationships_handler
        self.header_footer_handler = self.registry.header_footer_handler
        self.properties_handler = self.registry.properties_handler
        self.notes_handler = self.registry.notes_handler
        self.comments_handler = self.registry.comments_handler
        self.settings_handler = self.registry.settings_handler

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
        )

        root = parse_xml_string(xml_content)
        return self.doc_handler.to_json(
            root,
            simple=is_simple,
        )

    # --------------------------------
    # Styles Parsing
    # --------------------------------

    def parse_styles(
        self,
        xml_content: str | bytes,
    ) -> dict[str, Any]:

        root = parse_xml_string(xml_content)
        return self.styles_handler.to_json(root)

    # --------------------------------
    # Numbering Parsing
    # --------------------------------

    def parse_numbering(
        self,
        xml_content: str | bytes,
    ) -> dict[str, Any]:

        root = parse_xml_string(xml_content)
        return self.numbering_handler.to_json(root)

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
        )

        root = parse_xml_string(xml_content)
        return self.relationships_handler.to_json(
            root,
            simple=is_simple,
        )

    # --------------------------------
    # Header & Footer Parsing
    # --------------------------------

    def parse_header(
        self,
        xml_content: str | bytes,
        simple: bool = True,
    ) -> dict[str, Any]:

        root = parse_xml_string(xml_content)
        return self.header_footer_handler.to_json(root, simple=simple)

    def parse_footer(
        self,
        xml_content: str | bytes,
        simple: bool = True,
    ) -> dict[str, Any]:

        root = parse_xml_string(xml_content)
        return self.header_footer_handler.to_json(root, simple=simple)

    # --------------------------------
    # Metadata Parsing
    # --------------------------------

    def parse_metadata(
        self,
        core_xml: str | bytes | None,
        app_xml: str | bytes | None = None,
    ) -> dict[str, Any]:

        core_root = parse_xml_string(core_xml) if core_xml else None
        app_root = parse_xml_string(app_xml) if app_xml else None
        return self.properties_handler.to_json(core_root, app_element=app_root)

    # --------------------------------
    # Notes Parsing
    # --------------------------------

    def parse_footnotes(
        self,
        xml_content: str | bytes,
        simple: bool = True,
    ) -> list[dict[str, Any]]:

        root = parse_xml_string(xml_content)
        return self.notes_handler.to_json(root, is_endnotes=False, simple=simple)

    def parse_endnotes(
        self,
        xml_content: str | bytes,
        simple: bool = True,
    ) -> list[dict[str, Any]]:

        root = parse_xml_string(xml_content)
        return self.notes_handler.to_json(root, is_endnotes=True, simple=simple)

    # --------------------------------
    # Comments Parsing
    # --------------------------------

    def parse_comments(
        self,
        xml_content: str | bytes,
        simple: bool = True,
    ) -> list[dict[str, Any]]:

        root = parse_xml_string(xml_content)
        return self.comments_handler.to_json(root, simple=simple)

    # --------------------------------
    # Settings Parsing
    # --------------------------------

    def parse_settings(
        self,
        xml_content: str | bytes,
    ) -> dict[str, Any]:

        root = parse_xml_string(xml_content)
        return self.settings_handler.to_json(root)