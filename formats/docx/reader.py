# --------------------------------
# Imports
# --------------------------------

import zipfile
from pathlib import Path
from typing import BinaryIO


# --------------------------------
# DOCX Reader
# --------------------------------

class DocxReader:

    def __init__(self, source: str | Path | BinaryIO):
        self.source = source
        self.archive = zipfile.ZipFile(
            source,
            "r",
        )

    # --------------------------------
    # Package Parts
    # --------------------------------

    def list_parts(self) -> list[str]:
        return self.archive.namelist()

    def read_part(self, part_name: str) -> bytes:
        return self.archive.read(part_name)

    def read_xml_part(self, part_name: str) -> str:
        return self.archive.read(part_name).decode("utf-8")

    # --------------------------------
    # Main Document
    # --------------------------------

    def get_document_xml(self) -> str:
        return self.read_xml_part(
            "word/document.xml",
        )

    # --------------------------------
    # Styles
    # --------------------------------

    def get_styles_xml(self) -> str | None:
        part_name = "word/styles.xml"

        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    # --------------------------------
    # Numbering
    # --------------------------------

    def get_numbering_xml(self) -> str | None:
        part_name = "word/numbering.xml"

        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    # --------------------------------
    # Relationships
    # --------------------------------

    def get_relationships_xml(self) -> str | None:
        part_name = "word/_rels/document.xml.rels"

        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    # --------------------------------
    # Media
    # --------------------------------

    def get_media(self) -> dict[str, bytes]:
        media: dict[str, bytes] = {}

        for name in self.archive.namelist():
            if name.startswith("word/media/"):
                media[name] = self.archive.read(name)

        return media

    # --------------------------------
    # Headers & Footers
    # --------------------------------

    def get_headers_xml(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        for name in self.archive.namelist():
            if name.startswith("word/header") and name.endswith(".xml"):
                headers[name] = self.read_xml_part(name)
        return headers

    def get_footers_xml(self) -> dict[str, str]:
        footers: dict[str, str] = {}
        for name in self.archive.namelist():
            if name.startswith("word/footer") and name.endswith(".xml"):
                footers[name] = self.read_xml_part(name)
        return footers

    # --------------------------------
    # Document Metadata
    # --------------------------------

    def get_core_properties_xml(self) -> str | None:
        part_name = "docProps/core.xml"
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_app_properties_xml(self) -> str | None:
        part_name = "docProps/app.xml"
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Footnotes & Endnotes
    # --------------------------------

    def get_footnotes_xml(self) -> str | None:
        part_name = "word/footnotes.xml"
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_endnotes_xml(self) -> str | None:
        part_name = "word/endnotes.xml"
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Comments
    # --------------------------------

    def get_comments_xml(self) -> str | None:
        part_name = "word/comments.xml"
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Settings
    # --------------------------------

    def get_settings_xml(self) -> str | None:
        part_name = "word/settings.xml"
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_web_settings_xml(self) -> str | None:
        part_name = "word/webSettings.xml"
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Archive Lifecycle
    # --------------------------------

    def close(self) -> None:
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        self.close()