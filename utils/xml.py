import xml.etree.ElementTree as ET


# -------------------------------------------------
# Parse XML Bytes
# -------------------------------------------------

def parse_xml_bytes(xml_bytes):

    # Convert XML bytes into an XML root element.
    try:
        return ET.fromstring(xml_bytes)

    except ET.ParseError as error:
        print(f"XML parsing error: {error}")
        return None


# -------------------------------------------------
# Convert XML Element to String
# -------------------------------------------------

def element_to_string(element):

    # Return an empty string for an invalid element.
    if element is None:
        return ""

    # Convert the XML element into a UTF-8 string.
    try:
        return ET.tostring(
            element,
            encoding="utf-8",
        ).decode("utf-8")

    except (TypeError, ValueError) as error:
        print(f"Error converting element to string: {error}")
        return ""


# -------------------------------------------------
# Parse XML String or Bytes
# -------------------------------------------------

def parse_xml_string(xml_content):
    """Parse XML string or bytes into an ElementTree Element."""
    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8")
    return ET.fromstring(xml_content)


# -------------------------------------------------
# Serialize XML Element to Bytes
# -------------------------------------------------

def serialize_xml(element, encoding="utf-8", xml_declaration=True):
    """Serialize an ElementTree Element to XML bytes."""
    if element is None:
        return b""
    return ET.tostring(
        element,
        encoding=encoding,
        xml_declaration=xml_declaration,
    )