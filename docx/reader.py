"""DOCX package reader extracting XML parts, media, and relationships from a .docx file."""

import zipfile
from pathlib import Path
from typing import BinaryIO


class DocxReader:
    """Extracts internal components from a .docx OpenXML archive."""

    def __init__(self, source: str | Path | BinaryIO):
        self.source = source
        self.archive = zipfile.ZipFile(source, "r")

    def list_parts(self) -> list[str]:
        """List all parts (file paths) inside the docx package."""
        return self.archive.namelist()

    def read_part(self, part_name: str) -> bytes:
        """Read the raw bytes of a specific part."""
        return self.archive.read(part_name)

    def read_xml_part(self, part_name: str) -> str:
        """Read a specific XML part as a UTF-8 string."""
        return self.archive.read(part_name).decode("utf-8")

    def get_document_xml(self) -> str:
        """Read word/document.xml from the archive."""
        return self.read_xml_part("word/document.xml")

    def get_styles_xml(self) -> str | None:
        """Read word/styles.xml if present."""
        if "word/styles.xml" in self.archive.namelist():
            return self.read_xml_part("word/styles.xml")
        return None

    def get_numbering_xml(self) -> str | None:
        """Read word/numbering.xml if present."""
        if "word/numbering.xml" in self.archive.namelist():
            return self.read_xml_part("word/numbering.xml")
        return None

    def get_relationships_xml(self) -> str | None:
        """Read word/_rels/document.xml.rels if present."""
        if "word/_rels/document.xml.rels" in self.archive.namelist():
            return self.read_xml_part("word/_rels/document.xml.rels")
        return None

    def get_media(self) -> dict[str, bytes]:
        """Read all embedded media assets from the archive."""
        media: dict[str, bytes] = {}
        for name in self.archive.namelist():
            if name.startswith("word/media/"):
                media[name] = self.archive.read(name)
        return media


    def close(self) -> None:
        """Close the zip archive."""
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
