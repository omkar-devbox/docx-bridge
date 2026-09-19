from typing import Any
import xml.etree.ElementTree as ET


DEFAULT_XML_ENCODING: str = "utf-8"
DEFAULT_XML_DECL: str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def _get_docx_config() -> dict[str, Any]:
    """Retrieve DOCX settings from active configuration."""
    try:
        from config import DOCX_CONFIG_DATA
        return DOCX_CONFIG_DATA
    except (ImportError, AttributeError):
        return {}


def _get_default_encoding() -> str:
    """Retrieve default text encoding from configuration."""
    try:
        from config import DEFAULT_ENCODING
        return DEFAULT_ENCODING
    except (ImportError, AttributeError):
        return DEFAULT_XML_ENCODING


# --------------------------------
# Parse XML Bytes
# --------------------------------

def parse_xml_bytes(
    xml_bytes: bytes,
) -> ET.Element | None:
    """Parse raw XML bytes into an ElementTree Element."""
    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError as error:
        print(f"XML parsing error: {error}")
        return None


# --------------------------------
# Convert XML Element to String
# --------------------------------

def element_to_string(
    element: ET.Element | None,
    encoding: str | None = None,
    docx_config: dict[str, Any] | None = None,
) -> str:
    """Convert an ElementTree Element into an XML string using configuration encoding."""
    if element is None:
        return ""

    cfg = docx_config if docx_config is not None else _get_docx_config()
    enc = encoding or cfg.get("encoding") or _get_default_encoding()

    try:
        return ET.tostring(
            element,
            encoding=enc,
        ).decode(enc)
    except (TypeError, ValueError) as error:
        print(f"Error converting element to string: {error}")
        return ""


# --------------------------------
# Parse XML String or Bytes
# --------------------------------

def parse_xml_string(
    xml_content: str | bytes,
    encoding: str | None = None,
    docx_config: dict[str, Any] | None = None,
) -> ET.Element:
    """Parse an XML string or bytes into an ElementTree Element using configuration encoding."""
    if isinstance(xml_content, str):
        cfg = docx_config if docx_config is not None else _get_docx_config()
        enc = encoding or cfg.get("encoding") or _get_default_encoding()
        xml_content = xml_content.encode(enc)

    return ET.fromstring(xml_content)


# --------------------------------
# Serialize XML Element to Bytes
# --------------------------------

def serialize_xml(
    element: ET.Element | None,
    encoding: str | None = None,
    xml_declaration: bool | str | None = None,
    docx_config: dict[str, Any] | None = None,
) -> bytes:
    """Serialize an ElementTree Element to bytes using configuration encoding and declaration."""
    if element is None:
        return b""

    cfg = docx_config if docx_config is not None else _get_docx_config()
    enc = encoding or cfg.get("encoding") or _get_default_encoding()

    # If an explicit string declaration is provided
    if isinstance(xml_declaration, str):
        body = ET.tostring(element, encoding=enc, xml_declaration=False)
        return xml_declaration.encode(enc) + b"\n" + body

    # If docx_config has custom xml_declaration override and xml_declaration is not False
    if xml_declaration is not False and docx_config is not None and "xml_declaration" in docx_config:
        decl = docx_config["xml_declaration"]
        if isinstance(decl, str) and decl:
            body = ET.tostring(element, encoding=enc, xml_declaration=False)
            return decl.encode(enc) + b"\n" + body

    decl_flag = True if xml_declaration is None else bool(xml_declaration)
    return ET.tostring(
        element,
        encoding=enc,
        xml_declaration=decl_flag,
    )


__all__ = [
    "parse_xml_bytes",
    "element_to_string",
    "parse_xml_string",
    "serialize_xml",
]