"""Main entry point for docx-engine CLI and public API re-exports."""

from cli import create_parser, main
from converter import (
    doc_to_json,
    docx_to_json,
    ensure_numbering,
    extract_all_items,
    has_list_or_numbering,
    json_to_doc,
    json_to_docx,
)

# Backward-compatible aliases for internal helpers
_ensure_numbering = ensure_numbering
_extract_all_items = extract_all_items
_has_list_or_numbering = has_list_or_numbering

__all__ = [
    "docx_to_json",
    "json_to_docx",
    "doc_to_json",
    "json_to_doc",
    "main",
    "create_parser",
    "_ensure_numbering",
    "_extract_all_items",
    "_has_list_or_numbering",
]


if __name__ == "__main__":
    main()