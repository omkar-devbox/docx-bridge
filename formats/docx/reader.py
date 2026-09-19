# --------------------------------
# Imports
# --------------------------------

import fnmatch
import zipfile
from pathlib import Path
from typing import Any, BinaryIO

from config import (
    APP_PROPERTIES_PART,
    COMMENTS_EXTENDED_PART,
    COMMENTS_IDS_PART,
    COMMENTS_PART,
    CONTENT_TYPES_DATA,
    CONTENT_TYPES_PART,
    CORE_PROPERTIES_PART,
    CUSTOM_PROPERTIES_PART,
    DOCX_CONFIG_DATA,
    DOCUMENT_PART,
    DOCUMENT_RELATIONSHIPS_PART,
    ENDNOTES_PART,
    FONTS_PART,
    FOOTERS_PATTERN,
    FOOTNOTES_PART,
    GLOSSARY_PART,
    HEADERS_PATTERN,
    MEDIA_DIR,
    NUMBERING_PART,
    PACKAGE_RELATIONSHIPS_PART,
    SETTINGS_PART,
    STYLES_PART,
    THEME_PART,
    WEB_SETTINGS_PART,
)


# --------------------------------
# DOCX Reader
# --------------------------------

class DocxReader:

    def __init__(
        self,
        source: str | Path | BinaryIO,
        docx_config: dict[str, Any] | None = None,
        content_types_config: dict[str, Any] | None = None,
    ):
        self.source = source
        self.archive = zipfile.ZipFile(
            source,
            "r",
        )
        self.docx_config: dict[str, Any] = docx_config if docx_config is not None else DOCX_CONFIG_DATA
        self.content_types_config: dict[str, Any] = content_types_config if content_types_config is not None else CONTENT_TYPES_DATA

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
        part_name = (
            self.content_types_config.get("document")
            or self.docx_config.get("root_part")
            or DOCUMENT_PART
        )
        return self.read_xml_part(part_name)

    # --------------------------------
    # Styles
    # --------------------------------

    def get_styles_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("styles")
            or STYLES_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    # --------------------------------
    # Numbering
    # --------------------------------

    def get_numbering_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("numbering")
            or NUMBERING_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    # --------------------------------
    # Relationships
    # --------------------------------

    def get_relationships_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("document_relationships")
            or self.docx_config.get("document_relationships_part")
            or DOCUMENT_RELATIONSHIPS_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    def get_package_relationships_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("other", {}).get("package_relationships")
            or PACKAGE_RELATIONSHIPS_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    # --------------------------------
    # Content Types
    # --------------------------------

    def get_content_types_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("other", {}).get("content_types")
            or CONTENT_TYPES_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)

        return None

    # --------------------------------
    # Media
    # --------------------------------

    def get_media(self) -> dict[str, bytes]:
        media_dir = (
            self.content_types_config.get("media_dir")
            or self.docx_config.get("media_dir")
            or MEDIA_DIR
        )
        media: dict[str, bytes] = {}

        for name in self.archive.namelist():
            if name.startswith(media_dir):
                media[name] = self.archive.read(name)

        return media

    # --------------------------------
    # Headers & Footers
    # --------------------------------

    def get_headers_xml(self) -> dict[str, str]:
        pattern = (
            self.content_types_config.get("headers")
            or HEADERS_PATTERN
        )
        headers: dict[str, str] = {}
        for name in self.archive.namelist():
            if fnmatch.fnmatch(name, pattern):
                headers[name] = self.read_xml_part(name)
        return headers

    def get_footers_xml(self) -> dict[str, str]:
        pattern = (
            self.content_types_config.get("footers")
            or FOOTERS_PATTERN
        )
        footers: dict[str, str] = {}
        for name in self.archive.namelist():
            if fnmatch.fnmatch(name, pattern):
                footers[name] = self.read_xml_part(name)
        return footers

    # --------------------------------
    # Document Metadata
    # --------------------------------

    def get_core_properties_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("core_properties")
            or CORE_PROPERTIES_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_app_properties_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("app_properties")
            or APP_PROPERTIES_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_custom_properties_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("custom_properties")
            or CUSTOM_PROPERTIES_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Footnotes & Endnotes
    # --------------------------------

    def get_footnotes_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("footnotes")
            or FOOTNOTES_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_endnotes_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("endnotes")
            or ENDNOTES_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Comments
    # --------------------------------

    def get_comments_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("comments")
            or COMMENTS_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_comments_extended_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("comments_extended")
            or COMMENTS_EXTENDED_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_comments_ids_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("comments_ids")
            or COMMENTS_IDS_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Settings
    # --------------------------------

    def get_settings_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("settings")
            or SETTINGS_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_web_settings_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("web_settings")
            or WEB_SETTINGS_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    # --------------------------------
    # Fonts, Themes & Glossary
    # --------------------------------

    def get_font_table_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("fonts")
            or FONTS_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_theme_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("theme")
            or THEME_PART
        )
        if part_name in self.archive.namelist():
            return self.read_xml_part(part_name)
        return None

    def get_glossary_xml(self) -> str | None:
        part_name = (
            self.content_types_config.get("glossary")
            or GLOSSARY_PART
        )
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