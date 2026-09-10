# --------------------------------
# Imports
# --------------------------------

from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from utils.json import load_json


# --------------------------------
# Configuration Directory
# --------------------------------

_CONFIG_DIR = Path(__file__).resolve().parent


# --------------------------------
# Configuration Files
# --------------------------------

NAMESPACES_FILE = _CONFIG_DIR / "namespaces.json"  # Namespace mappings
MASTER_TAGS_FILE = _CONFIG_DIR / "master-tags.json"  # Master tag mappings
RELATIONSHIPS_FILE = _CONFIG_DIR / "relationships.json"  # Relationship mappings
CONTENT_TYPES_FILE = _CONFIG_DIR / "content-types.json"  # Content type mappings
DOCX_CONFIG_FILE = _CONFIG_DIR / "docx.json"  # DOCX configuration
PAGE_SIZES_FILE = _CONFIG_DIR / "page-sizes.json"  # Page size definitions


# --------------------------------
# Configuration Data
# --------------------------------

NAMESPACES_DATA: dict[str, dict[str, str]] = load_json(NAMESPACES_FILE)  # Loaded namespaces
MASTER_TAGS_DATA: dict[str, dict[str, str]] = load_json(MASTER_TAGS_FILE)  # Loaded master tags
RELATIONSHIPS_DATA: dict[str, Any] = load_json(RELATIONSHIPS_FILE)  # Loaded relationships
CONTENT_TYPES_DATA: dict[str, Any] = load_json(CONTENT_TYPES_FILE)  # Loaded content types
DOCX_CONFIG_DATA: dict[str, Any] = load_json(DOCX_CONFIG_FILE)  # Loaded DOCX configuration
PAGE_SIZES_DATA: dict[str, Any] = load_json(PAGE_SIZES_FILE)  # Loaded page sizes


# --------------------------------
# Namespace Helpers
# --------------------------------

def _flatten_namespaces(
    data: dict[str, dict[str, str]],
) -> dict[str, str]:

    namespaces: dict[str, str] = {}

    for category, prefixes in data.items():
        if isinstance(prefixes, dict):
            for prefix, uri in prefixes.items():
                namespaces[prefix] = uri  # Store prefix to URI mapping

    return namespaces


# --------------------------------
# Master Tag Helpers
# --------------------------------

def _process_master_tags(
    data: dict[str, dict[str, str]],
) -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, dict[str, str]],
]:

    xml_to_json: dict[str, str] = {}
    json_to_xml: dict[str, str] = {}
    categories: dict[str, dict[str, str]] = {}

    for category, tags in data.items():
        if isinstance(tags, dict):
            categories[category] = tags  # Store category mappings

            for xml_tag, json_name in tags.items():
                xml_to_json[xml_tag] = json_name  # Store XML to JSON mapping

                if json_name not in json_to_xml:
                    json_to_xml[json_name] = xml_tag  # Store first reverse mapping

    return xml_to_json, json_to_xml, categories


# --------------------------------
# Namespace Loading
# --------------------------------

def load_namespaces(
    filepath: Path | str | None = None,
) -> dict[str, str]:

    if filepath is not None:
        data = load_json(Path(filepath))  # Load custom namespace file
        return _flatten_namespaces(data)

    return _flatten_namespaces(NAMESPACES_DATA)  # Use default namespace data


# --------------------------------
# Master Tag Loading
# --------------------------------

def load_master_tags(
    filepath: Path | str | None = None,
) -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, dict[str, str]],
]:

    if filepath is not None:
        data = load_json(Path(filepath))  # Load custom master tag file
        return _process_master_tags(data)

    return _process_master_tags(MASTER_TAGS_DATA)  # Use default master tags


# --------------------------------
# Relationship Loading
# --------------------------------

def load_relationships(
    filepath: Path | str | None = None,
) -> dict[str, Any]:

    if filepath is not None:
        return load_json(Path(filepath))  # Load custom relationships

    return RELATIONSHIPS_DATA  # Use default relationships


# --------------------------------
# Content Type Loading
# --------------------------------

def load_content_types(
    filepath: Path | str | None = None,
) -> dict[str, Any]:

    if filepath is not None:
        return load_json(Path(filepath))  # Load custom content types

    return CONTENT_TYPES_DATA  # Use default content types


# --------------------------------
# DOCX Configuration Loading
# --------------------------------

def load_docx_config(
    filepath: Path | str | None = None,
) -> dict[str, Any]:

    if filepath is not None:
        return load_json(Path(filepath))  # Load custom DOCX configuration

    return DOCX_CONFIG_DATA  # Use default DOCX configuration


# --------------------------------
# Page Size Loading
# --------------------------------

def load_page_sizes(
    filepath: Path | str | None = None,
) -> dict[str, Any]:

    if filepath is not None:
        return load_json(Path(filepath))  # Load custom page sizes

    return PAGE_SIZES_DATA  # Use default page sizes


# --------------------------------
# Cached Mappings & Configurations
# --------------------------------

NAMESPACES: dict[str, str] = load_namespaces()  # Cached namespace mappings

REVERSE_NAMESPACES: dict[str, str] = {
    uri: prefix
    for prefix, uri in NAMESPACES.items()
}  # URI to prefix lookup

XML_TO_JSON_TAGS, JSON_TO_XML_TAGS, TAG_CATEGORIES = load_master_tags()  # Cached tag mappings

XML_DECLARATION: str = DOCX_CONFIG_DATA.get(
    "xml_declaration",
    "",
)  # XML declaration header

PACKAGE_RELATIONSHIPS_NS: str = RELATIONSHIPS_DATA.get(
    "namespaces", {}
).get(
    "package",
    "",
)  # Package relationships namespace

DOCUMENT_RELATIONSHIPS_NS: str = RELATIONSHIPS_DATA.get(
    "namespaces", {}
).get(
    "document",
    "",
)  # Document relationships namespace

RELATIONSHIP_TYPES: dict[str, str] = RELATIONSHIPS_DATA.get(
    "types",
    {},
)  # Relationship types map

INTERNAL_PLUMBING_TARGETS: set[str] = set(
    RELATIONSHIPS_DATA.get("internal_plumbing_targets", [])
)  # Internal plumbing targets set


# --------------------------------
# Schema Ordering & Properties
# --------------------------------

SCHEMA_ORDERS: dict[str, list[str]] = DOCX_CONFIG_DATA.get(
    "schema_orders",
    {},
)

PPR_ORDER: list[str] = SCHEMA_ORDERS.get("pPr", [])
RPR_ORDER: list[str] = SCHEMA_ORDERS.get("rPr", [])
TBLPR_ORDER: list[str] = SCHEMA_ORDERS.get("tblPr", [])
TBLCELLMAR_ORDER: list[str] = SCHEMA_ORDERS.get("tblCellMar", [])
TRPR_ORDER: list[str] = SCHEMA_ORDERS.get("trPr", [])
TCPR_ORDER: list[str] = SCHEMA_ORDERS.get("tcPr", [])
SECTPR_ORDER: list[str] = SCHEMA_ORDERS.get("sectPr", [])

STYLE_PROPS: set[str] = set(
    DOCX_CONFIG_DATA.get("style_properties", [])
)

_DEFAULTS: dict[str, Any] = DOCX_CONFIG_DATA.get("defaults", {})
DEFAULT_PAGE_WIDTH: int = int(_DEFAULTS.get("page_width", 11906))
DEFAULT_PAGE_HEIGHT: int = int(_DEFAULTS.get("page_height", 16838))
DEFAULT_ORIENTATION: str = str(_DEFAULTS.get("orientation", "portrait"))
DEFAULT_MARGINS: dict[str, int] = dict(DOCX_CONFIG_DATA.get("default_margins", {}))

# Page size dimensions to name mapping: (width, height) -> "a4"
PAGE_SIZES: dict[tuple[int, int], str] = {
    tuple(map(int, k.split(","))): v
    for k, v in PAGE_SIZES_DATA.get("dimensions_map", {}).items()
}

# Page size name to dimensions mapping: "a4" -> (width, height)
PAGE_SIZE_MAP: dict[str, tuple[int, int]] = {
    k: (int(v["width"]), int(v["height"]))
    for k, v in PAGE_SIZES_DATA.get("standard", {}).items()
    if isinstance(v, dict) and "width" in v and "height" in v
}


# --------------------------------
# XML Namespace Registration
# --------------------------------

for prefix, uri in NAMESPACES.items():
    try:
        ET.register_namespace(prefix, uri)  # Register namespace for XML serialization
    except (ValueError, KeyError):
        pass  # Ignore invalid namespace registration


# --------------------------------
# Tag Conversion
# --------------------------------

def tag_to_name(
    xml_tag: str,
    default: str | None = None,
) -> str:

    if not xml_tag:
        return default or ""  # Return fallback for empty tags

    if xml_tag.startswith("{") and "}" in xml_tag:
        uri, local = xml_tag[1:].split("}", 1)  # Extract URI and local name

        prefix = REVERSE_NAMESPACES.get(uri)  # Find namespace prefix

        if prefix:
            xml_tag = f"{prefix}:{local}"  # Convert to prefixed XML tag
        else:
            xml_tag = local  # Use local name when prefix is unknown

    return XML_TO_JSON_TAGS.get(
        xml_tag,
        default if default is not None else xml_tag,
    )  # Return mapped JSON name


def name_to_tag(
    json_name: str,
    default: str | None = None,
) -> str:

    return JSON_TO_XML_TAGS.get(
        json_name,
        default if default is not None else json_name,
    )  # Return mapped XML tag


# --------------------------------
# Tag Categories
# --------------------------------

def get_tags_for_category(
    category: str,
) -> dict[str, str]:

    return TAG_CATEGORIES.get(category, {})  # Return category tag mappings


def get_schema_order(
    element_name: str,
) -> list[str]:

    return SCHEMA_ORDERS.get(element_name, [])


# --------------------------------
# Public API
# --------------------------------

__all__ = [
    "NAMESPACES_DATA",
    "MASTER_TAGS_DATA",
    "RELATIONSHIPS_DATA",
    "CONTENT_TYPES_DATA",
    "DOCX_CONFIG_DATA",
    "PAGE_SIZES_DATA",
    "NAMESPACES_FILE",
    "MASTER_TAGS_FILE",
    "RELATIONSHIPS_FILE",
    "CONTENT_TYPES_FILE",
    "DOCX_CONFIG_FILE",
    "PAGE_SIZES_FILE",
    "load_namespaces",
    "load_master_tags",
    "load_relationships",
    "load_content_types",
    "load_docx_config",
    "load_page_sizes",
    "NAMESPACES",
    "REVERSE_NAMESPACES",
    "XML_TO_JSON_TAGS",
    "JSON_TO_XML_TAGS",
    "TAG_CATEGORIES",
    "XML_DECLARATION",
    "PACKAGE_RELATIONSHIPS_NS",
    "DOCUMENT_RELATIONSHIPS_NS",
    "RELATIONSHIP_TYPES",
    "INTERNAL_PLUMBING_TARGETS",
    "SCHEMA_ORDERS",
    "PPR_ORDER",
    "RPR_ORDER",
    "TBLPR_ORDER",
    "TBLCELLMAR_ORDER",
    "TRPR_ORDER",
    "TCPR_ORDER",
    "SECTPR_ORDER",
    "STYLE_PROPS",
    "DEFAULT_PAGE_WIDTH",
    "DEFAULT_PAGE_HEIGHT",
    "DEFAULT_ORIENTATION",
    "DEFAULT_MARGINS",
    "PAGE_SIZES",
    "PAGE_SIZE_MAP",
    "tag_to_name",
    "name_to_tag",
    "get_tags_for_category",
    "get_schema_order",
]