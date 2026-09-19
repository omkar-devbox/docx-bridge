"""Open Packaging Conventions (OPC) package construction and relationship helpers."""

from pathlib import Path
from typing import Any

from config import (
    APP_PROPERTIES_PART,
    COMMENTS_PART,
    CONTENT_TYPES_DATA,
    CONTENT_TYPES_DEFAULTS,
    CONTENT_TYPES_NAMESPACE,
    CONTENT_TYPES_OVERRIDES,
    CONTENT_TYPE_FOOTER,
    CONTENT_TYPE_HEADER,
    CORE_PROPERTIES_PART,
    DOCX_CONFIG_DATA,
    DOCUMENT_PART,
    DOCUMENT_RELATIONSHIPS_NS,
    DOCUMENT_RELATIONSHIPS_PART,
    ENDNOTES_PART,
    FOOTNOTES_PART,
    INTERNAL_PLUMBING_TARGETS,
    MEDIA_DIR,
    NUMBERING_PART,
    PACKAGE_RELATIONSHIPS_NS,
    RELATIONSHIPS_DATA,
    RELATIONSHIP_TYPES,
    SETTINGS_PART,
    STYLES_PART,
    WEB_SETTINGS_PART,
    XML_DECLARATION,
)
from formats.docx.reader import DocxReader
from formats.docx.writer import DocxWriter
from parser.docx.xml_to_json import XmlToJsonParser


def build_root_relationships(
    has_metadata: bool = True,
    relationships_data: dict[str, Any] | None = None,
    content_types_data: dict[str, Any] | None = None,
    docx_config: dict[str, Any] | None = None,
) -> str:
    """Return standard root .rels XML content."""
    xml_decl = (
        (docx_config or DOCX_CONFIG_DATA).get("xml_declaration")
        or XML_DECLARATION
    )
    rels_ns = (
        (relationships_data or RELATIONSHIPS_DATA).get("namespaces", {}).get("package")
        or PACKAGE_RELATIONSHIPS_NS
    )
    rel_types = (relationships_data or RELATIONSHIPS_DATA).get("types", RELATIONSHIP_TYPES)
    ct_data = content_types_data or CONTENT_TYPES_DATA

    doc_target = (
        ct_data.get("document")
        or (docx_config or DOCX_CONFIG_DATA).get("root_part")
        or DOCUMENT_PART
    )
    core_target = ct_data.get("core_properties") or CORE_PROPERTIES_PART
    app_target = ct_data.get("app_properties") or APP_PROPERTIES_PART

    lines = [
        xml_decl,
        f'<Relationships xmlns="{rels_ns}">',
        f'  <Relationship Id="rId1" '
        f'Type="{rel_types.get("officeDocument", "")}" '
        f'Target="{doc_target}"/>',
    ]
    if has_metadata:
        lines.append(
            f'  <Relationship Id="rId2" '
            f'Type="{rel_types.get("coreProperties", "")}" '
            f'Target="{core_target}"/>'
        )
        lines.append(
            f'  <Relationship Id="rId3" '
            f'Type="{rel_types.get("extendedProperties", "")}" '
            f'Target="{app_target}"/>'
        )
    lines.append('</Relationships>')
    return '\n'.join(lines)


def build_content_types_xml(
    data: dict[str, Any],
    extra_parts: list[str] | None = None,
    content_types_data: dict[str, Any] | None = None,
    docx_config: dict[str, Any] | None = None,
) -> str:
    """Return standard [Content_Types].xml content based on data elements and written parts."""
    ct_data = content_types_data or CONTENT_TYPES_DATA
    xml_decl = (
        (docx_config or DOCX_CONFIG_DATA).get("xml_declaration")
        or XML_DECLARATION
    )
    ns = ct_data.get("namespace") or CONTENT_TYPES_NAMESPACE
    defaults = ct_data.get("defaults") or CONTENT_TYPES_DEFAULTS
    overrides = ct_data.get("overrides") or CONTENT_TYPES_OVERRIDES
    header_ct = ct_data.get("content_types", {}).get("header") or CONTENT_TYPE_HEADER
    footer_ct = ct_data.get("content_types", {}).get("footer") or CONTENT_TYPE_FOOTER

    content_types_lines = [
        xml_decl,
        f'<Types xmlns="{ns}">',
    ]

    for ext, ct in defaults.items():
        content_types_lines.append(f'  <Default Extension="{ext}" ContentType="{ct}"/>')

    def add_override(part_name: str) -> None:
        key = "/" + part_name.lstrip("/")
        ct = overrides.get(key)
        if ct:
            content_types_lines.append(
                f'  <Override PartName="{key}" ContentType="{ct}"/>'
            )

    doc_part = (
        ct_data.get("document")
        or (docx_config or DOCX_CONFIG_DATA).get("root_part")
        or DOCUMENT_PART
    )
    core_part = ct_data.get("core_properties") or CORE_PROPERTIES_PART
    app_part = ct_data.get("app_properties") or APP_PROPERTIES_PART
    settings_part = ct_data.get("settings") or SETTINGS_PART
    web_settings_part = ct_data.get("web_settings") or WEB_SETTINGS_PART

    # Core & Document overrides
    add_override(doc_part)
    add_override(core_part)
    add_override(app_part)
    add_override(settings_part)
    add_override(web_settings_part)

    if "styles" in data:
        add_override(ct_data.get("styles") or STYLES_PART)

    if "numbering" in data:
        add_override(ct_data.get("numbering") or NUMBERING_PART)

    if "footnotes" in data:
        add_override(ct_data.get("footnotes") or FOOTNOTES_PART)

    if "endnotes" in data:
        add_override(ct_data.get("endnotes") or ENDNOTES_PART)

    if "comments" in data:
        add_override(ct_data.get("comments") or COMMENTS_PART)

    # Extra parts like headers/footers
    if extra_parts:
        for part in extra_parts:
            clean_part = "/" + part.lstrip("/")
            if "header" in part and part.endswith(".xml"):
                content_types_lines.append(
                    f'  <Override PartName="{clean_part}" '
                    f'ContentType="{header_ct}"/>'
                )
            elif "footer" in part and part.endswith(".xml"):
                content_types_lines.append(
                    f'  <Override PartName="{clean_part}" '
                    f'ContentType="{footer_ct}"/>'
                )

    content_types_lines.append("</Types>")
    return "\n".join(content_types_lines)


def copy_template_parts(
    template_docx: Path,
    writer: DocxWriter,
    exclude_parts: set[str] | None = None,
    content_types_data: dict[str, Any] | None = None,
    docx_config: dict[str, Any] | None = None,
) -> set[str]:
    """Copy non-generated parts from a template DOCX archive into writer."""
    ct_data = content_types_data or CONTENT_TYPES_DATA
    d_config = docx_config or DOCX_CONFIG_DATA

    doc_part = ct_data.get("document") or d_config.get("root_part") or DOCUMENT_PART
    styles_part = ct_data.get("styles") or STYLES_PART
    num_part = ct_data.get("numbering") or NUMBERING_PART
    rels_part = (
        ct_data.get("document_relationships")
        or d_config.get("document_relationships_part")
        or DOCUMENT_RELATIONSHIPS_PART
    )
    media_dir = ct_data.get("media_dir") or d_config.get("media_dir") or MEDIA_DIR

    copied_parts: set[str] = set()
    excludes = exclude_parts or set()

    with DocxReader(template_docx, docx_config=d_config, content_types_config=ct_data) as reader:
        for part_name in reader.list_parts():
            if (
                part_name
                not in (
                    doc_part,
                    styles_part,
                    num_part,
                    rels_part,
                )
                and part_name not in excludes
                and not part_name.startswith(media_dir)
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
    relationships_data: dict[str, Any] | None = None,
    content_types_data: dict[str, Any] | None = None,
    docx_config: dict[str, Any] | None = None,
) -> None:
    """Preserve internal relationships (theme, settings, fonts) from template archive."""
    rel_data = relationships_data or RELATIONSHIPS_DATA
    plumbing = set(rel_data.get("internal_plumbing_targets", INTERNAL_PLUMBING_TARGETS))

    with DocxReader(
        template_docx,
        docx_config=docx_config,
        content_types_config=content_types_data,
    ) as reader:
        template_rels_xml = reader.get_relationships_xml()
        if not template_rels_xml:
            return

        template_rels = XmlToJsonParser(
            docx_config=docx_config,
            content_types_config=content_types_data,
            relationships_config=relationships_data,
        ).parse_relationships(
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
                    target in plumbing
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
    relationships_data: dict[str, Any] | None = None,
    content_types_data: dict[str, Any] | None = None,
) -> None:
    """Ensure numbering, styles, settings, and notes relationships exist in rels_list if required."""
    ct_data = content_types_data or CONTENT_TYPES_DATA
    rel_data = relationships_data or RELATIONSHIPS_DATA
    rel_ns = rel_data.get("namespaces", {}).get("document") or DOCUMENT_RELATIONSHIPS_NS
    rel_types = rel_data.get("types", RELATIONSHIP_TYPES)

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
            rel_type = rel_types.get(
                rel_type_suffix,
                f"{rel_ns}/{rel_type_suffix}",
            )
            rels_list.append(
                {
                    "id": f"rId{next_rid_num}",
                    "type": rel_type,
                    "target": target,
                }
            )
            existing_targets.add(target)
            next_rid_num += 1

    if "numbering" in data:
        add_rel("numbering", Path(ct_data.get("numbering") or NUMBERING_PART).name)

    if "styles" in data:
        add_rel("styles", Path(ct_data.get("styles") or STYLES_PART).name)

    if "footnotes" in data:
        add_rel("footnotes", Path(ct_data.get("footnotes") or FOOTNOTES_PART).name)

    if "endnotes" in data:
        add_rel("endnotes", Path(ct_data.get("endnotes") or ENDNOTES_PART).name)

    if "comments" in data:
        add_rel("comments", Path(ct_data.get("comments") or COMMENTS_PART).name)

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
    add_rel("settings", Path(ct_data.get("settings") or SETTINGS_PART).name)
    add_rel("webSettings", Path(ct_data.get("web_settings") or WEB_SETTINGS_PART).name)


def filter_standalone_relationships(
    rels_list: list[dict[str, Any]],
    data: dict[str, Any],
    media_targets: set[str],
    copied_parts: set[str],
    extra_targets: set[str] | None = None,
    content_types_data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Filter relationship list for standalone documents without a template."""
    ct_data = content_types_data or CONTENT_TYPES_DATA
    filtered_rels: list[dict[str, Any]] = []
    extras = extra_targets or set()
    media_dir = ct_data.get("media_dir") or MEDIA_DIR
    media_prefix = media_dir.lstrip("word/").rstrip("/")

    styles_name = Path(ct_data.get("styles") or STYLES_PART).name
    numbering_name = Path(ct_data.get("numbering") or NUMBERING_PART).name
    settings_name = Path(ct_data.get("settings") or SETTINGS_PART).name
    web_settings_name = Path(ct_data.get("web_settings") or WEB_SETTINGS_PART).name
    footnotes_name = Path(ct_data.get("footnotes") or FOOTNOTES_PART).name
    endnotes_name = Path(ct_data.get("endnotes") or ENDNOTES_PART).name
    comments_name = Path(ct_data.get("comments") or COMMENTS_PART).name

    for rel in rels_list:
        target = rel.get("target", "")

        if rel.get("targetMode") == "External":
            filtered_rels.append(rel)

        elif target in media_targets or f"{media_prefix}/{target}" in media_targets:
            filtered_rels.append(rel)

        elif target in extras or f"word/{target}" in extras:
            filtered_rels.append(rel)

        elif target == styles_name and "styles" in data:
            filtered_rels.append(rel)

        elif target == numbering_name and "numbering" in data:
            filtered_rels.append(rel)

        elif target in (settings_name, web_settings_name):
            filtered_rels.append(rel)

        elif target == footnotes_name and "footnotes" in data:
            filtered_rels.append(rel)

        elif target == endnotes_name and "endnotes" in data:
            filtered_rels.append(rel)

        elif target == comments_name and "comments" in data:
            filtered_rels.append(rel)

        elif target.startswith("header") or target.startswith("footer"):
            filtered_rels.append(rel)

        elif (
            f"word/{target}" in copied_parts
            or target in copied_parts
        ):
            filtered_rels.append(rel)

    return filtered_rels
