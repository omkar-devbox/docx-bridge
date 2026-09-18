"""Handler for OPC package structure, part resolution, and packaging."""

import io
from typing import Any
import zipfile

from handlers.docx.base import BaseHandler
from handlers.docx.package.content_types import ContentTypesHandler
from handlers.docx.package.relationships import RelationshipsHandler


class PackageHandler(BaseHandler):
    """Handles OPC package structures, parts, and zip bundling."""

    def __init__(
        self,
        content_types_handler: ContentTypesHandler | None = None,
        relationships_handler: RelationshipsHandler | None = None,
    ):
        self.content_types_handler = content_types_handler or ContentTypesHandler()
        self.relationships_handler = relationships_handler or RelationshipsHandler()

    def inspect_parts(self, file_source: str | io.BytesIO) -> list[str]:
        """List all parts contained in a .docx zip package."""
        with zipfile.ZipFile(file_source, "r") as zf:
            return zf.namelist()

    def read_part(self, file_source: str | io.BytesIO, part_name: str) -> bytes | None:
        """Read raw bytes of a specific part from the package."""
        with zipfile.ZipFile(file_source, "r") as zf:
            if part_name in zf.namelist():
                return zf.read(part_name)
        return None

    def to_json(self, file_source: Any) -> dict[str, Any]:
        """Summarize package parts and structure into a JSON AST dictionary."""
        parts = self.inspect_parts(file_source) if isinstance(file_source, (str, io.BytesIO)) else []
        return {
            "type": "package",
            "parts": parts,
        }

    def to_xml(self, data: dict[str, Any]) -> Any:
        """Construct package root content types XML."""
        return self.content_types_handler.to_xml(data)


__all__ = ["PackageHandler"]
