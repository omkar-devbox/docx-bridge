"""DOCX package writer bundling XML parts, media, and relationships into a valid .docx file."""

import zipfile
from pathlib import Path
from typing import BinaryIO


class DocxWriter:
    """Builds a valid .docx OpenXML zip archive from parts."""

    def __init__(self, target: str | Path | BinaryIO):
        self.target = target
        self.archive = zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED)

    def write_part(self, part_name: str, content: bytes | str) -> None:
        """Write raw bytes or string content to a path in the docx package."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.archive.writestr(part_name, content)

    def close(self) -> None:
        """Close the zip archive."""
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
