# --------------------------------
# Imports
# --------------------------------

from abc import ABC, abstractmethod
from typing import Any
import xml.etree.ElementTree as ET

from config import (
    NAMESPACES,
    REVERSE_NAMESPACES,
    tag_to_name,
    name_to_tag,
    PPR_ORDER,
    RPR_ORDER,
    TBLPR_ORDER,
    TBLCELLMAR_ORDER,
    TRPR_ORDER,
    TCPR_ORDER,
    SECTPR_ORDER,
    SCHEMA_ORDERS,
    get_schema_order,
)


# --------------------------------
# Namespace Helpers
# --------------------------------

def qn(prefixed_tag: str) -> str:

    if not prefixed_tag:
        return ""  # Return empty value for missing tag

    if prefixed_tag.startswith("{"):
        return prefixed_tag  # Already in Clark notation

    if ":" in prefixed_tag:
        prefix, local = prefixed_tag.split(":", 1)  # Split prefix and local name

        if prefix in NAMESPACES:
            return f"{{{NAMESPACES[prefix]}}}{local}"  # Convert to Clark notation

    return prefixed_tag  # Return unchanged when namespace is unknown


def de_qn(clark_tag: str) -> str:

    if not clark_tag:
        return ""  # Return empty value for missing tag

    if clark_tag.startswith("{") and "}" in clark_tag:
        uri, local = clark_tag[1:].split("}", 1)  # Extract URI and local name

        prefix = REVERSE_NAMESPACES.get(uri)  # Find namespace prefix

        if prefix:
            return f"{prefix}:{local}"  # Convert to prefixed tag

        return local  # Return local name for unknown namespace

    return clark_tag  # Return unchanged when not in Clark notation


def local_name(tag: str) -> str:

    if not tag:
        return ""  # Return empty value for missing tag

    if "}" in tag:
        return tag.split("}", 1)[1]  # Extract local name from Clark notation

    if ":" in tag:
        return tag.split(":", 1)[1]  # Extract local name from prefixed tag

    return tag  # Return tag when no namespace is present


# --------------------------------
# Base Handler
# --------------------------------

class BaseHandler(ABC):

    # --------------------------------
    # Namespace Access
    # --------------------------------

    @classmethod
    def get_namespace(
        cls,
        prefix: str,
    ) -> str:

        return NAMESPACES.get(
            prefix,
            "",
        )  # Get namespace URI from configuration


    @classmethod
    def ns(
        cls,
        prefix: str,
    ) -> str:

        return NAMESPACES.get(
            prefix,
            "",
        )  # Get namespace URI from configuration


    # --------------------------------
    # Namespace Constants
    # --------------------------------

    W_NS = NAMESPACES.get("w", "")  # WordprocessingML namespace
    R_NS = NAMESPACES.get("r", "")  # Relationship namespace
    WP_NS = NAMESPACES.get("wp", "")  # Word Drawing namespace
    A_NS = NAMESPACES.get("a", "")  # DrawingML namespace
    PIC_NS = NAMESPACES.get("pic", "")  # Picture namespace
    REL_NS = NAMESPACES.get("rel", "")  # Package relationship namespace


    # --------------------------------
    # Handler Interface
    # --------------------------------

    @abstractmethod
    def to_json(
        self,
        element: ET.Element,
    ) -> dict[str, Any]:
        pass


    @abstractmethod
    def to_xml(
        self,
        data: dict[str, Any],
    ) -> ET.Element:
        pass


    # --------------------------------
    # XML & Namespace Helpers
    # --------------------------------

    @staticmethod
    def qn(
        prefixed_tag: str,
    ) -> str:

        return qn(prefixed_tag)  # Qualify tag using configured namespace


    @staticmethod
    def de_qn(
        clark_tag: str,
    ) -> str:

        return de_qn(clark_tag)  # Convert Clark tag to prefixed tag


    @staticmethod
    def local_name(
        tag: str,
    ) -> str:

        return local_name(tag)  # Extract local element name


    @staticmethod
    def tag_to_name(
        xml_tag: str,
        default: str | None = None,
    ) -> str:

        return tag_to_name(
            xml_tag,
            default,
        )  # Convert XML tag to JSON name


    @staticmethod
    def name_to_tag(
        json_name: str,
        default: str | None = None,
    ) -> str:

        return name_to_tag(
            json_name,
            default,
        )  # Convert JSON name to XML tag


    # --------------------------------
    # Schema Ordering Helpers
    # --------------------------------

    @staticmethod
    def get_schema_order(
        element_name: str,
    ) -> list[str]:

        return get_schema_order(element_name)  # Get schema ordering from configuration


    @classmethod
    def sort_children_by_schema(
        cls,
        parent: ET.Element,
        schema_order: list[str] | str,
    ) -> None:

        if isinstance(schema_order, str):
            schema_order = get_schema_order(schema_order)

        sort_children_by_schema(
            parent,
            schema_order,
        )  # Sort children by configured schema order


# --------------------------------
# XML Schema Ordering
# --------------------------------

def sort_children_by_schema(
    parent: ET.Element,
    schema_order: list[str],
) -> None:

    if parent is None or len(parent) <= 1:
        return  # Nothing to sort

    order_map = {
        name: index
        for index, name in enumerate(schema_order)
    }  # Create schema order lookup

    sorted_children = sorted(
        list(parent),
        key=lambda element: order_map.get(
            local_name(element.tag),
            999,
        ),
    )  # Sort children according to schema order

    parent[:] = sorted_children  # Replace children with sorted elements


# --------------------------------
# Public API
# --------------------------------

__all__ = [
    "BaseHandler",
    "qn",
    "de_qn",
    "local_name",
    "sort_children_by_schema",
    "NAMESPACES",
    "REVERSE_NAMESPACES",
    "tag_to_name",
    "name_to_tag",
    "PPR_ORDER",
    "RPR_ORDER",
    "TBLPR_ORDER",
    "TBLCELLMAR_ORDER",
    "TRPR_ORDER",
    "TCPR_ORDER",
    "SECTPR_ORDER",
    "SCHEMA_ORDERS",
    "get_schema_order",
]