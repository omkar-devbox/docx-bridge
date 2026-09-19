from typing import Any
from xml.sax.saxutils import quoteattr

from config import (
    CONTENT_TYPES_DATA,
    DOCX_CONFIG_DATA,
    PACKAGE_RELATIONSHIPS_NS,
    RELATIONSHIPS_DATA,
    RELATIONSHIP_TYPES,
    XML_DECLARATION,
)
from handlers.docx import DocxHandlerRegistry
from handlers.docx.package.content_types import ContentTypesHandler
from handlers.docx.package.relationships import RelationshipsHandler
from utils.docx.xml import serialize_xml


# --------------------------------
# JSON to XML Parser
# --------------------------------

class JsonToXmlParser:

    # --------------------------------
    # Initialization
    # --------------------------------

    def __init__(
        self,
        registry: DocxHandlerRegistry | None = None,
        docx_config: dict[str, Any] | None = None,
        content_types_config: dict[str, Any] | None = None,
        relationships_config: dict[str, Any] | None = None,
    ):
        self.registry = registry or DocxHandlerRegistry()
        self.docx_config: dict[str, Any] = docx_config if docx_config is not None else DOCX_CONFIG_DATA
        self.content_types_config: dict[str, Any] = content_types_config if content_types_config is not None else CONTENT_TYPES_DATA
        self.relationships_config: dict[str, Any] = relationships_config if relationships_config is not None else RELATIONSHIPS_DATA

        self.doc_handler = self.registry.document_handler
        self.styles_handler = self.registry.styles_handler
        self.numbering_handler = self.registry.numbering_handler
        self.header_footer_handler = self.registry.header_footer_handler
        self.properties_handler = self.registry.properties_handler
        self.notes_handler = self.registry.notes_handler
        self.comments_handler = self.registry.comments_handler
        self.settings_handler = self.registry.settings_handler
        self.theme_handler = self.registry.theme_handler

        if relationships_config is not None:
            self.relationships_handler = RelationshipsHandler(
                relationships_config=self.relationships_config
            )
        else:
            self.relationships_handler = self.registry.relationships_handler

        if content_types_config is not None:
            self.content_types_handler = ContentTypesHandler(
                content_types_config=self.content_types_config
            )
        else:
            self.content_types_handler = self.registry.content_types_handler

    # --------------------------------
    # Document XML
    # --------------------------------

    def build_document_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.doc_handler.to_xml(data)
        return serialize_xml(root, docx_config=self.docx_config)

    # --------------------------------
    # Styles XML
    # --------------------------------

    def build_styles_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.styles_handler.to_xml(data)
        return serialize_xml(root, docx_config=self.docx_config)

    # --------------------------------
    # Numbering XML
    # --------------------------------

    def build_numbering_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.numbering_handler.to_xml(data)
        return serialize_xml(root, docx_config=self.docx_config)

    # --------------------------------
    # Header & Footer XML
    # --------------------------------

    def build_header_xml(
        self,
        data: dict[str, Any] | list[Any],
    ) -> bytes:

        root = self.header_footer_handler.to_xml(data, is_footer=False)
        return serialize_xml(root, docx_config=self.docx_config)

    def build_footer_xml(
        self,
        data: dict[str, Any] | list[Any],
    ) -> bytes:

        root = self.header_footer_handler.to_xml(data, is_footer=True)
        return serialize_xml(root, docx_config=self.docx_config)

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
        return serialize_xml(root, docx_config=self.docx_config)

    def build_endnotes_xml(
        self,
        data: list[dict[str, Any]] | dict[str, Any],
    ) -> bytes:

        root = self.notes_handler.to_xml(data, is_endnotes=True)
        return serialize_xml(root, docx_config=self.docx_config)

    # --------------------------------
    # Comments XML
    # --------------------------------

    def build_comments_xml(
        self,
        data: list[dict[str, Any]] | dict[str, Any],
    ) -> bytes:

        root = self.comments_handler.to_xml(data)
        return serialize_xml(root, docx_config=self.docx_config)

    # --------------------------------
    # Settings XML
    # --------------------------------

    def build_settings_xml(
        self,
        settings_data: dict[str, Any] | None = None,
    ) -> bytes:

        root = self.settings_handler.to_xml(settings_data)
        return serialize_xml(root, docx_config=self.docx_config)

    def build_web_settings_xml(self) -> bytes:

        return self.settings_handler.to_web_settings_xml()

    # --------------------------------
    # Theme & Content Types XML
    # --------------------------------

    def build_theme_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.theme_handler.to_xml(data)
        return serialize_xml(root, docx_config=self.docx_config)

    def build_content_types_xml(
        self,
        data: dict[str, Any] | None = None,
    ) -> bytes:

        root = self.content_types_handler.to_xml(data)
        return serialize_xml(root, docx_config=self.docx_config)

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

        xml_decl = self.docx_config.get("xml_declaration") or XML_DECLARATION
        rels_ns = (
            self.relationships_config.get("namespaces", {}).get("package")
            or PACKAGE_RELATIONSHIPS_NS
        )
        rel_types = self.relationships_config.get("types") or RELATIONSHIP_TYPES

        lines = [
            xml_decl,
            f'<Relationships xmlns="{rels_ns}">',
        ]

        for rel in rel_list:
            r_id = quoteattr(
                str(rel.get("id", ""))
            )

            raw_type = str(
                rel.get("type", "")
            )

            full_type = rel_types.get(
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