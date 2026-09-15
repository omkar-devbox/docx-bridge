"""DOCX converter package: bidirectional DOCX and JSON translation."""

from .docx_to_json import docx_to_json
from .json_to_docx import json_to_docx
from .numbering import ensure_numbering, extract_all_items, has_list_or_numbering

# Aliases
to_json = docx_to_json
to_docx = json_to_docx

__all__ = [
    "docx_to_json",
    "json_to_docx",
    "to_json",
    "to_docx",
    "ensure_numbering",
    "extract_all_items",
    "has_list_or_numbering",
]
