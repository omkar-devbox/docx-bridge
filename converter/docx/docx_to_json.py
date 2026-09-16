"""DOCX to JSON conversion pipeline."""

from pathlib import Path
from typing import Any

from formats.docx.reader import DocxReader
from parser.docx.xml_to_json import XmlToJsonParser
from utils.common.json import dump_json


def docx_to_json(
    docx_path: Path | str,
    output_path: Path | str,
    mode: str = "simple",
) -> None:
    """Convert a DOCX package to structured JSON format."""
    docx_path = Path(docx_path)
    output_path = Path(output_path)

    with DocxReader(docx_path) as reader:
        parser = XmlToJsonParser()

        # Parse main document
        doc_xml = reader.get_document_xml()
        data = parser.parse_document(doc_xml, mode=mode)

        # Parse and merge styles
        styles_xml = reader.get_styles_xml()
        if styles_xml:
            parsed_styles_data = parser.parse_styles(styles_xml)

            if isinstance(parsed_styles_data, dict):
                existing_styles = data.get("styles", {})
                file_styles = parsed_styles_data.get(
                    "styles",
                    parsed_styles_data,
                )

                merged_styles: dict[str, Any] = {}

                if isinstance(file_styles, list):
                    for item in file_styles:
                        if isinstance(item, dict) and "id" in item:
                            merged_styles[item["id"]] = item

                elif isinstance(file_styles, dict):
                    merged_styles = dict(file_styles)

                # Preserve styles already parsed from document
                if isinstance(existing_styles, dict):
                    for key, value in existing_styles.items():
                        if key not in merged_styles:
                            merged_styles[key] = value

                if merged_styles:
                    data["styles"] = merged_styles

                if (
                    "defaults" in parsed_styles_data
                    and "defaults" not in data
                ):
                    data["defaults"] = parsed_styles_data["defaults"]

                if (
                    "latentStyles" in parsed_styles_data
                    and "latentStyles" not in data
                ):
                    data["latentStyles"] = parsed_styles_data["latentStyles"]

        # Parse numbering
        numbering_xml = reader.get_numbering_xml()
        if numbering_xml:
            data["numbering"] = parser.parse_numbering(numbering_xml)

        # Parse relationships
        rels_xml = reader.get_relationships_xml()
        if rels_xml:
            parsed_rels = parser.parse_relationships(
                rels_xml,
                mode=mode,
            )

            if parsed_rels:
                key = "relations" if mode == "simple" else "relationships"
                data[key] = parsed_rels

        # Parse media
        media = reader.get_media()
        if media:
            from handlers.docx.media import MediaHandler

            data["media"] = MediaHandler.media_map_to_json(media)

        # Parse metadata (core & app properties)
        core_xml = reader.get_core_properties_xml()
        app_xml = reader.get_app_properties_xml()
        if core_xml or app_xml:
            metadata = parser.parse_metadata(core_xml, app_xml)
            if metadata:
                data["metadata"] = metadata

        # Parse headers
        headers_xml = reader.get_headers_xml()
        if headers_xml:
            data["headers"] = {
                part_name: parser.parse_header(xml, simple=(mode == "simple"))
                for part_name, xml in headers_xml.items()
            }

        # Parse footers
        footers_xml = reader.get_footers_xml()
        if footers_xml:
            data["footers"] = {
                part_name: parser.parse_footer(xml, simple=(mode == "simple"))
                for part_name, xml in footers_xml.items()
            }

        # Parse footnotes
        footnotes_xml = reader.get_footnotes_xml()
        if footnotes_xml:
            footnotes = parser.parse_footnotes(footnotes_xml, simple=(mode == "simple"))
            if footnotes:
                data["footnotes"] = footnotes

        # Parse endnotes
        endnotes_xml = reader.get_endnotes_xml()
        if endnotes_xml:
            endnotes = parser.parse_endnotes(endnotes_xml, simple=(mode == "simple"))
            if endnotes:
                data["endnotes"] = endnotes

        # Parse comments
        comments_xml = reader.get_comments_xml()
        if comments_xml:
            comments = parser.parse_comments(comments_xml, simple=(mode == "simple"))
            if comments:
                data["comments"] = comments

        # Parse settings
        settings_xml = reader.get_settings_xml()
        if settings_xml:
            settings = parser.parse_settings(settings_xml)
            if settings:
                data["settings"] = settings

        dump_json(data, output_path)

        print(
            f"Successfully converted "
            f"'{docx_path}' -> '{output_path}'"
        )
