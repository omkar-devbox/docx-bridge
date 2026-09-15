"""DOC converter package: legacy Word 97-2003 binary format translation."""

from .doc_to_json import doc_to_json
from .json_to_doc import json_to_doc

# Aliases
to_json = doc_to_json
to_doc = json_to_doc

__all__ = [
    "doc_to_json",
    "json_to_doc",
    "to_json",
    "to_doc",
]
