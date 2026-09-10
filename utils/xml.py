import xml.etree.ElementTree as ET


# --------------------------------
# Parse XML Bytes
# --------------------------------

def parse_xml_bytes(
    xml_bytes: bytes,
) -> ET.Element | None:

    try:
        return ET.fromstring(xml_bytes)  # Parse XML bytes into root element

    except ET.ParseError as error:
        print(f"XML parsing error: {error}")  # Report XML parsing error
        return None


# --------------------------------
# Convert XML Element to String
# --------------------------------

def element_to_string(
    element: ET.Element | None,
) -> str:

    if element is None:
        return ""  # Return empty string for missing element

    try:
        return ET.tostring(
            element,
            encoding="utf-8",
        ).decode("utf-8")  # Convert XML element to UTF-8 string

    except (TypeError, ValueError) as error:
        print(
            f"Error converting element to string: {error}"
        )  # Report conversion error
        return ""


# --------------------------------
# Parse XML String or Bytes
# --------------------------------

def parse_xml_string(
    xml_content: str | bytes,
) -> ET.Element:

    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8")  # Convert string to bytes

    return ET.fromstring(xml_content)  # Parse XML content


# --------------------------------
# Serialize XML Element to Bytes
# --------------------------------

def serialize_xml(
    element: ET.Element | None,
    encoding: str = "utf-8",
    xml_declaration: bool = True,
) -> bytes:

    if element is None:
        return b""  # Return empty bytes for missing element

    return ET.tostring(
        element,
        encoding=encoding,
        xml_declaration=xml_declaration,
    )  # Serialize XML element to bytes