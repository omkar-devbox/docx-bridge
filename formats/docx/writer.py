# --------------------------------
# Imports
# --------------------------------

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
    FOOTNOTES_PART,
    GLOSSARY_PART,
    MEDIA_DIR,
    NUMBERING_PART,
    PACKAGE_RELATIONSHIPS_PART,
    SETTINGS_PART,
    STYLES_PART,
    THEME_PART,
    WEB_SETTINGS_PART,
)


# --------------------------------
# DOCX Writer
# --------------------------------

class DocxWriter:

    def __init__(
        self,
        target: str | Path | BinaryIO,
        docx_config: dict[str, Any] | None = None,
        content_types_config: dict[str, Any] | None = None,
    ):
        self.target = target
        self.archive = zipfile.ZipFile(
            target,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        )
        self.docx_config: dict[str, Any] = docx_config if docx_config is not None else DOCX_CONFIG_DATA
        self.content_types_config: dict[str, Any] = content_types_config if content_types_config is not None else CONTENT_TYPES_DATA

    # --------------------------------
    # Generic Write Part
    # --------------------------------

    def write_part(
        self,
        part_name: str,
        content: bytes | str,
    ) -> None:
        if isinstance(content, str):
            content = content.encode("utf-8")

        self.archive.writestr(
            part_name,
            content,
        )

    # --------------------------------
    # Config-Driven Part Writers
    # --------------------------------

    def write_document_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("document")
            or self.docx_config.get("root_part")
            or DOCUMENT_PART
        )
        self.write_part(part_name, content)

    def write_styles_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("styles")
            or STYLES_PART
        )
        self.write_part(part_name, content)

    def write_numbering_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("numbering")
            or NUMBERING_PART
        )
        self.write_part(part_name, content)

    def write_relationships_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("document_relationships")
            or self.docx_config.get("document_relationships_part")
            or DOCUMENT_RELATIONSHIPS_PART
        )
        self.write_part(part_name, content)

    def write_package_relationships_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("other", {}).get("package_relationships")
            or PACKAGE_RELATIONSHIPS_PART
        )
        self.write_part(part_name, content)

    def write_content_types_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("other", {}).get("content_types")
            or CONTENT_TYPES_PART
        )
        self.write_part(part_name, content)

    def write_settings_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("settings")
            or SETTINGS_PART
        )
        self.write_part(part_name, content)

    def write_web_settings_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("web_settings")
            or WEB_SETTINGS_PART
        )
        self.write_part(part_name, content)

    def write_core_properties_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("core_properties")
            or CORE_PROPERTIES_PART
        )
        self.write_part(part_name, content)

    def write_app_properties_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("app_properties")
            or APP_PROPERTIES_PART
        )
        self.write_part(part_name, content)

    def write_custom_properties_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("custom_properties")
            or CUSTOM_PROPERTIES_PART
        )
        self.write_part(part_name, content)

    def write_footnotes_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("footnotes")
            or FOOTNOTES_PART
        )
        self.write_part(part_name, content)

    def write_endnotes_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("endnotes")
            or ENDNOTES_PART
        )
        self.write_part(part_name, content)

    def write_comments_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("comments")
            or COMMENTS_PART
        )
        self.write_part(part_name, content)

    def write_comments_extended_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("comments_extended")
            or COMMENTS_EXTENDED_PART
        )
        self.write_part(part_name, content)

    def write_comments_ids_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("comments_ids")
            or COMMENTS_IDS_PART
        )
        self.write_part(part_name, content)

    def write_font_table_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("fonts")
            or FONTS_PART
        )
        self.write_part(part_name, content)

    def write_theme_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("theme")
            or THEME_PART
        )
        self.write_part(part_name, content)

    def write_glossary_xml(self, content: bytes | str) -> None:
        part_name = (
            self.content_types_config.get("glossary")
            or GLOSSARY_PART
        )
        self.write_part(part_name, content)

    def write_media(self, filename: str, content: bytes) -> str:
        media_dir = (
            self.content_types_config.get("media_dir")
            or self.docx_config.get("media_dir")
            or MEDIA_DIR
        )
        part_name = f"{media_dir.rstrip('/')}/{filename.lstrip('/')}"
        self.write_part(part_name, content)
        return part_name

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