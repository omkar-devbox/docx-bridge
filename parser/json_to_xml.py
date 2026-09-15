from typing import Any
from xml.sax.saxutils import quoteattr

from config import (
    XML_DECLARATION,
    PACKAGE_RELATIONSHIPS_NS,
    RELATIONSHIP_TYPES,
)
from utils.xml import serialize_xml
from handlers.docx import DocxHandlerRegistry


# --------------------------------
# JSON to XML Parser
# --------------------------------

class JsonToXmlParser:

    # --------------------------------
    # Initialization
    # --------------------------------

    def __init__(self, registry: DocxHandlerRegistry | None = None):
        self.registry = registry or DocxHandlerRegistry()
        self.doc_handler = self.registry.document_handler
        self.styles_handler = self.registry.styles_handler
        self.numbering_handler = self.registry.numbering_handler
        self.header_footer_handler = self.registry.header_footer_handler
        self.properties_handler = self.registry.properties_handler
        self.notes_handler = self.registry.notes_handler
        self.comments_handler = self.registry.comments_handler
        self.settings_handler = self.registry.settings_handler

    # --------------------------------
    # Document XML
    # --------------------------------

    def build_document_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.doc_handler.to_xml(data)
        return serialize_xml(root)

    # --------------------------------
    # Styles XML
    # --------------------------------

    def build_styles_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.styles_handler.to_xml(data)
        return serialize_xml(root)

    # --------------------------------
    # Numbering XML
    # --------------------------------

    def build_numbering_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.numbering_handler.to_xml(data)
        return serialize_xml(root)

    # --------------------------------
    # Header & Footer XML
    # --------------------------------

    def build_header_xml(
        self,
        data: dict[str, Any] | list[Any],
    ) -> bytes:

        root = self.header_footer_handler.to_xml(data, is_footer=False)
        return serialize_xml(root)

    def build_footer_xml(
        self,
        data: dict[str, Any] | list[Any],
    ) -> bytes:

        root = self.header_footer_handler.to_xml(data, is_footer=True)
        return serialize_xml(root)

    # --------------------------------
    # Metadata XML
    # --------------------------------

    def build_core_properties_xml(
        self,
        metadata: dict[str, Any],
    ) -> bytes:

        return self.properties_handler.to_core_xml(metadata)

    def build_app_properties_xml(
        self,
        metadata: dict[str, Any],
    ) -> bytes:

        return self.properties_handler.to_app_xml(metadata)

    # --------------------------------
    # Notes XML
    # --------------------------------

    def build_footnotes_xml(
        self,
        data: list[dict[str, Any]] | dict[str, Any],
    ) -> bytes:

        root = self.notes_handler.to_xml(data, is_endnotes=False)
        return serialize_xml(root)

    def build_endnotes_xml(
        self,
        data: list[dict[str, Any]] | dict[str, Any],
    ) -> bytes:

        root = self.notes_handler.to_xml(data, is_endnotes=True)
        return serialize_xml(root)

    # --------------------------------
    # Comments XML
    # --------------------------------

    def build_comments_xml(
        self,
        data: list[dict[str, Any]] | dict[str, Any],
    ) -> bytes:

        root = self.comments_handler.to_xml(data)
        return serialize_xml(root)

    # --------------------------------
    # Settings XML
    # --------------------------------

    def build_settings_xml(
        self,
        settings_data: dict[str, Any] | None = None,
    ) -> bytes:

        root = self.settings_handler.to_xml(settings_data)
        return serialize_xml(root)

    def build_web_settings_xml(self) -> bytes:

        return self.settings_handler.to_web_settings_xml()

    # --------------------------------
    # Relationships XML
    # --------------------------------

    def build_relationships_xml(
        self,
        data: list[dict[str, Any]] | dict[str, Any],
    ) -> bytes:

        rel_list = (
            data
            if isinstance(data, list)
            else data.get("relationships", [])
        )

        lines = [
            XML_DECLARATION,
            f'<Relationships xmlns="{PACKAGE_RELATIONSHIPS_NS}">',
        ]

        for rel in rel_list:
            r_id = quoteattr(
                str(rel.get("id", ""))
            )

            raw_type = str(
                rel.get("type", "")
            )

            full_type = RELATIONSHIP_TYPES.get(
                raw_type,
                raw_type,
            )

            r_type = quoteattr(
                full_type
            )

            r_target = quoteattr(
                str(rel.get("target", ""))
            )

            attrs = [
                f"Id={r_id}",
                f"Type={r_type}",
                f"Target={r_target}",
            ]

            if rel.get("targetMode"):
                r_tm = quoteattr(
                    str(rel.get("targetMode"))
                )

                attrs.append(
                    f"TargetMode={r_tm}"
                )

            lines.append(
                f"  <Relationship {' '.join(attrs)}/>"
            )

        lines.append(
            "</Relationships>"
        )

        return "\n".join(
            lines
        ).encode("utf-8")