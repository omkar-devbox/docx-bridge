"""Command line interface and entrypoint for docx-engine."""

import argparse
import sys
from pathlib import Path

from docx.reader import DocxReader
from docx.writer import DocxWriter
from parser.xml_to_json import XmlToJsonParser
from parser.json_to_xml import JsonToXmlParser
from utils.json import dump_json, load_json


def docx_to_json(docx_path: Path, output_path: Path) -> None:
    """Convert a .docx file to JSON representation."""
    with DocxReader(docx_path) as reader:
        parser = XmlToJsonParser()
        doc_xml = reader.get_document_xml()
        data = parser.parse_document(doc_xml)

        styles_xml = reader.get_styles_xml()
        if styles_xml:
            data["styles"] = parser.parse_styles(styles_xml)

        numbering_xml = reader.get_numbering_xml()
        if numbering_xml:
            data["numbering"] = parser.parse_numbering(numbering_xml)

        rels_xml = reader.get_relationships_xml()
        if rels_xml:
            data["relationships"] = parser.parse_relationships(rels_xml)

        media = reader.get_media()
        if media:
            from handlers.media import MediaHandler
            data["media"] = MediaHandler.media_map_to_json(media)

        dump_json(data, output_path)
        print(f"Successfully converted '{docx_path}' -> '{output_path}'")


def json_to_docx(json_path: Path, output_path: Path, template_docx: Path | None = None) -> None:
    """Convert JSON representation back to a .docx file."""
    data = load_json(json_path)
    parser = JsonToXmlParser()

    # Automatically check if a matching template docx exists next to json file
    if template_docx is None:
        candidate = json_path.with_suffix(".docx")
        if candidate.exists() and candidate.resolve() != output_path.resolve():
            template_docx = candidate

    # Reconstruct or update archive
    with DocxWriter(output_path) as writer:
        copied_parts: set[str] = set()
        if template_docx and template_docx.exists():
            with DocxReader(template_docx) as reader:
                for part_name in reader.list_parts():
                    if part_name not in ("word/document.xml", "word/styles.xml", "word/numbering.xml", "word/_rels/document.xml.rels") and not part_name.startswith("word/media/"):
                        writer.write_part(part_name, reader.read_part(part_name))
                        copied_parts.add(part_name)
        else:
            # Add standard OPC root relationships
            root_rels = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                '  <Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="word/document.xml"/>\n'
                '</Relationships>'
            )
            writer.write_part("_rels/.rels", root_rels)

            # Add standard [Content_Types].xml
            content_types_lines = [
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
                '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                '  <Default Extension="xml" ContentType="application/xml"/>',
                '  <Default Extension="png" ContentType="image/png"/>',
                '  <Default Extension="jpeg" ContentType="image/jpeg"/>',
                '  <Default Extension="jpg" ContentType="image/jpeg"/>',
                '  <Default Extension="gif" ContentType="image/gif"/>',
                '  <Default Extension="emf" ContentType="image/x-emf"/>',
                '  <Default Extension="wmf" ContentType="image/x-wmf"/>',
                '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
            ]
            if "styles" in data:
                content_types_lines.append(
                    '  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                )
            if "numbering" in data:
                content_types_lines.append(
                    '  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                )
            content_types_lines.append('</Types>')
            writer.write_part("[Content_Types].xml", "\n".join(content_types_lines))

        doc_xml_bytes = parser.build_document_xml(data)
        writer.write_part("word/document.xml", doc_xml_bytes)

        if "styles" in data:
            styles_xml_bytes = parser.build_styles_xml(data["styles"])
            writer.write_part("word/styles.xml", styles_xml_bytes)

        if "numbering" in data:
            num_xml_bytes = parser.build_numbering_xml(data["numbering"])
            writer.write_part("word/numbering.xml", num_xml_bytes)

        media_targets: set[str] = set()
        if "media" in data:
            from handlers.media import MediaHandler
            raw_media = MediaHandler.media_map_to_bytes(data["media"])
            for part_name, content_bytes in raw_media.items():
                writer.write_part(part_name, content_bytes)
                rel_target = part_name[5:] if part_name.startswith("word/") else part_name
                media_targets.add(rel_target)

        if "relationships" in data:
            raw_rels = data["relationships"]
            # If no template was used, filter out internal relationships targeting non-existent parts
            if not template_docx:
                filtered_rels = []
                for rel in raw_rels:
                    target = rel.get("target", "")
                    if rel.get("targetMode") == "External":
                        filtered_rels.append(rel)
                    elif target in media_targets or f"media/{target}" in media_targets:
                        filtered_rels.append(rel)
                    elif target == "styles.xml" and "styles" in data:
                        filtered_rels.append(rel)
                    elif target == "numbering.xml" and "numbering" in data:
                        filtered_rels.append(rel)
                    elif f"word/{target}" in copied_parts or target in copied_parts:
                        filtered_rels.append(rel)
                rels_bytes = parser.build_relationships_xml(filtered_rels)
            else:
                rels_bytes = parser.build_relationships_xml(raw_rels)
            writer.write_part("word/_rels/document.xml.rels", rels_bytes)

        print(f"Successfully converted '{json_path}' -> '{output_path}'")



def main() -> None:
    """Parse CLI arguments and execute commands."""
    parser = argparse.ArgumentParser(
        prog="docx-engine",
        description="Convert DOCX files to structured JSON and back."
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # docx-to-json command
    to_json_cmd = subparsers.add_parser("docx-to-json", help="Convert .docx to .json")
    to_json_cmd.add_argument("input", type=Path, help="Path to source .docx file")
    to_json_cmd.add_argument("-o", "--output", type=Path, required=True, help="Path to output .json file")

    # json-to-docx command
    to_docx_cmd = subparsers.add_parser("json-to-docx", help="Convert .json to .docx")
    to_docx_cmd.add_argument("input", type=Path, help="Path to source .json file")
    to_docx_cmd.add_argument("-o", "--output", type=Path, required=True, help="Path to output .docx file")
    to_docx_cmd.add_argument("-t", "--template", type=Path, default=None, help="Optional template .docx file")

    args = parser.parse_args()

    if args.command == "docx-to-json":
        docx_to_json(args.input, args.output)
    elif args.command == "json-to-docx":
        json_to_docx(args.input, args.output, args.template)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
