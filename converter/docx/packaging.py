"""Open Packaging Conventions (OPC) package construction and relationship helpers."""

from pathlib import Path
from typing import Any

from formats.docx.reader import DocxReader
from formats.docx.writer import DocxWriter
from parser.docx.xml_to_json import XmlToJsonParser


def build_root_relationships(has_metadata: bool = True) -> str:
    """Return standard root .rels XML content."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        '  <Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>',
    ]
    if has_metadata:
        lines.append(
            '  <Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/>'
        )
        lines.append(
            '  <Relationship Id="rId3" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
            'Target="docProps/app.xml"/>'
        )
    lines.append('</Relationships>')
    return '\n'.join(lines)


def build_content_types_xml(
    data: dict[str, Any],
    extra_parts: list[str] | None = None,
) -> str:
    """Return standard [Content_Types].xml content based on data elements and written parts."""
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

    # Core & extended properties
    content_types_lines.append(
        '  <Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    )
    content_types_lines.append(
        '  <Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    )

    # Settings
    content_types_lines.append(
        '  <Override PartName="/word/settings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
    )
    content_types_lines.append(
        '  <Override PartName="/word/webSettings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.webSettings+xml"/>'
    )

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

    if "footnotes" in data:
        content_types_lines.append(
            '  <Override PartName="/word/footnotes.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
        )

    if "endnotes" in data:
        content_types_lines.append(
            '  <Override PartName="/word/endnotes.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml"/>'
        )

    if "comments" in data:
        content_types_lines.append(
            '  <Override PartName="/word/comments.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
        )

    # Extra parts like headers/footers
    if extra_parts:
        for part in extra_parts:
            clean_part = "/" + part.lstrip("/")
            if "header" in part and part.endswith(".xml"):
                content_types_lines.append(
                    f'  <Override PartName="{clean_part}" '
                    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
                )
            elif "footer" in part and part.endswith(".xml"):
                content_types_lines.append(
                    f'  <Override PartName="{clean_part}" '
                    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                )

    content_types_lines.append("</Types>")
    return "\n".join(content_types_lines)


def copy_template_parts(
    template_docx: Path,
    writer: DocxWriter,
    exclude_parts: set[str] | None = None,
) -> set[str]:
    """Copy non-generated parts from a template DOCX archive into writer."""
    copied_parts: set[str] = set()
    excludes = exclude_parts or set()

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
                and part_name not in excludes
                and not part_name.startswith("word/media/")
            ):
                writer.write_part(
                    part_name,
                    reader.read_part(part_name),
                )
                copied_parts.add(part_name)

    return copied_parts


def merge_template_relationships(
    template_docx: Path,
    rels_list: list[dict[str, Any]],
) -> None:
    """Preserve internal relationships (theme, settings, fonts) from template archive."""
    with DocxReader(template_docx) as reader:
        template_rels_xml = reader.get_relationships_xml()
        if not template_rels_xml:
            return

        template_rels = XmlToJsonParser().parse_relationships(
            template_rels_xml,
            mode="raw",
        )

        existing_rids = {
            str(rel.get("id"))
            for rel in rels_list
        }
        existing_targets = {
            rel.get("target")
            for rel in rels_list
        }

        for template_rel in template_rels:
            template_id = str(template_rel.get("id"))
            target = template_rel.get("target", "")
            rel_type = template_rel.get("type", "")

            if (
                template_id not in existing_rids
                and target not in existing_targets
                and (
                    target
                    in (
                        "theme/theme1.xml",
                        "settings.xml",
                        "webSettings.xml",
                        "fontTable.xml",
                        "styles.xml",
                        "numbering.xml",
                    )
                    or "theme" in rel_type
                    or "settings" in rel_type
                    or "fontTable" in rel_type
                    or "webSettings" in rel_type
                    or "styles" in rel_type
                    or "numbering" in rel_type
                    or target.startswith("../customXml")
                )
            ):
                rels_list.append(template_rel)
                existing_rids.add(template_id)
                existing_targets.add(target)


def ensure_package_relationships(
    rels_list: list[dict[str, Any]],
    data: dict[str, Any],
) -> None:
    """Ensure numbering, styles, settings, and notes relationships exist in rels_list if required."""
    existing_targets = {rel.get("target", "") for rel in rels_list}

    used_ids: set[int] = set()
    for rel in rels_list:
        rel_id = str(rel.get("id", ""))
        if rel_id.startswith("rId") and rel_id[3:].isdigit():
            used_ids.add(int(rel_id[3:]))

    next_rid_num = max(used_ids, default=0) + 1

    def add_rel(rel_type_suffix: str, target: str) -> None:
        nonlocal next_rid_num
        if target not in existing_targets:
            rels_list.append(
                {
                    "id": f"rId{next_rid_num}",
                    "type": f"http://schemas.openxmlformats.org/officeDocument/2006/relationships/{rel_type_suffix}",
                    "target": target,
                }
            )
            existing_targets.add(target)
            next_rid_num += 1

    if "numbering" in data:
        add_rel("numbering", "numbering.xml")

    if "styles" in data:
        add_rel("styles", "styles.xml")

    if "footnotes" in data:
        add_rel("footnotes", "footnotes.xml")

    if "endnotes" in data:
        add_rel("endnotes", "endnotes.xml")

    if "comments" in data:
        add_rel("comments", "comments.xml")

    # Header and footer relationships
    if "headers" in data:
        hdrs = data["headers"]
        if isinstance(hdrs, dict):
            for name in hdrs:
                target = name[5:] if name.startswith("word/") else name
                if not target.startswith("header"):
                    target = f"header_{target}"
                if not target.endswith(".xml"):
                    target = f"{target}.xml"
                add_rel("header", target)
        elif isinstance(hdrs, list):
            for idx, h_item in enumerate(hdrs, 1):
                target = h_item.get("target") or f"header{idx}.xml"
                add_rel("header", target)

    if "footers" in data:
        ftrs = data["footers"]
        if isinstance(ftrs, dict):
            for name in ftrs:
                target = name[5:] if name.startswith("word/") else name
                if not target.startswith("footer"):
                    target = f"footer_{target}"
                if not target.endswith(".xml"):
                    target = f"{target}.xml"
                add_rel("footer", target)
        elif isinstance(ftrs, list):
            for idx, f_item in enumerate(ftrs, 1):
                target = f_item.get("target") or f"footer{idx}.xml"
                add_rel("footer", target)

    # Standard settings for document compatibility
    add_rel("settings", "settings.xml")
    add_rel("webSettings", "webSettings.xml")


def filter_standalone_relationships(
    rels_list: list[dict[str, Any]],
    data: dict[str, Any],
    media_targets: set[str],
    copied_parts: set[str],
    extra_targets: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Filter relationship list for standalone documents without a template."""
    filtered_rels: list[dict[str, Any]] = []
    extras = extra_targets or set()

    for rel in rels_list:
        target = rel.get("target", "")

        if rel.get("targetMode") == "External":
            filtered_rels.append(rel)

        elif target in media_targets or f"media/{target}" in media_targets:
            filtered_rels.append(rel)

        elif target in extras or f"word/{target}" in extras:
            filtered_rels.append(rel)

        elif target == "styles.xml" and "styles" in data:
            filtered_rels.append(rel)

        elif target == "numbering.xml" and "numbering" in data:
            filtered_rels.append(rel)

        elif target in ("settings.xml", "webSettings.xml"):
            filtered_rels.append(rel)

        elif target == "footnotes.xml" and "footnotes" in data:
            filtered_rels.append(rel)

        elif target == "endnotes.xml" and "endnotes" in data:
            filtered_rels.append(rel)

        elif target == "comments.xml" and "comments" in data:
            filtered_rels.append(rel)

        elif target.startswith("header") or target.startswith("footer"):
            filtered_rels.append(rel)

        elif (
            f"word/{target}" in copied_parts
            or target in copied_parts
        ):
            filtered_rels.append(rel)

    return filtered_rels
