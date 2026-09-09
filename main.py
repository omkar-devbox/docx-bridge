"""Command line interface and entrypoint for docx-engine."""

import argparse
import sys
from pathlib import Path

from docx.reader import DocxReader
from docx.writer import DocxWriter
from parser.xml_to_json import XmlToJsonParser
from parser.json_to_xml import JsonToXmlParser
from utils.json import dump_json, load_json


def docx_to_json(docx_path: Path, output_path: Path, mode: str = "simple") -> None:
    """Convert a .docx file to JSON representation.
    
    Args:
        docx_path: Path to the .docx source file.
        output_path: Path to write the output .json file.
        mode: 'simple' for clean, compact, AI-friendly JSON (default);
              'raw' for full OpenXML schema mapping.
    """
    with DocxReader(docx_path) as reader:
        parser = XmlToJsonParser()
        doc_xml = reader.get_document_xml()
        data = parser.parse_document(doc_xml, mode=mode)

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


def _has_list_or_numbering(data: dict[str, Any]) -> bool:
    """Check whether JSON document contains list, bullet, or numbering elements."""
    body = data.get("body", [])
    if isinstance(body, dict):
        body = body.get("content", [])
    if not isinstance(body, list):
        body = data.get("content", [])
    if not isinstance(body, list):
        return False

    def check_item(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        if item.get("type") in ("bullet", "list_item", "listItem", "list"):
            return True
        if item.get("bullet") or item.get("list") or item.get("numbering") or item.get("numbered") or item.get("number"):
            return True
        if "rows" in item and isinstance(item["rows"], list):
            for row in item["rows"]:
                if isinstance(row, list):
                    for cell in row:
                        if check_item(cell):
                            return True
                        if isinstance(cell, dict) and "content" in cell:
                            for sub in cell.get("content", []):
                                if check_item(sub):
                                    return True
        return False

    for item in body:
        if check_item(item):
            return True
    return False


def json_to_docx(json_path: Path, output_path: Path, template_docx: Path | None = None) -> None:
    """Convert JSON representation back to a .docx file."""
    data = load_json(json_path)
    parser = JsonToXmlParser()

    # Automatically check if a matching template docx exists next to json file
    if template_docx is None:
        candidate = json_path.with_suffix(".docx")
        if candidate.exists() and candidate.resolve() != output_path.resolve():
            template_docx = candidate

    # Auto-provision numbering presets if document uses lists/bullets but has no numbering definition
    if _has_list_or_numbering(data):
        from handlers.numbering import NumberingHandler
        if "numbering" not in data or not data["numbering"]:
            data["numbering"] = NumberingHandler.build_default_numbering()
        elif isinstance(data["numbering"], dict) and not data["numbering"].get("abstractNumbering"):
            data["numbering"] = NumberingHandler.build_default_numbering()

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

        # Ensure document relationships exist and include numbering/styles/media
        rels_list = list(data.get("relationships", []))
        has_num_rel = any(r.get("target") == "numbering.xml" for r in rels_list)
        has_style_rel = any(r.get("target") == "styles.xml" for r in rels_list)

        used_ids = set()
        for r in rels_list:
            rid = str(r.get("id", ""))
            if rid.startswith("rId") and rid[3:].isdigit():
                used_ids.add(int(rid[3:]))
        next_rid_num = max(used_ids, default=0) + 1

        if "numbering" in data and not has_num_rel:
            rels_list.append({
                "id": f"rId{next_rid_num}",
                "type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering",
                "target": "numbering.xml",
            })
            next_rid_num += 1

        if "styles" in data and not has_style_rel:
            rels_list.append({
                "id": f"rId{next_rid_num}",
                "type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
                "target": "styles.xml",
            })
            next_rid_num += 1

        if rels_list:
            if not template_docx:
                filtered_rels = []
                for rel in rels_list:
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
                rels_bytes = parser.build_relationships_xml(rels_list)
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
    to_json_cmd.add_argument(
        "-m", "--mode",
        choices=["simple", "raw"],
        default="simple",
        help="Output mode: 'simple' for concise AI-friendly JSON, 'raw' for detailed OpenXML mapping (default: simple)"
    )

    # json-to-docx command
    to_docx_cmd = subparsers.add_parser("json-to-docx", help="Convert .json to .docx")
    to_docx_cmd.add_argument("input", type=Path, help="Path to source .json file")
    to_docx_cmd.add_argument("-o", "--output", type=Path, required=True, help="Path to output .docx file")
    to_docx_cmd.add_argument("-t", "--template", type=Path, default=None, help="Optional template .docx file")

    args = parser.parse_args()

    if args.command == "docx-to-json":
        docx_to_json(args.input, args.output, mode=args.mode)
    elif args.command == "json-to-docx":
        json_to_docx(args.input, args.output, args.template)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
