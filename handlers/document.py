# --------------------------------
# Imports
# --------------------------------

from typing import Any
import xml.etree.ElementTree as ET

from config import (
    STYLE_PROPS,
    DEFAULT_MARGINS,
    DEFAULT_ORIENTATION,
)
from handlers.base import BaseHandler, qn
from handlers.paragraph import ParagraphHandler
from handlers.table import TableHandler
from handlers.sections import SectionsHandler
from handlers.media import MediaHandler


# --------------------------------
# Document Handler
# --------------------------------

class DocumentHandler(BaseHandler):

    # --------------------------------
    # Initialization
    # --------------------------------

    def __init__(
        self,
        paragraph_handler: ParagraphHandler | None = None,
        table_handler: TableHandler | None = None,
        sections_handler: SectionsHandler | None = None,
    ):
        self.paragraph_handler = (
            paragraph_handler or ParagraphHandler()
        )  # Paragraph handler

        self.table_handler = (
            table_handler or TableHandler(self.paragraph_handler)
        )  # Table handler

        self.sections_handler = (
            sections_handler or SectionsHandler()
        )  # Section handler

        self.media_handler = MediaHandler()  # Media handler


    # --------------------------------
    # Style Helpers
    # --------------------------------

    def _extract_style_keys(
        self,
        obj: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:

        style_dict: dict[str, Any] = {}
        content_dict: dict[str, Any] = {}

        style_value = obj.get("style")

        if style_value and not str(style_value).startswith("s"):
            style_dict["basedOn"] = style_value  # Preserve base style

        for key, value in obj.items():
            if key in STYLE_PROPS and value not in (None, "", {}):
                style_dict[key] = value  # Extract style property
            elif key != "style" or "basedOn" not in style_dict:
                content_dict[key] = value  # Preserve content property

        return style_dict, content_dict


    def _hashable_style(
        self,
        style_dict: dict[str, Any],
    ) -> tuple:

        items: list[tuple[str, Any]] = []

        for key in sorted(style_dict):
            value = style_dict[key]

            if isinstance(value, dict):
                normalized = tuple(
                    sorted(
                        (dict_key, str(dict_value))
                        for dict_key, dict_value in value.items()
                    )
                )
                items.append((key, normalized))

            elif isinstance(value, list):
                items.append((key, tuple(value)))

            else:
                items.append((key, str(value)))

        return tuple(items)


    # --------------------------------
    # Style Deduplication
    # --------------------------------

    def _deduplicate_styles(
        self,
        sections: list[dict[str, Any]],
        existing_styles: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        styles_map: dict[str, Any] = dict(
            existing_styles or {}
        )  # Preserve existing styles

        style_counts: dict[tuple, int] = {}
        style_objects: dict[tuple, dict[str, Any]] = {}

        def register_style(item: Any) -> None:
            if not isinstance(item, dict):
                return

            style_dict, _ = self._extract_style_keys(item)

            if style_dict:
                style_key = self._hashable_style(style_dict)
                style_counts[style_key] = (
                    style_counts.get(style_key, 0) + 1
                )
                style_objects[style_key] = style_dict

        def scan_item(item: Any) -> None:
            if not isinstance(item, dict):
                return

            register_style(item)

            runs = item.get("runs", [])

            if isinstance(runs, list):
                for run in runs:
                    register_style(run)

            rows = item.get("rows", [])

            if not isinstance(rows, list):
                return

            for row in rows:
                if isinstance(row, list):
                    for cell in row:
                        scan_item(cell)

                elif isinstance(row, dict):
                    cells = row.get("cells", [])

                    if isinstance(cells, list):
                        for cell in cells:
                            scan_item(cell)

        for section in sections:
            if not isinstance(section, dict):
                continue

            content = section.get("content", [])

            if isinstance(content, list):
                for item in content:
                    scan_item(item)

        hash_to_class: dict[tuple, str] = {}
        class_index = 1

        # Reuse existing matching styles first.
        for style_name, style_definition in styles_map.items():
            if not isinstance(style_definition, dict):
                continue

            style_key = self._hashable_style(style_definition)

            if style_key in style_counts:
                hash_to_class[style_key] = style_name

        # Create reusable styles for repeated combinations.
        for style_key, count in style_counts.items():
            if style_key in hash_to_class:
                continue

            style_definition = style_objects[style_key]

            if count < 2 and len(style_definition) < 2:
                continue

            while f"s{class_index}" in styles_map:
                class_index += 1

            style_name = f"s{class_index}"
            class_index += 1

            hash_to_class[style_key] = style_name
            styles_map[style_name] = style_definition

        def apply_style(item: Any) -> Any:
            if not isinstance(item, dict):
                return item

            style_dict, content_dict = self._extract_style_keys(item)

            if style_dict:
                style_key = self._hashable_style(style_dict)

                if style_key in hash_to_class:
                    content_dict["style"] = hash_to_class[style_key]
                else:
                    content_dict.update(style_dict)
            else:
                content_dict = dict(item)

            runs = content_dict.get("runs")

            if isinstance(runs, list):
                new_runs: list[Any] = []

                for run in runs:
                    if not isinstance(run, dict):
                        new_runs.append(run)
                        continue

                    run_style, run_content = self._extract_style_keys(run)

                    if run_style:
                        style_key = self._hashable_style(run_style)

                        if style_key in hash_to_class:
                            run_content["style"] = hash_to_class[style_key]
                        else:
                            run_content.update(run_style)

                    new_runs.append(run_content)

                content_dict["runs"] = new_runs

            rows = content_dict.get("rows")

            if isinstance(rows, list):
                new_rows: list[Any] = []

                for row in rows:
                    if isinstance(row, list):
                        new_rows.append(
                            [
                                apply_style(cell)
                                for cell in row
                            ]
                        )

                    elif isinstance(row, dict):
                        row_copy = dict(row)
                        cells = row_copy.get("cells")

                        if isinstance(cells, list):
                            row_copy["cells"] = [
                                apply_style(cell)
                                for cell in cells
                            ]

                        new_rows.append(row_copy)

                    else:
                        new_rows.append(row)

                content_dict["rows"] = new_rows

            return content_dict

        for section in sections:
            if not isinstance(section, dict):
                continue

            content = section.get("content", [])

            if isinstance(content, list):
                section["content"] = [
                    apply_style(item)
                    for item in content
                ]

        return styles_map


    # --------------------------------
    # Style Resolution
    # --------------------------------

    def _resolve_item_style(
        self,
        item: dict[str, Any],
        styles_map: dict[str, Any],
    ) -> dict[str, Any]:

        style_key = item.get("style")

        if not style_key:
            return dict(item)

        if not isinstance(styles_map, dict):
            return dict(item)

        preset = styles_map.get(style_key)

        if not isinstance(preset, dict):
            return dict(item)

        # Preserve named styles from styles.xml.
        if (
            preset.get("id") == style_key
            or "type" in preset
            or "name" in preset
        ):
            result = dict(item)
            result["style"] = style_key
            return result

        merged = dict(preset)

        if "basedOn" in merged:
            merged["style"] = merged["basedOn"]
        else:
            merged["style"] = style_key

        # Item properties override preset properties.
        merged.update(item)

        return merged


    # --------------------------------
    # Section Content Helpers
    # --------------------------------

    def _get_section_content(
        self,
        section: dict[str, Any],
    ) -> list[Any]:

        content = section.get(
            "content",
            section.get(
                "children",
                section.get("body", []),
            ),
        )

        return content if isinstance(content, list) else []


    # --------------------------------
    # Heading Rendering
    # --------------------------------

    def _render_heading(
        self,
        item: dict[str, Any],
    ) -> ET.Element:

        paragraph_data = dict(item)
        paragraph_data["type"] = "paragraph"

        if "heading" not in paragraph_data and "style" not in paragraph_data:
            item_type = str(item.get("type", ""))

            if (
                item_type.startswith("h")
                and len(item_type) == 2
                and item_type[1].isdigit()
            ):
                level = int(item_type[1])
            else:
                level = item.get("level") or 1

            paragraph_data["style"] = f"Heading{level}"

        return self.paragraph_handler.to_xml(
            paragraph_data
        )


    # --------------------------------
    # Page Break Rendering
    # --------------------------------

    def _render_page_break(self) -> ET.Element:

        paragraph = ET.Element(qn("w:p"))
        run = ET.SubElement(
            paragraph,
            qn("w:r"),
        )

        ET.SubElement(
            run,
            qn("w:br"),
            {qn("w:type"): "page"},
        )

        return paragraph


    # --------------------------------
    # Divider Rendering
    # --------------------------------

    def _render_divider(self) -> ET.Element:

        paragraph = ET.Element(qn("w:p"))
        paragraph_properties = ET.SubElement(
            paragraph,
            qn("w:pPr"),
        )

        paragraph_border = ET.SubElement(
            paragraph_properties,
            qn("w:pBdr"),
        )

        ET.SubElement(
            paragraph_border,
            qn("w:bottom"),
            {
                qn("w:val"): "single",
                qn("w:sz"): "6",
                qn("w:space"): "1",
                qn("w:color"): "auto",
            },
        )

        return paragraph


    # --------------------------------
    # Table Rendering
    # --------------------------------

    def _resolve_table_styles(
        self,
        item: dict[str, Any],
        styles_map: dict[str, Any],
    ) -> dict[str, Any]:

        table_data = dict(item)
        rows = table_data.get("rows")

        if not isinstance(rows, list):
            return table_data

        resolved_rows: list[Any] = []

        for row in rows:
            if isinstance(row, list):
                resolved_rows.append(
                    [
                        self._resolve_item_style(
                            cell,
                            styles_map,
                        )
                        if isinstance(cell, dict)
                        else cell
                        for cell in row
                    ]
                )

            elif isinstance(row, dict):
                row_copy = dict(row)
                cells = row_copy.get("cells")

                if isinstance(cells, list):
                    row_copy["cells"] = [
                        self._resolve_item_style(
                            cell,
                            styles_map,
                        )
                        if isinstance(cell, dict)
                        else cell
                        for cell in cells
                    ]

                resolved_rows.append(row_copy)

            else:
                resolved_rows.append(row)

        table_data["rows"] = resolved_rows

        return table_data


    # --------------------------------
    # List Rendering
    # --------------------------------

    def _render_list(
        self,
        item: dict[str, Any],
        styles_map: dict[str, Any],
    ) -> list[ET.Element]:

        is_ordered = bool(item.get("ordered", False))
        base_level = item.get("level", 0)
        elements: list[ET.Element] = []

        list_items = item.get("items", [])

        if not isinstance(list_items, list):
            return elements

        for list_item in list_items:

            if isinstance(list_item, str):
                item_data: dict[str, Any] = {
                    "text": list_item,
                    "level": base_level,
                    (
                        "numbered"
                        if is_ordered
                        else "bullet"
                    ): True,
                }

            elif isinstance(list_item, dict):
                item_data = dict(list_item)

                item_data.setdefault(
                    "level",
                    base_level,
                )

                if not any(
                    key in item_data
                    for key in (
                        "bullet",
                        "numbered",
                        "list",
                        "numbering",
                    )
                ):
                    item_data[
                        "numbered"
                        if is_ordered
                        else "bullet"
                    ] = True

            else:
                continue

            resolved_item = self._resolve_item_style(
                item_data,
                styles_map,
            )

            elements.append(
                self.paragraph_handler.to_xml(
                    resolved_item
                )
            )

        return elements


    # --------------------------------
    # Media Rendering
    # --------------------------------

    def _render_media(
        self,
        item: dict[str, Any],
    ) -> ET.Element:

        paragraph = ET.Element(qn("w:p"))
        run = ET.SubElement(
            paragraph,
            qn("w:r"),
        )

        run.append(
            self.media_handler.to_xml(item)
        )

        return paragraph


    # --------------------------------
    # Paragraph Rendering
    # --------------------------------

    def _render_paragraph(
        self,
        item: dict[str, Any],
        styles_map: dict[str, Any],
    ) -> ET.Element:

        paragraph_data = dict(item)
        runs = paragraph_data.get("runs")

        if isinstance(runs, list):
            paragraph_data["runs"] = [
                self._resolve_item_style(
                    run,
                    styles_map,
                )
                if isinstance(run, dict)
                else run
                for run in runs
            ]

        return self.paragraph_handler.to_xml(
            paragraph_data
        )


    # --------------------------------
    # Content Rendering
    # --------------------------------

    def _render_element(
        self,
        raw_item: Any,
        styles_map: dict[str, Any],
    ) -> ET.Element | list[ET.Element] | None:

        if isinstance(raw_item, str):
            return self.paragraph_handler.to_xml(
                {"text": raw_item}
            )

        if not isinstance(raw_item, dict):
            return None

        item = self._resolve_item_style(
            raw_item,
            styles_map,
        )

        item_type = item.get(
            "type",
            "paragraph",
        )

        # Heading.
        if item_type in (
            "heading",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ):
            return self._render_heading(item)

        # Page break.
        if item_type in (
            "pageBreak",
            "page_break",
        ):
            return self._render_page_break()

        # Divider.
        if item_type in (
            "divider",
            "horizontal_rule",
            "hr",
        ):
            return self._render_divider()

        # Table.
        if (
            item_type in (
                "table",
                "w:tbl",
                self.tag_to_name("w:tbl"),
                "tbl",
            )
            or "rows" in item
        ):
            table_data = self._resolve_table_styles(
                item,
                styles_map,
            )

            return self.table_handler.to_xml(
                table_data
            )

        # List.
        if (
            item_type == "list"
            and isinstance(item.get("items"), list)
        ):
            return self._render_list(
                item,
                styles_map,
            )

        # Media.
        if item_type in (
            "image",
            "drawing",
            "shape",
            "shapeGroup",
        ):
            return self._render_media(item)

        # Paragraph and list item.
        if (
            item_type in (
                "paragraph",
                "w:p",
                self.tag_to_name("w:p"),
                "p",
                "bullet",
                "list_item",
                "listItem",
            )
            or "text" in item
            or "runs" in item
        ):
            return self._render_paragraph(
                item,
                styles_map,
            )

        # Fallback to paragraph handler.
        return self.paragraph_handler.to_xml(item)


    # --------------------------------
    # Document XML Parsing
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> dict[str, Any]:

        body = element.find(
            qn("w:body")
        )

        if body is None:
            if simple:
                return {"sections": []}

            return {
                "type": "document",
                "body": {
                    "content": [],
                },
            }

        # Raw mode preserves the direct body structure.
        if not simple:
            raw_content: list[Any] = []

            for child in body:
                if child.tag == qn("w:p"):
                    raw_content.append(
                        self.paragraph_handler.to_json(
                            child,
                            simple=False,
                        )
                    )

                elif child.tag == qn("w:tbl"):
                    raw_content.append(
                        self.table_handler.to_json(
                            child,
                            simple=False,
                        )
                    )

                elif child.tag == qn("w:sectPr"):
                    raw_content.append(
                        self.sections_handler.to_json(
                            child,
                            simple=False,
                        )
                    )

            return {
                "type": "document",
                "body": {
                    "content": raw_content,
                },
            }

        # Simple mode groups content by sections.
        sections: list[dict[str, Any]] = []
        current_content: list[dict[str, Any]] = []

        for child in body:

            if child.tag == qn("w:p"):
                section_properties = self._extract_paragraph_section(
                    child
                )

                if section_properties is None:
                    current_content.append(
                        self.paragraph_handler.to_json(
                            child,
                            simple=True,
                        )
                    )
                    continue

                paragraph_json = (
                    self.paragraph_handler.to_json(
                        child,
                        simple=True,
                    )
                )

                current_content.append(
                    paragraph_json
                )

                section_data = self.sections_handler.to_json(
                    section_properties,
                    simple=True,
                )

                section = dict(section_data)
                section["content"] = current_content

                sections.append(section)
                current_content = []

            elif child.tag == qn("w:tbl"):
                current_content.append(
                    self.table_handler.to_json(
                        child,
                        simple=True,
                    )
                )

            elif child.tag == qn("w:sectPr"):
                section_data = self.sections_handler.to_json(
                    child,
                    simple=True,
                )

                section = dict(section_data)
                section["content"] = current_content

                sections.append(section)
                current_content = []

        # Preserve remaining content with a default section.
        if current_content or not sections:
            sections.append(
                {
                    "page": {
                        "size": "a4",
                        "orientation": DEFAULT_ORIENTATION,
                        "margins": {
                            "top": DEFAULT_MARGINS.get("top", 1440),
                            "bottom": DEFAULT_MARGINS.get("bottom", 1440),
                            "left": DEFAULT_MARGINS.get("left", 1440),
                            "right": DEFAULT_MARGINS.get("right", 1440),
                        },
                    },
                    "content": current_content,
                }
            )

        result: dict[str, Any] = {
            "sections": sections,
        }

        background = self._parse_background(
            element
        )

        if background:
            result["background"] = background

        return result


    # --------------------------------
    # Paragraph Section Extraction
    # --------------------------------

    def _extract_paragraph_section(
        self,
        paragraph: ET.Element,
    ) -> ET.Element | None:

        paragraph_properties = paragraph.find(
            qn("w:pPr")
        )

        if paragraph_properties is None:
            return None

        section_properties = paragraph_properties.find(
            qn("w:sectPr")
        )

        if section_properties is None:
            section_properties = paragraph.find(
                qn("w:sectPr")
            )

        if section_properties is None:
            return None

        # Temporarily detach section properties before paragraph parsing.
        if section_properties in paragraph_properties:
            paragraph_properties.remove(
                section_properties
            )

        elif section_properties in paragraph:
            paragraph.remove(
                section_properties
            )

        return section_properties


    # --------------------------------
    # Background Parsing
    # --------------------------------

    def _parse_background(
        self,
        element: ET.Element,
    ) -> dict[str, Any]:

        background_element = element.find(
            qn("w:background")
        )

        if background_element is None:
            return {}

        background: dict[str, Any] = {}

        color = background_element.get(
            qn("w:color")
        )

        if color is not None:
            background["color"] = color

        theme_color = background_element.get(
            qn("w:themeColor")
        )

        if theme_color is not None:
            background["themeColor"] = theme_color

        vml_background = background_element.find(
            qn("v:background")
        )

        if vml_background is None:
            return background

        vml_data: dict[str, Any] = {}

        for key, value in vml_background.attrib.items():
            vml_data[self.local_name(key)] = value

        vml_fill = vml_background.find(
            qn("v:fill")
        )

        if vml_fill is not None:
            fill_data: dict[str, Any] = {}

            for key, value in vml_fill.attrib.items():
                fill_data[self.local_name(key)] = value

            vml_data["fill"] = fill_data

        background["vmlBackground"] = vml_data

        return background


    # --------------------------------
    # Document XML Building
    # --------------------------------

    def to_xml(
        self,
        data: dict[str, Any] | list[Any],
    ) -> ET.Element:

        document = ET.Element(
            qn("w:document"),
            {
                qn("mc:Ignorable"): "w14 w15 wp14",
            },
        )

        # Document background must appear before body.
        self._append_background(
            document,
            data,
        )

        body = ET.SubElement(
            document,
            qn("w:body"),
        )

        styles_map: dict[str, Any] = {}
        sections_data: list[dict[str, Any]] = []

        # Normalize input into section structure.
        if isinstance(data, list):
            sections_data = [
                {
                    "content": data,
                }
            ]

        elif isinstance(data, dict):
            raw_styles = data.get("styles")

            if isinstance(raw_styles, dict):
                styles_map = raw_styles

            raw_sections = data.get("sections")

            if isinstance(raw_sections, list):
                sections_data = raw_sections

            elif "body" in data:
                raw_body = data["body"]

                if isinstance(raw_body, list):
                    sections_data = [
                        {
                            "content": raw_body,
                            "page": data.get("page"),
                        }
                    ]

                elif isinstance(raw_body, dict):
                    sections_data = [
                        {
                            "content": raw_body.get(
                                "content",
                                [],
                            ),
                            "page": raw_body.get(
                                "page",
                                data.get("page"),
                            ),
                        }
                    ]

            elif isinstance(data.get("content"), list):
                sections_data = [
                    {
                        "content": data["content"],
                        "page": data.get("page"),
                    }
                ]

            else:
                sections_data = [
                    {
                        "content": [],
                        "page": data.get("page"),
                    }
                ]

        # Build each section.
        for section_index, section in enumerate(
            sections_data
        ):

            if not isinstance(section, dict):
                continue

            is_last_section = (
                section_index == len(sections_data) - 1
            )

            content_items = self._get_section_content(
                section
            )

            rendered_elements: list[ET.Element] = []

            for item in content_items:
                rendered = self._render_element(
                    item,
                    styles_map,
                )

                if isinstance(rendered, list):
                    rendered_elements.extend(
                        rendered
                    )

                elif rendered is not None:
                    rendered_elements.append(
                        rendered
                    )

            section_element = (
                self.sections_handler.to_xml(
                    section
                )
            )

            if not is_last_section:
                self._append_non_final_section(
                    body,
                    rendered_elements,
                    section_element,
                )
            else:
                # Final section properties belong directly to body.
                for rendered in rendered_elements:
                    body.append(rendered)

                body.append(section_element)

        return document


    # --------------------------------
    # Background Building
    # --------------------------------

    def _append_background(
        self,
        document: ET.Element,
        data: dict[str, Any] | list[Any],
    ) -> None:

        if not isinstance(data, dict):
            return

        background_data = data.get(
            "background"
        )

        if not isinstance(background_data, dict):
            return

        background_attributes: dict[str, str] = {}

        if "color" in background_data:
            background_attributes[
                qn("w:color")
            ] = str(
                background_data["color"]
            ).lstrip("#")

        if "themeColor" in background_data:
            background_attributes[
                qn("w:themeColor")
            ] = str(
                background_data["themeColor"]
            )

        background_element = ET.SubElement(
            document,
            qn("w:background"),
            background_attributes,
        )

        vml_data = background_data.get(
            "vmlBackground"
        )

        if not isinstance(vml_data, dict):
            return

        vml_element = ET.SubElement(
            background_element,
            qn("v:background"),
            {
                "id": str(
                    vml_data.get(
                        "id",
                        "_x0000_s1025",
                    )
                ),
                qn("o:bwmode"): str(
                    vml_data.get(
                        "bwmode",
                        "white",
                    )
                ),
                "fillcolor": str(
                    vml_data.get(
                        "fillcolor",
                        f"#{background_data.get('color', 'f2f2f2')}",
                    )
                ),
            },
        )

        fill_data = vml_data.get("fill")

        if not isinstance(fill_data, dict):
            return

        fill_attributes: dict[str, str] = {}

        fill_id = (
            fill_data.get("id")
            or fill_data.get("relationshipId")
        )

        if fill_id:
            fill_attributes[
                qn("r:id")
            ] = str(fill_id)

        if "title" in fill_data:
            fill_attributes[
                qn("o:title")
            ] = str(
                fill_data["title"]
            )

        if "type" in fill_data:
            fill_attributes[
                "type"
            ] = str(
                fill_data["type"]
            )

        ET.SubElement(
            vml_element,
            qn("v:fill"),
            fill_attributes,
        )


    # --------------------------------
    # Non-Final Section Building
    # --------------------------------

    def _append_non_final_section(
        self,
        body: ET.Element,
        rendered_elements: list[ET.Element],
        section_element: ET.Element,
    ) -> None:

        if (
            rendered_elements
            and rendered_elements[-1].tag == qn("w:p")
        ):
            last_paragraph = rendered_elements[-1]

            paragraph_properties = last_paragraph.find(
                qn("w:pPr")
            )

            if paragraph_properties is None:
                paragraph_properties = ET.Element(
                    qn("w:pPr")
                )

                last_paragraph.insert(
                    0,
                    paragraph_properties,
                )

            paragraph_properties.append(
                section_element
            )

            for rendered in rendered_elements:
                body.append(rendered)

            return

        # Section ended with table or empty content.
        for rendered in rendered_elements:
            body.append(rendered)

        break_paragraph = ET.Element(
            qn("w:p")
        )

        paragraph_properties = ET.SubElement(
            break_paragraph,
            qn("w:pPr"),
        )

        paragraph_properties.append(
            section_element
        )

        body.append(
            break_paragraph
        )


# --------------------------------
# Public API
# --------------------------------

__all__ = [
    "DocumentHandler",
    "STYLE_PROPS",
]