from typing import Any
from xml.sax.saxutils import quoteattr

from config import (
    XML_DECLARATION,
    PACKAGE_RELATIONSHIPS_NS,
    RELATIONSHIP_TYPES,
)
from utils.xml import serialize_xml
from handlers.document import DocumentHandler
from handlers.styles import StylesHandler
from handlers.numbering import NumberingHandler


# --------------------------------
# JSON to XML Parser
# --------------------------------

class JsonToXmlParser:

    # --------------------------------
    # Initialization
    # --------------------------------

    def __init__(self):
        self.doc_handler = DocumentHandler()  # Document XML handler
        self.styles_handler = StylesHandler()  # Styles XML handler
        self.numbering_handler = NumberingHandler()  # Numbering XML handler


    # --------------------------------
    # Document XML
    # --------------------------------

    def build_document_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.doc_handler.to_xml(data)  # Build document XML tree
        return serialize_xml(root)  # Serialize XML tree to bytes


    # --------------------------------
    # Styles XML
    # --------------------------------

    def build_styles_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.styles_handler.to_xml(data)  # Build styles XML tree
        return serialize_xml(root)  # Serialize XML tree to bytes


    # --------------------------------
    # Numbering XML
    # --------------------------------

    def build_numbering_xml(
        self,
        data: dict[str, Any],
    ) -> bytes:

        root = self.numbering_handler.to_xml(data)  # Build numbering XML tree
        return serialize_xml(root)  # Serialize XML tree to bytes


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
        )  # Normalize relationship data

        lines = [
            XML_DECLARATION,
            f'<Relationships xmlns="{PACKAGE_RELATIONSHIPS_NS}">',
        ]  # Initialize relationships XML

        for rel in rel_list:
            r_id = quoteattr(
                str(rel.get("id", ""))
            )  # Escape relationship ID

            raw_type = str(
                rel.get("type", "")
            )  # Read relationship type

            full_type = RELATIONSHIP_TYPES.get(
                raw_type,
                raw_type,
            )  # Resolve relationship type

            r_type = quoteattr(
                full_type
            )  # Escape relationship type

            r_target = quoteattr(
                str(rel.get("target", ""))
            )  # Escape relationship target

            attrs = [
                f"Id={r_id}",
                f"Type={r_type}",
                f"Target={r_target}",
            ]  # Build relationship attributes

            if rel.get("targetMode"):
                r_tm = quoteattr(
                    str(rel.get("targetMode"))
                )  # Escape target mode

                attrs.append(
                    f"TargetMode={r_tm}"
                )  # Add target mode

            lines.append(
                f"  <Relationship {' '.join(attrs)}/>"
            )  # Add relationship element

        lines.append(
            "</Relationships>"
        )  # Close relationships XML

        return "\n".join(
            lines
        ).encode("utf-8")  # Return XML bytes