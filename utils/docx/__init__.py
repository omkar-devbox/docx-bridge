"""DOCX XML manipulation utilities."""

from .xml import (
    element_to_string,
    parse_xml_bytes,
    parse_xml_string,
    serialize_xml,
)

__all__ = [
    "element_to_string",
    "parse_xml_bytes",
    "parse_xml_string",
    "serialize_xml",
]
