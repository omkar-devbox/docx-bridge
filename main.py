# --------------------------------
# Imports
# --------------------------------

import argparse
import sys
from pathlib import Path
from typing import Any

from docx.reader import DocxReader
from docx.writer import DocxWriter
from parser.json_to_xml import JsonToXmlParser
from parser.xml_to_json import XmlToJsonParser
from utils.json import dump_json, load_json


# --------------------------------
# DOCX -> JSON
# --------------------------------

def docx_to_json(
    docx_path: Path | str,
    output_path: Path | str,
    mode: str = "simple",
) -> None:
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
            from handlers.media import MediaHandler

            data["media"] = MediaHandler.media_map_to_json(media)

        dump_json(data, output_path)

        print(
            f"Successfully converted "
            f"'{docx_path}' -> '{output_path}'"
        )


# --------------------------------
# Content Helpers
# --------------------------------

def _extract_all_items(
    data: dict[str, Any] | list[Any],
) -> list[Any]:
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    items: list[Any] = []

    # Section-based document
    sections = data.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue

            content = section.get(
                "content",
                section.get("children", []),
            )

            if isinstance(content, list):
                items.extend(content)

        return items

    # Body-based document
    body = data.get("body")

    if isinstance(body, dict):
        content = body.get("content", [])

        if isinstance(content, list):
            items.extend(content)

    elif isinstance(body, list):
        items.extend(body)

    # Direct content
    elif isinstance(data.get("content"), list):
        items.extend(data["content"])

    return items


def _has_list_or_numbering(
    data: dict[str, Any],
) -> bool:
    all_items = _extract_all_items(data)

    if not all_items:
        return False

    def check_item(item: Any) -> bool:
        if not isinstance(item, dict):
            return False

        item_type = item.get("type")

        if item_type in (
            "bullet",
            "list_item",
            "listItem",
            "list",
        ):
            return True

        if any(
            item.get(key)
            for key in (
                "bullet",
                "list",
                "numbering",
                "numbered",
                "number",
            )
        ):
            return True

        if isinstance(item.get("items"), list):
            return True

        rows = item.get("rows")

        if isinstance(rows, list):
            for row in rows:

                # Row represented as a list
                if isinstance(row, list):
                    for cell in row:
                        if check_item(cell):
                            return True

                        if (
                            isinstance(cell, dict)
                            and isinstance(cell.get("content"), list)
                        ):
                            for sub_item in cell["content"]:
                                if check_item(sub_item):
                                    return True

                # Row represented as a dictionary
                elif isinstance(row, dict):
                    cells = row.get("cells")

                    if isinstance(cells, list):
                        for cell in cells:
                            if check_item(cell):
                                return True

        return False

    for item in all_items:
        if check_item(item):
            return True

    return False


# --------------------------------
# Numbering Provisioning
# --------------------------------

def _ensure_numbering(
    data: dict[str, Any],
) -> None:
    if not _has_list_or_numbering(data):
        return

    from handlers.numbering import NumberingHandler

    # Create default numbering when missing
    if "numbering" not in data or not data["numbering"]:
        data["numbering"] = (
            NumberingHandler.build_default_numbering()
        )

    elif (
        isinstance(data["numbering"], dict)
        and not data["numbering"].get("abstractNumbering")
    ):
        data["numbering"] = (
            NumberingHandler.build_default_numbering()
        )

    num_dict = data["numbering"]

    if not isinstance(num_dict, dict):
        return

    abstract_list = num_dict.setdefault(
        "abstractNumbering",
        [],
    )

    instance_list = num_dict.setdefault(
        "numbering",
        [],
    )

    used_abs_ids = {
        int(item["id"])
        for item in abstract_list
        if isinstance(item, dict)
        and str(item.get("id", "")).isdigit()
    }

    used_num_ids = {
        int(item["numId"])
        for item in instance_list
        if isinstance(item, dict)
        and str(item.get("numId", "")).isdigit()
    }

    symbol_to_num_id: dict[str, int] = {}

    def process_item(item: Any) -> None:
        if not isinstance(item, dict):
            return

        # Detect custom bullet/list symbol
        raw_symbol = None

        if (
            "bullet" in item
            and item["bullet"] not in (False, None)
        ):
            bullet_value = item["bullet"]

            if isinstance(bullet_value, dict):
                raw_symbol = (
                    bullet_value.get("icon")
                    or bullet_value.get("style")
                    or bullet_value.get("type")
                    or bullet_value.get("format")
                )

            elif not isinstance(bullet_value, bool):
                raw_symbol = str(bullet_value)

        elif (
            "list" in item
            and item["list"] not in (False, None)
        ):
            list_value = item["list"]

            if isinstance(list_value, dict):
                raw_symbol = (
                    list_value.get("icon")
                    or list_value.get("style")
                    or list_value.get("type")
                    or list_value.get("format")
                )

            elif not isinstance(list_value, bool):
                raw_symbol = str(list_value)

        if raw_symbol:
            known_id = NumberingHandler.get_known_preset_id(
                raw_symbol
            )

            # Register custom bullet symbol
            if known_id is None:
                if raw_symbol not in symbol_to_num_id:
                    next_id = (
                        max(
                            used_num_ids | used_abs_ids,
                            default=0,
                        )
                        + 1
                    )

                    used_abs_ids.add(next_id)
                    used_num_ids.add(next_id)

                    abstract_list.append(
                        NumberingHandler.build_custom_bullet_abstract_num(
                            raw_symbol,
                            next_id,
                        )
                    )

                    instance_list.append(
                        {
                            "numId": str(next_id),
                            "abstractNumId": str(next_id),
                        }
                    )

                    symbol_to_num_id[raw_symbol] = next_id

                custom_id = symbol_to_num_id[raw_symbol]
                level = item.get("level", 0)

                item["numbering"] = {
                    "id": custom_id,
                    "level": level,
                }

        # Process table rows/cells recursively
        rows = item.get("rows")

        if not isinstance(rows, list):
            return

        for row in rows:

            # Row as list
            if isinstance(row, list):
                for cell in row:
                    process_item(cell)

                    if (
                        isinstance(cell, dict)
                        and isinstance(cell.get("content"), list)
                    ):
                        for sub_item in cell["content"]:
                            process_item(sub_item)

            # Row as dictionary
            elif isinstance(row, dict):
                cells = row.get("cells")

                if not isinstance(cells, list):
                    continue

                for cell in cells:
                    process_item(cell)

                    if (
                        isinstance(cell, dict)
                        and isinstance(cell.get("content"), list)
                    ):
                        for sub_item in cell["content"]:
                            process_item(sub_item)

    for item in _extract_all_items(data):
        process_item(item)


# --------------------------------
# JSON -> DOCX
# --------------------------------

def json_to_docx(
    json_path: Path | str,
    output_path: Path | str,
    template_docx: Path | str | None = None,
) -> None:
    json_path = Path(json_path)
    output_path = Path(output_path)

    if template_docx is not None:
        template_docx = Path(template_docx)

    data = load_json(json_path)
    parser = JsonToXmlParser()

    # Automatically use matching DOCX template
    if template_docx is None:
        candidate = json_path.with_suffix(".docx")

        if (
            candidate.exists()
            and candidate.resolve() != output_path.resolve()
        ):
            template_docx = candidate

    # Ensure numbering exists before XML generation
    _ensure_numbering(data)

    # Build DOCX archive
    with DocxWriter(output_path) as writer:
        copied_parts: set[str] = set()

        # Copy non-generated template parts
        if template_docx and template_docx.exists():
            with DocxReader(template_docx) as reader:
                for part_name in reader.list_parts():
                    if (
                        part_name
                        not in (
                            "word/document.xml",
                            "word/styles.xml",
                            "word/numbering.xml",
                            "word/_rels/document.xml.rels",
                        )
                        and not part_name.startswith("word/media/")
                    ):
                        writer.write_part(
                            part_name,
                            reader.read_part(part_name),
                        )
                        copied_parts.add(part_name)

        else:
            # Standard OPC root relationships
            root_rels = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                '  <Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="word/document.xml"/>\n'
                '</Relationships>'
            )

            writer.write_part(
                "_rels/.rels",
                root_rels,
            )

            # Standard content types
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
                '  <Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
            ]

            if "styles" in data:
                content_types_lines.append(
                    '  <Override PartName="/word/styles.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                )

            if "numbering" in data:
                content_types_lines.append(
                    '  <Override PartName="/word/numbering.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                )

            content_types_lines.append("</Types>")

            writer.write_part(
                "[Content_Types].xml",
                "\n".join(content_types_lines),
            )

        # --------------------------------
        # Document XML
        # --------------------------------

        doc_xml_bytes = parser.build_document_xml(data)

        writer.write_part(
            "word/document.xml",
            doc_xml_bytes,
        )

        # --------------------------------
        # Styles XML
        # --------------------------------

        if "styles" in data:
            styles_dict: dict[str, Any] = {
                "styles": data["styles"],
            }

            if "defaults" in data:
                styles_dict["defaults"] = data["defaults"]

            if "latentStyles" in data:
                styles_dict["latentStyles"] = data["latentStyles"]

            styles_xml_bytes = parser.build_styles_xml(
                styles_dict
            )

            writer.write_part(
                "word/styles.xml",
                styles_xml_bytes,
            )

        # --------------------------------
        # Numbering XML
        # --------------------------------

        if "numbering" in data:
            numbering_xml_bytes = parser.build_numbering_xml(
                data["numbering"]
            )

            writer.write_part(
                "word/numbering.xml",
                numbering_xml_bytes,
            )

        # --------------------------------
        # Media
        # --------------------------------

        media_targets: set[str] = set()

        if "media" in data:
            from handlers.media import MediaHandler

            raw_media = MediaHandler.media_map_to_bytes(
                data["media"]
            )

            for part_name, content_bytes in raw_media.items():
                writer.write_part(
                    part_name,
                    content_bytes,
                )

                rel_target = (
                    part_name[5:]
                    if part_name.startswith("word/")
                    else part_name
                )

                media_targets.add(rel_target)

        # --------------------------------
        # Relationships
        # --------------------------------

        raw_rels = (
            data.get("relations")
            if "relations" in data
            else data.get("relationships", [])
        )

        rels_list: list[dict[str, Any]] = []

        if isinstance(raw_rels, dict):
            for rel_id, rel_value in raw_rels.items():
                if isinstance(rel_value, dict):
                    entry = dict(rel_value)
                    entry.setdefault("id", rel_id)
                    rels_list.append(entry)

        elif isinstance(raw_rels, list):
            rels_list = [
                dict(rel)
                for rel in raw_rels
                if isinstance(rel, dict)
            ]

        # Preserve template internal relationships
        if template_docx and template_docx.exists():
            with DocxReader(template_docx) as reader:
                template_rels_xml = (
                    reader.get_relationships_xml()
                )

                if template_rels_xml:
                    template_rels = (
                        XmlToJsonParser().parse_relationships(
                            template_rels_xml,
                            mode="raw",
                        )
                    )

                    existing_rids = {
                        str(rel.get("id"))
                        for rel in rels_list
                    }

                    for template_rel in template_rels:
                        template_id = str(
                            template_rel.get("id")
                        )

                        target = template_rel.get(
                            "target",
                            "",
                        )

                        rel_type = template_rel.get(
                            "type",
                            "",
                        )

                        if (
                            template_id not in existing_rids
                            and (
                                target
                                in (
                                    "theme/theme1.xml",
                                    "settings.xml",
                                    "webSettings.xml",
                                    "fontTable.xml",
                                )
                                or "theme" in rel_type
                                or "settings" in rel_type
                                or "fontTable" in rel_type
                                or "webSettings" in rel_type
                                or target.startswith("../customXml")
                            )
                        ):
                            rels_list.append(template_rel)
                            existing_rids.add(template_id)

        has_numbering_rel = any(
            rel.get("target") == "numbering.xml"
            for rel in rels_list
        )

        has_styles_rel = any(
            rel.get("target") == "styles.xml"
            for rel in rels_list
        )

        # Find next relationship ID
        used_ids: set[int] = set()

        for rel in rels_list:
            rel_id = str(rel.get("id", ""))

            if (
                rel_id.startswith("rId")
                and rel_id[3:].isdigit()
            ):
                used_ids.add(int(rel_id[3:]))

        next_rid_num = max(
            used_ids,
            default=0,
        ) + 1

        # Add numbering relationship
        if "numbering" in data and not has_numbering_rel:
            rels_list.append(
                {
                    "id": f"rId{next_rid_num}",
                    "type": (
                        "http://schemas.openxmlformats.org/"
                        "officeDocument/2006/relationships/numbering"
                    ),
                    "target": "numbering.xml",
                }
            )

            next_rid_num += 1

        # Add styles relationship
        if "styles" in data and not has_styles_rel:
            rels_list.append(
                {
                    "id": f"rId{next_rid_num}",
                    "type": (
                        "http://schemas.openxmlformats.org/"
                        "officeDocument/2006/relationships/styles"
                    ),
                    "target": "styles.xml",
                }
            )

            next_rid_num += 1

        # Write relationships only when required
        if rels_list:
            if not template_docx:
                filtered_rels: list[dict[str, Any]] = []

                for rel in rels_list:
                    target = rel.get("target", "")

                    if rel.get("targetMode") == "External":
                        filtered_rels.append(rel)

                    elif target in media_targets:
                        filtered_rels.append(rel)

                    elif f"media/{target}" in media_targets:
                        filtered_rels.append(rel)

                    elif (
                        target == "styles.xml"
                        and "styles" in data
                    ):
                        filtered_rels.append(rel)

                    elif (
                        target == "numbering.xml"
                        and "numbering" in data
                    ):
                        filtered_rels.append(rel)

                    elif (
                        f"word/{target}" in copied_parts
                        or target in copied_parts
                    ):
                        filtered_rels.append(rel)

                rels_bytes = parser.build_relationships_xml(
                    filtered_rels
                )

            else:
                rels_bytes = parser.build_relationships_xml(
                    rels_list
                )

            writer.write_part(
                "word/_rels/document.xml.rels",
                rels_bytes,
            )

        print(
            f"Successfully converted "
            f"'{json_path}' -> '{output_path}'"
        )


# --------------------------------
# CLI
# --------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="docx-engine",
        description="Convert DOCX files to structured JSON and back.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Sub-commands",
    )

    # --------------------------------
    # DOCX -> JSON Command
    # --------------------------------

    to_json_cmd = subparsers.add_parser(
        "docx-to-json",
        help="Convert .docx to .json",
    )

    to_json_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .docx file",
    )

    to_json_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .json file",
    )

    to_json_cmd.add_argument(
        "-m",
        "--mode",
        choices=["simple", "raw"],
        default="simple",
        help=(
            "Output mode: 'simple' for concise AI-friendly JSON, "
            "'raw' for detailed OpenXML mapping "
            "(default: simple)"
        ),
    )

    # --------------------------------
    # JSON -> DOCX Command
    # --------------------------------

    to_docx_cmd = subparsers.add_parser(
        "json-to-docx",
        help="Convert .json to .docx",
    )

    to_docx_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .json file",
    )

    to_docx_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .docx file",
    )

    to_docx_cmd.add_argument(
        "-t",
        "--template",
        type=Path,
        default=None,
        help="Optional template .docx file",
    )

    # --------------------------------
    # Execute Command
    # --------------------------------

    args = parser.parse_args()

    if args.command == "docx-to-json":
        docx_to_json(
            args.input,
            args.output,
            mode=args.mode,
        )

    elif args.command == "json-to-docx":
        json_to_docx(
            args.input,
            args.output,
            args.template,
        )

    else:
        parser.print_help()
        sys.exit(1)


# --------------------------------
# Entry Point
# --------------------------------

if __name__ == "__main__":
    main()