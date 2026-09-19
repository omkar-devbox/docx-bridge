"""Utility functions for XML and JSON processing."""

from .common.json import dump_json, load_json, save_json

__all__ = [
    "dump_json",
    "element_to_string",
    "load_json",
    "parse_xml_bytes",
    "parse_xml_string",
    "save_json",
    "serialize_xml",
]


def __getattr__(name: str):
    if name in (
        "element_to_string",
        "parse_xml_bytes",
        "parse_xml_string",
        "serialize_xml",
    ):
        from .docx import xml
        return getattr(xml, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
