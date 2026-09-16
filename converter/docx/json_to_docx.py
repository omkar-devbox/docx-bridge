"""JSON to DOCX conversion pipeline."""

from pathlib import Path
from typing import Any

from formats.docx.writer import DocxWriter
from parser.docx.json_to_xml import JsonToXmlParser
from utils.common.json import load_json
from .numbering import ensure_numbering
from .packaging import (
    build_content_types_xml,
    build_root_relationships,
    copy_template_parts,
    ensure_package_relationships,
    filter_standalone_relationships,
    merge_template_relationships,
)


def json_to_docx(
    json_path: Path | str,
    output_path: Path | str,
    template_docx: Path | str | None = None,
) -> None:
    """Convert structured JSON back to a DOCX package."""
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
    ensure_numbering(data)

    # Pre-collect extra targets (headers, footers)
    extra_targets: set[str] = set()
    if "headers" in data:
        hdrs = data["headers"]
        if isinstance(hdrs, dict):
            for name in hdrs:
                target = name[5:] if name.startswith("word/") else name
                if not target.startswith("header"):
                    target = f"header_{target}"
                if not target.endswith(".xml"):
                    target = f"{target}.xml"
                extra_targets.add(target)
        elif isinstance(hdrs, list):
            for idx, h_item in enumerate(hdrs, 1):
                extra_targets.add(h_item.get("target") or f"header{idx}.xml")

    if "footers" in data:
        ftrs = data["footers"]
        if isinstance(ftrs, dict):
            for name in ftrs:
                target = name[5:] if name.startswith("word/") else name
                if not target.startswith("footer"):
                    target = f"footer_{target}"
                if not target.endswith(".xml"):
                    target = f"{target}.xml"
                extra_targets.add(target)
        elif isinstance(ftrs, list):
            for idx, f_item in enumerate(ftrs, 1):
                extra_targets.add(f_item.get("target") or f"footer{idx}.xml")

    # Build DOCX archive
    with DocxWriter(output_path) as writer:
        copied_parts: set[str] = set()

        # Parts to exclude from copying if template is used
        exclude_parts: set[str] = set()
        if "metadata" in data:
            exclude_parts.update(["docProps/core.xml", "docProps/app.xml"])
        if "settings" in data:
            exclude_parts.add("word/settings.xml")
        if "footnotes" in data:
            exclude_parts.add("word/footnotes.xml")
        if "endnotes" in data:
            exclude_parts.add("word/endnotes.xml")
        if "comments" in data:
            exclude_parts.add("word/comments.xml")
        for target in extra_targets:
            exclude_parts.add(f"word/{target}")

        # Copy non-generated template parts
        if template_docx and template_docx.exists():
            copied_parts = copy_template_parts(template_docx, writer, exclude_parts=exclude_parts)
        else:
            # Standard OPC root relationships
            writer.write_part(
                "_rels/.rels",
                build_root_relationships(),
            )

            # Standard content types (including any headers/footers)
            extra_content_types = {f"word/{t}" for t in extra_targets}
            writer.write_part(
                "[Content_Types].xml",
                build_content_types_xml(data, extra_parts=extra_content_types),
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
        # Document Properties (Metadata)
        # --------------------------------

        if "metadata" in data or not template_docx:
            meta = data.get("metadata", {})
            if "docProps/core.xml" not in copied_parts:
                writer.write_part(
                    "docProps/core.xml",
                    parser.build_core_properties_xml(meta),
                )
            if "docProps/app.xml" not in copied_parts:
                writer.write_part(
                    "docProps/app.xml",
                    parser.build_app_properties_xml(meta),
                )

        # --------------------------------
        # Settings & WebSettings XML
        # --------------------------------

        if "word/settings.xml" not in copied_parts:
            if "settings" in data or not template_docx:
                writer.write_part(
                    "word/settings.xml",
                    parser.build_settings_xml(data.get("settings")),
                )
        if "word/webSettings.xml" not in copied_parts:
            if "settings" in data or not template_docx:
                writer.write_part(
                    "word/webSettings.xml",
                    parser.build_web_settings_xml(),
                )

        # --------------------------------
        # Headers & Footers
        # --------------------------------

        if "headers" in data:
            hdrs = data["headers"]
            if isinstance(hdrs, dict):
                for name, h_data in hdrs.items():
                    target = name[5:] if name.startswith("word/") else name
                    if not target.startswith("header"):
                        target = f"header_{target}"
                    if not target.endswith(".xml"):
                        target = f"{target}.xml"
                    part_name = f"word/{target}"
                    writer.write_part(part_name, parser.build_header_xml(h_data))
            elif isinstance(hdrs, list):
                for idx, h_data in enumerate(hdrs, 1):
                    target = h_data.get("target") or f"header{idx}.xml"
                    part_name = f"word/{target}"
                    writer.write_part(part_name, parser.build_header_xml(h_data))

        if "footers" in data:
            ftrs = data["footers"]
            if isinstance(ftrs, dict):
                for name, f_data in ftrs.items():
                    target = name[5:] if name.startswith("word/") else name
                    if not target.startswith("footer"):
                        target = f"footer_{target}"
                    if not target.endswith(".xml"):
                        target = f"{target}.xml"
                    part_name = f"word/{target}"
                    writer.write_part(part_name, parser.build_footer_xml(f_data))
            elif isinstance(ftrs, list):
                for idx, f_data in enumerate(ftrs, 1):
                    target = f_data.get("target") or f"footer{idx}.xml"
                    part_name = f"word/{target}"
                    writer.write_part(part_name, parser.build_footer_xml(f_data))

        # --------------------------------
        # Footnotes & Endnotes XML
        # --------------------------------

        if "footnotes" in data and "word/footnotes.xml" not in copied_parts:
            writer.write_part(
                "word/footnotes.xml",
                parser.build_footnotes_xml(data["footnotes"]),
            )

        if "endnotes" in data and "word/endnotes.xml" not in copied_parts:
            writer.write_part(
                "word/endnotes.xml",
                parser.build_endnotes_xml(data["endnotes"]),
            )

        # --------------------------------
        # Comments XML
        # --------------------------------

        if "comments" in data and "word/comments.xml" not in copied_parts:
            writer.write_part(
                "word/comments.xml",
                parser.build_comments_xml(data["comments"]),
            )

        # --------------------------------
        # Media
        # --------------------------------

        media_targets: set[str] = set()

        if "media" in data:
            from handlers.docx.media import MediaHandler

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
            merge_template_relationships(template_docx, rels_list)

        # Add numbering and styles relationships if required
        ensure_package_relationships(rels_list, data)

        # Write relationships only when required
        if rels_list:
            if not template_docx:
                filtered_rels = filter_standalone_relationships(
                    rels_list,
                    data,
                    media_targets,
                    copied_parts,
                    extra_targets=extra_targets,
                )
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
