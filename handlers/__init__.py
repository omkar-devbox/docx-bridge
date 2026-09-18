"""Handlers package for document components across DOCX format.

Submodules:
- `handlers.docx`: OpenXML (.docx) handlers
- `handlers.common`: Shared base classes, unit conversions, and helpers
"""

# Subpackage modules
from . import common
from . import docx

# Common exports
from .common import (
    CommonBaseHandler,
    BaseHandlerRegistry,
    dxa_to_pt,
    pt_to_dxa,
    inches_to_dxa,
    dxa_to_inches,
    cm_to_dxa,
    dxa_to_cm,
    emu_to_dxa,
    dxa_to_emu,
    bgr_to_hex,
    hex_to_bgr,
    normalize_hex_color,
    to_number,
    to_bool,
    clean_dict,
    normalize_alignment,
)

# OpenXML (DOCX) handlers & helpers (re-exported at root for backward compatibility)
from .docx import (
    BaseHandler,
    DocxBaseHandler,
    DocumentHandler,
    ParagraphHandler,
    RunHandler,
    TableHandler,
    StylesHandler,
    NumberingHandler,
    SectionsHandler,
    MediaHandler,
    RelationshipsHandler,
    DocxHandlerRegistry,
    HandlerRegistry,
    qn,
    de_qn,
    local_name,
    sort_children_by_schema,
    NAMESPACES,
    XML_TO_JSON_TAGS,
    JSON_TO_XML_TAGS,
    tag_to_name,
    name_to_tag,
    get_tags_for_category,
)

__all__ = [
    # Subpackages
    "common",
    "docx",
    # Common
    "CommonBaseHandler",
    "BaseHandlerRegistry",
    "dxa_to_pt",
    "pt_to_dxa",
    "inches_to_dxa",
    "dxa_to_inches",
    "cm_to_dxa",
    "dxa_to_cm",
    "emu_to_dxa",
    "dxa_to_emu",
    "bgr_to_hex",
    "hex_to_bgr",
    "normalize_hex_color",
    "to_number",
    "to_bool",
    "clean_dict",
    "normalize_alignment",
    # DOCX Handlers
    "BaseHandler",
    "DocxBaseHandler",
    "DocumentHandler",
    "ParagraphHandler",
    "RunHandler",
    "TableHandler",
    "StylesHandler",
    "NumberingHandler",
    "SectionsHandler",
    "MediaHandler",
    "RelationshipsHandler",
    "DocxHandlerRegistry",
    "HandlerRegistry",
    "qn",
    "de_qn",
    "local_name",
    "sort_children_by_schema",
    "NAMESPACES",
    "XML_TO_JSON_TAGS",
    "JSON_TO_XML_TAGS",
    "tag_to_name",
    "name_to_tag",
    "get_tags_for_category",
]

