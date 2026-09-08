"""Configuration module loading namespaces and master-tag mappings from JSON."""

from pathlib import Path
import xml.etree.ElementTree as ET
from utils.json import load_json

_CONFIG_DIR = Path(__file__).resolve().parent
NAMESPACES_FILE = _CONFIG_DIR / "namespaces.json"
MASTER_TAGS_FILE = _CONFIG_DIR / "master-tags.json"


def load_namespaces(filepath: Path | str | None = None) -> dict[str, str]:
    """Load namespace mappings from namespaces.json and flatten categories into prefix->uri dict."""
    path = Path(filepath) if filepath else NAMESPACES_FILE
    data = load_json(path)
    namespaces: dict[str, str] = {}

    for category, prefixes in data.items():
        if isinstance(prefixes, dict):
            for prefix, uri in prefixes.items():
                namespaces[prefix] = uri

    return namespaces


def load_master_tags(
    filepath: Path | str | None = None,
) -> tuple[dict[str, str], dict[str, str], dict[str, dict[str, str]]]:
    """Load master tags from master-tags.json.

    Returns:
        (xml_to_json_map, json_to_xml_map, categories_map)
    """
    path = Path(filepath) if filepath else MASTER_TAGS_FILE
    data = load_json(path)
    xml_to_json: dict[str, str] = {}
    json_to_xml: dict[str, str] = {}
    categories: dict[str, dict[str, str]] = {}

    for category, tags in data.items():
        if isinstance(tags, dict):
            categories[category] = tags
            for xml_tag, json_name in tags.items():
                xml_to_json[xml_tag] = json_name
                # Avoid overwriting existing reverse mapping if already present
                if json_name not in json_to_xml:
                    json_to_xml[json_name] = xml_tag

    return xml_to_json, json_to_xml, categories


# -------------------------------------------------
# Module-level cached mappings
# -------------------------------------------------
NAMESPACES: dict[str, str] = load_namespaces()
REVERSE_NAMESPACES: dict[str, str] = {uri: prefix for prefix, uri in NAMESPACES.items()}
XML_TO_JSON_TAGS, JSON_TO_XML_TAGS, TAG_CATEGORIES = load_master_tags()

# Register all namespaces with ElementTree for clean XML serialization
for prefix, uri in NAMESPACES.items():
    try:
        ET.register_namespace(prefix, uri)
    except (ValueError, KeyError):
        pass


def tag_to_name(xml_tag: str, default: str | None = None) -> str:
    """Convert an XML tag (prefixed 'w:p' or Clark '{uri}p') to a readable JSON name using master-tags.json."""
    if not xml_tag:
        return default or ""

    # If in Clark notation, resolve to prefixed tag
    if xml_tag.startswith("{") and "}" in xml_tag:
        uri, local = xml_tag[1:].split("}", 1)
        prefix = REVERSE_NAMESPACES.get(uri)
        if prefix:
            xml_tag = f"{prefix}:{local}"
        else:
            xml_tag = local

    return XML_TO_JSON_TAGS.get(xml_tag, default if default is not None else xml_tag)


def name_to_tag(json_name: str, default: str | None = None) -> str:
    """Convert a readable JSON name back to an XML tag (e.g. 'paragraph' -> 'w:p') using master-tags.json."""
    return JSON_TO_XML_TAGS.get(json_name, default if default is not None else json_name)


def get_tags_for_category(category: str) -> dict[str, str]:
    """Retrieve all tag mappings for a specific category (e.g. 'style', 'content', 'table')."""
    return TAG_CATEGORIES.get(category, {})


__all__ = [
    "load_namespaces",
    "load_master_tags",
    "NAMESPACES",
    "REVERSE_NAMESPACES",
    "XML_TO_JSON_TAGS",
    "JSON_TO_XML_TAGS",
    "TAG_CATEGORIES",
    "tag_to_name",
    "name_to_tag",
    "get_tags_for_category",
]
