"""Base handler defining common interfaces, namespaces, and XML/dict helpers."""

from abc import ABC, abstractmethod
from typing import Any
import xml.etree.ElementTree as ET

from config import (
    NAMESPACES,
    REVERSE_NAMESPACES,
    XML_TO_JSON_TAGS,
    JSON_TO_XML_TAGS,
    tag_to_name,
    name_to_tag,
)


def qn(prefixed_tag: str) -> str:
    """Convert prefixed tag (e.g. 'w:p') to Clark notation ('{uri}p') using loaded config."""
    if not prefixed_tag:
        return ""
    if prefixed_tag.startswith("{"):
        return prefixed_tag
    if ":" in prefixed_tag:
        prefix, local = prefixed_tag.split(":", 1)
        if prefix in NAMESPACES:
            return f"{{{NAMESPACES[prefix]}}}{local}"
    return prefixed_tag


def de_qn(clark_tag: str) -> str:
    """Convert Clark notation ('{uri}p') to prefixed tag ('w:p') using loaded config."""
    if not clark_tag:
        return ""
    if clark_tag.startswith("{") and "}" in clark_tag:
        uri, local = clark_tag[1:].split("}", 1)
        prefix = REVERSE_NAMESPACES.get(uri)
        if prefix:
            return f"{prefix}:{local}"
        return local
    return clark_tag


def local_name(tag: str) -> str:
    """Extract local element name without prefix or URI."""
    if not tag:
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    if ":" in tag:
        return tag.split(":", 1)[1]
    return tag


class BaseHandler(ABC):
    """Abstract base class for all DOCX OpenXML handlers."""

    @classmethod
    def get_namespace(cls, prefix: str) -> str:
        """Get namespace URI dynamically from loaded config without hardcoding."""
        return NAMESPACES.get(prefix, "")

    @classmethod
    def ns(cls, prefix: str) -> str:
        """Shorthand to get namespace URI dynamically from loaded config."""
        return NAMESPACES.get(prefix, "")

    # Namespace URIs dynamically retrieved from config (no hardcoded fallback URIs)
    W_NS = NAMESPACES.get("w", "")
    R_NS = NAMESPACES.get("r", "")
    WP_NS = NAMESPACES.get("wp", "")
    A_NS = NAMESPACES.get("a", "")
    PIC_NS = NAMESPACES.get("pic", "")
    REL_NS = NAMESPACES.get("rel", "")

    @abstractmethod
    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert an XML element into a JSON-compatible dictionary."""
        pass

    @abstractmethod
    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert a JSON-compatible dictionary into an XML Element."""
        pass

    @staticmethod
    def qn(prefixed_tag: str) -> str:
        """Helper to qualify a tag."""
        return qn(prefixed_tag)

    @staticmethod
    def de_qn(clark_tag: str) -> str:
        """Helper to de-qualify a tag."""
        return de_qn(clark_tag)

    @staticmethod
    def tag_to_name(xml_tag: str, default: str | None = None) -> str:
        """Map XML tag to readable JSON name using master-tags.json."""
        return tag_to_name(xml_tag, default)

    @staticmethod
    def name_to_tag(json_name: str, default: str | None = None) -> str:
        """Map readable JSON name to XML tag using master-tags.json."""
        return name_to_tag(json_name, default)
