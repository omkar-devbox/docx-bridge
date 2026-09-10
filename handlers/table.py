from typing import Any
import xml.etree.ElementTree as ET

from handlers.base import BaseHandler, qn, local_name
from handlers.paragraph import ParagraphHandler


# --------------------------------
# Table Handler
# --------------------------------

class TableHandler(BaseHandler):

    def __init__(
        self,
        paragraph_handler: ParagraphHandler | None = None,
    ):
        self.paragraph_handler = (
            paragraph_handler
            or ParagraphHandler()
        )

    # --------------------------------
    # JSON Conversion
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> dict[str, Any]:

        table_properties: dict[str, Any] = {}

        tbl_pr = (
            element
            if element.tag == qn("w:tblPr")
            else element.find(qn("w:tblPr"))
        )

        # --------------------------------
        # Table Properties
        # --------------------------------

        if tbl_pr is not None:

            # --------------------------------
            # Table Style
            # --------------------------------

            tbl_style = tbl_pr.find(
                qn("w:tblStyle")
            )

            if tbl_style is not None:
                table_properties["style"] = (
                    tbl_style.attrib.get(
                        qn("w:val"),
                        "",
                    )
                )

            # --------------------------------
            # Table Width
            # --------------------------------

            tbl_width = tbl_pr.find(
                qn("w:tblW")
            )

            if tbl_width is not None:
                width_value = tbl_width.attrib.get(
                    qn("w:w"),
                    "",
                )

                width_data = {
                    "value": (
                        int(width_value)
                        if width_value.isdigit()
                        else width_value
                    ),
                    "type": tbl_width.attrib.get(
                        qn("w:type"),
                        "auto",
                    ),
                }

                table_properties["width"] = width_data

            # --------------------------------
            # Table Alignment
            # --------------------------------

            alignment = tbl_pr.find(
                qn("w:jc")
            )

            if alignment is not None:
                table_properties["alignment"] = (
                    alignment.attrib.get(
                        qn("w:val"),
                        "",
                    )
                )

            # --------------------------------
            # Floating Table Position
            # --------------------------------

            position_properties = tbl_pr.find(
                qn("w:tblpPr")
            )

            if position_properties is not None:
                position_data: dict[str, Any] = {}

                for key, value in (
                    position_properties.attrib.items()
                ):
                    clean_key = local_name(key)

                    if value.isdigit() or (
                        value.startswith("-")
                        and value[1:].isdigit()
                    ):
                        value = int(value)

                    position_data[clean_key] = value

                table_properties[
                    "positionProperties"
                ] = position_data

            # --------------------------------
            # Cell Margins
            # --------------------------------

            table_cell_margins = tbl_pr.find(
                qn("w:tblCellMar")
            )

            if table_cell_margins is not None:
                margins: dict[str, Any] = {}

                for side in (
                    "top",
                    "left",
                    "bottom",
                    "right",
                    "start",
                    "end",
                ):
                    side_element = table_cell_margins.find(
                        qn(f"w:{side}")
                    )

                    if side_element is None:
                        continue

                    width_value = side_element.attrib.get(
                        qn("w:w"),
                        "0",
                    )

                    margins[side] = {
                        "value": (
                            int(width_value)
                            if width_value.isdigit()
                            else width_value
                        ),
                        "type": side_element.attrib.get(
                            qn("w:type"),
                            "dxa",
                        ),
                    }

                if margins:
                    table_properties[
                        "cellMargins"
                    ] = margins

            # --------------------------------
            # Cell Spacing
            # --------------------------------

            cell_spacing = tbl_pr.find(
                qn("w:tblCellSpacing")
            )

            if cell_spacing is not None:
                width_value = cell_spacing.attrib.get(
                    qn("w:w"),
                    "",
                )

                spacing_data = {
                    "value": (
                        int(width_value)
                        if width_value.isdigit()
                        else width_value
                    ),
                    "type": cell_spacing.attrib.get(
                        qn("w:type"),
                        "dxa",
                    ),
                }

                table_properties[
                    "cellSpacing"
                ] = spacing_data

            # --------------------------------
            # Table Indent
            # --------------------------------

            table_indent = tbl_pr.find(
                qn("w:tblInd")
            )

            if table_indent is not None:
                width_value = table_indent.attrib.get(
                    qn("w:w"),
                    "",
                )

                indent_data = {
                    "value": (
                        int(width_value)
                        if width_value.isdigit()
                        else width_value
                    ),
                    "type": table_indent.attrib.get(
                        qn("w:type"),
                        "dxa",
                    ),
                }

                table_properties["indent"] = (
                    indent_data
                )

            # --------------------------------
            # Table Layout
            # --------------------------------

            table_layout = tbl_pr.find(
                qn("w:tblLayout")
            )

            if table_layout is not None:
                table_properties["layout"] = (
                    table_layout.attrib.get(
                        qn("w:type"),
                        "fixed",
                    )
                )

            # --------------------------------
            # Table Look
            # --------------------------------

            table_look = tbl_pr.find(
                qn("w:tblLook")
            )

            if table_look is not None:
                look_data: dict[str, Any] = {}

                for key, value in (
                    table_look.attrib.items()
                ):
                    look_data[local_name(key)] = value

                table_properties["look"] = look_data

            # --------------------------------
            # Table Shading
            # --------------------------------

            table_shading = tbl_pr.find(
                qn("w:shd")
            )

            if table_shading is not None:
                shading_data: dict[str, Any] = {}

                for key, value in (
                    table_shading.attrib.items()
                ):
                    shading_data[local_name(key)] = value

                table_properties["shading"] = (
                    shading_data
                )

            # --------------------------------
            # Table Borders
            # --------------------------------

            table_borders = tbl_pr.find(
                qn("w:tblBorders")
            )

            if table_borders is not None:
                borders_data: dict[str, Any] = {}

                for side in (
                    "top",
                    "left",
                    "bottom",
                    "right",
                    "start",
                    "end",
                    "insideH",
                    "insideV",
                ):
                    border_element = table_borders.find(
                        qn(f"w:{side}")
                    )

                    if border_element is not None:
                        borders_data[side] = {
                            local_name(key): value
                            for key, value
                            in border_element.attrib.items()
                        }

                if borders_data:
                    table_properties["borders"] = (
                        borders_data
                    )

        # --------------------------------
        # Table Grid
        # --------------------------------

        grid_columns: list[int | str] = []

        table_grid = element.find(
            qn("w:tblGrid")
        )

        if table_grid is not None:
            for column in table_grid.findall(
                qn("w:gridCol")
            ):
                width_value = column.attrib.get(
                    qn("w:w"),
                    "",
                )

                grid_columns.append(
                    int(width_value)
                    if width_value.isdigit()
                    else width_value
                )

        # --------------------------------
        # Rows
        # --------------------------------

        rows: list[Any] = []

        for row in element.findall(qn("w:tr")):

            row_properties: dict[str, Any] = {}

            row_properties_element = row.find(
                qn("w:trPr")
            )

            if row_properties_element is not None:

                # Header row
                if row_properties_element.find(
                    qn("w:tblHeader")
                ) is not None:
                    row_properties["header"] = True

                # Prevent row splitting
                if row_properties_element.find(
                    qn("w:cantSplit")
                ) is not None:
                    row_properties["cantSplit"] = True

                # Row alignment
                alignment = row_properties_element.find(
                    qn("w:jc")
                )

                if alignment is not None:
                    row_properties["alignment"] = (
                        alignment.attrib.get(
                            qn("w:val"),
                            "",
                        )
                    )

                # Row cell spacing
                row_spacing = row_properties_element.find(
                    qn("w:tblCellSpacing")
                )

                if row_spacing is not None:
                    width_value = row_spacing.attrib.get(
                        qn("w:w"),
                        "",
                    )

                    row_properties["cellSpacing"] = {
                        "value": (
                            int(width_value)
                            if width_value.isdigit()
                            else width_value
                        ),
                        "type": row_spacing.attrib.get(
                            qn("w:type"),
                            "dxa",
                        ),
                    }

                # Row height
                row_height = row_properties_element.find(
                    qn("w:trHeight")
                )

                if row_height is not None:
                    height_value = row_height.attrib.get(
                        qn("w:val"),
                        "",
                    )

                    row_properties["height"] = (
                        int(height_value)
                        if height_value.isdigit()
                        else height_value
                    )

                    height_rule = row_height.attrib.get(
                        qn("w:hRule")
                    )

                    if height_rule:
                        row_properties[
                            "heightRule"
                        ] = height_rule

            # --------------------------------
            # Cells
            # --------------------------------

            cells: list[Any] = []

            for cell in row.findall(qn("w:tc")):

                cell_properties: dict[str, Any] = {}

                cell_properties_element = cell.find(
                    qn("w:tcPr")
                )

                if cell_properties_element is not None:

                    # Cell width
                    cell_width = cell_properties_element.find(
                        qn("w:tcW")
                    )

                    if cell_width is not None:
                        width_value = cell_width.attrib.get(
                            qn("w:w"),
                            "",
                        )

                        cell_properties["width"] = {
                            "value": (
                                int(width_value)
                                if width_value.isdigit()
                                else width_value
                            ),
                            "type": cell_width.attrib.get(
                                qn("w:type"),
                                "auto",
                            ),
                        }

                    # Column span
                    grid_span = cell_properties_element.find(
                        qn("w:gridSpan")
                    )

                    if grid_span is not None:
                        span_value = grid_span.attrib.get(
                            qn("w:val"),
                            "1",
                        )

                        cell_properties["gridSpan"] = (
                            int(span_value)
                            if span_value.isdigit()
                            else span_value
                        )

                    # Vertical merge
                    vertical_merge = cell_properties_element.find(
                        qn("w:vMerge")
                    )

                    if vertical_merge is not None:
                        merge_value = vertical_merge.attrib.get(
                            qn("w:val"),
                            "continue",
                        )

                        cell_properties["vMerge"] = (
                            merge_value
                        )

                    # Vertical alignment
                    vertical_alignment = (
                        cell_properties_element.find(
                            qn("w:vAlign")
                        )
                    )

                    if vertical_alignment is not None:
                        cell_properties["vAlign"] = (
                            vertical_alignment.attrib.get(
                                qn("w:val"),
                                "",
                            )
                        )

                    # Hide end mark
                    hide_mark = cell_properties_element.find(
                        qn("w:hideMark")
                    )

                    if hide_mark is not None:
                        cell_properties[
                            "hideMark"
                        ] = True

                    # Cell shading
                    cell_shading = cell_properties_element.find(
                        qn("w:shd")
                    )

                    if cell_shading is not None:
                        shading_data: dict[str, Any] = {}

                        for key, value in (
                            cell_shading.attrib.items()
                        ):
                            shading_data[
                                local_name(key)
                            ] = value

                        cell_properties[
                            "shading"
                        ] = shading_data

                    # Cell borders
                    cell_borders = cell_properties_element.find(
                        qn("w:tcBorders")
                    )

                    if cell_borders is not None:
                        borders_data: dict[str, Any] = {}

                        for side in (
                            "top",
                            "left",
                            "bottom",
                            "right",
                            "start",
                            "end",
                            "insideH",
                            "insideV",
                            "tl2br",
                            "tr2bl",
                        ):
                            border_element = cell_borders.find(
                                qn(f"w:{side}")
                            )

                            if border_element is not None:
                                borders_data[side] = {
                                    local_name(key): value
                                    for key, value
                                    in border_element.attrib.items()
                                }

                        cell_properties[
                            "borders"
                        ] = borders_data

                # --------------------------------
                # Cell Content
                # --------------------------------

                content: list[dict[str, Any]] = []

                # Preserve direct child order.
                for child in cell:

                    if child.tag == qn("w:p"):
                        content.append(
                            self.paragraph_handler.to_json(
                                child,
                                simple=simple,
                            )
                        )

                    elif child.tag == qn("w:tbl"):
                        content.append(
                            self.to_json(
                                child,
                                simple=simple,
                            )
                        )

                # --------------------------------
                # Simple Cell Representation
                # --------------------------------

                if simple:

                    def is_simple_paragraph(
                        item: Any,
                    ) -> bool:
                        return (
                            isinstance(item, dict)
                            and "rows" not in item
                        )

                    if (
                        len(content) == 1
                        and is_simple_paragraph(
                            content[0]
                        )
                    ):
                        paragraph_data = content[0]
                        paragraph_keys = set(
                            paragraph_data.keys()
                        )

                        if (
                            not cell_properties
                            and paragraph_keys == {"text"}
                        ):
                            cells.append(
                                paragraph_data["text"]
                            )

                        elif (
                            not cell_properties
                            and not paragraph_keys
                        ):
                            cells.append("")

                        else:
                            cell_data: dict[str, Any] = {}

                            if "width" in cell_properties:
                                cell_data["width"] = (
                                    cell_properties["width"]
                                )

                            if "gridSpan" in cell_properties:
                                cell_data["colSpan"] = (
                                    cell_properties[
                                        "gridSpan"
                                    ]
                                )

                            if "vMerge" in cell_properties:
                                cell_data["rowSpan"] = (
                                    cell_properties[
                                        "vMerge"
                                    ]
                                )

                            if "vAlign" in cell_properties:
                                cell_data["vAlign"] = (
                                    cell_properties[
                                        "vAlign"
                                    ]
                                )

                            if "shading" in cell_properties:
                                shading = cell_properties[
                                    "shading"
                                ]

                                if (
                                    isinstance(
                                        shading,
                                        dict,
                                    )
                                    and any(
                                        key in shading
                                        for key in (
                                            "themeFill",
                                            "themeFillShade",
                                            "themeFillTint",
                                        )
                                    )
                                    and len(shading) > 1
                                ):
                                    cell_data["bg"] = shading

                                elif (
                                    isinstance(
                                        shading,
                                        dict,
                                    )
                                    and "fill" in shading
                                ):
                                    cell_data["bg"] = (
                                        shading["fill"]
                                    )

                                else:
                                    cell_data["bg"] = shading

                            if "borders" in cell_properties:
                                cell_data["borders"] = (
                                    cell_properties[
                                        "borders"
                                    ]
                                )

                            for key in paragraph_keys:
                                cell_data[key] = (
                                    paragraph_data[key]
                                )

                            cells.append(cell_data)

                    elif (
                        not content
                        and not cell_properties
                    ):
                        cells.append("")

                    else:
                        cell_data: dict[str, Any] = {}

                        if "width" in cell_properties:
                            cell_data["width"] = (
                                cell_properties[
                                    "width"
                                ]
                            )

                        if "gridSpan" in cell_properties:
                            cell_data["colSpan"] = (
                                cell_properties[
                                    "gridSpan"
                                ]
                            )

                        if "vMerge" in cell_properties:
                            cell_data["rowSpan"] = (
                                cell_properties[
                                    "vMerge"
                                ]
                            )

                        if "vAlign" in cell_properties:
                            cell_data["vAlign"] = (
                                cell_properties[
                                    "vAlign"
                                ]
                            )

                        if "shading" in cell_properties:
                            shading = cell_properties[
                                "shading"
                            ]

                            if (
                                isinstance(
                                    shading,
                                    dict,
                                )
                                and any(
                                    key in shading
                                    for key in (
                                        "themeFill",
                                        "themeFillShade",
                                        "themeFillTint",
                                    )
                                )
                                and len(shading) > 1
                            ):
                                cell_data["bg"] = shading

                            elif (
                                isinstance(
                                    shading,
                                    dict,
                                )
                                and "fill" in shading
                            ):
                                cell_data["bg"] = (
                                    shading["fill"]
                                )

                            else:
                                cell_data["bg"] = shading

                        if "borders" in cell_properties:
                            cell_data["borders"] = (
                                cell_properties[
                                    "borders"
                                ]
                            )

                        cell_data["content"] = content
                        cells.append(cell_data)

                # --------------------------------
                # Full Cell Representation
                # --------------------------------

                else:
                    cells.append(
                        {
                            "type": self.tag_to_name(
                                "w:tc"
                            ),
                            "properties": cell_properties,
                            "content": content,
                        }
                    )

            # --------------------------------
            # Row Representation
            # --------------------------------

            if simple and not row_properties:
                rows.append(cells)
            else:
                rows.append(
                    {
                        "type": self.tag_to_name(
                            "w:tr"
                        ),
                        "properties": row_properties,
                        "cells": cells,
                    }
                )

        # --------------------------------
        # Table Result
        # --------------------------------

        if simple:
            result: dict[str, Any] = {
                "type": "table",
                "rows": rows,
            }

            simple_property_map = {
                "style": "style",
                "alignment": "align",
                "width": "width",
                "borders": "borders",
                "cellMargins": "cellMargins",
                "indent": "indent",
                "layout": "layout",
                "look": "look",
                "shading": "shading",
            }

            for source_key, target_key in (
                simple_property_map.items()
            ):
                if source_key in table_properties:
                    result[target_key] = (
                        table_properties[source_key]
                    )

            if grid_columns:
                result["grid"] = grid_columns

        else:
            result = {
                "type": self.tag_to_name(
                    "w:tbl"
                ),
                "properties": table_properties,
                "rows": rows,
            }

            if grid_columns:
                result["grid"] = grid_columns

        return result

    # --------------------------------
    # XML Conversion
    # --------------------------------

    def to_xml(
        self,
        data: dict[str, Any],
    ) -> ET.Element:

        table = ET.Element(qn("w:tbl"))

        properties = dict(
            data.get("tableProperties")
            or data.get("properties")
            or {}
        )

        # --------------------------------
        # Collect Flat Properties
        # --------------------------------

        property_aliases = (
            "style",
            "tableStyle",
            "alignment",
            "align",
            "width",
            "tableWidth",
            "borders",
            "layout",
            "cellMargins",
            "tableCellMargins",
            "indent",
            "tableIndent",
            "look",
            "tableLook",
            "cellSpacing",
            "tableCellSpacing",
            "shading",
            "positionProperties",
        )

        for key in property_aliases:
            if (
                key in data
                and key not in properties
            ):
                properties[key] = data[key]

        # --------------------------------
        # Table Properties
        # --------------------------------

        table_properties = ET.SubElement(
            table,
            qn("w:tblPr"),
        )

        # --------------------------------
        # Floating Position
        # --------------------------------

        position_properties = (
            properties.get(
                "tablePositionProperties"
            )
            or properties.get(
                "positionProperties"
            )
        )

        if position_properties:
            position_attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in position_properties.items()
            }

            ET.SubElement(
                table_properties,
                qn("w:tblpPr"),
                position_attributes,
            )

        # --------------------------------
        # Table Style
        # --------------------------------

        style_value = (
            properties.get("tableStyle")
            or properties.get("style")
        )

        if style_value:
            ET.SubElement(
                table_properties,
                qn("w:tblStyle"),
                {
                    qn("w:val"): str(style_value),
                },
            )

        # --------------------------------
        # Table Width
        # --------------------------------

        width_info = (
            properties.get("tableWidth")
            or properties.get("width")
        )

        if width_info is not None:

            if (
                isinstance(
                    width_info,
                    (int, str),
                )
                and str(width_info).isdigit()
            ):
                width_attributes = {
                    qn("w:w"): str(width_info),
                    qn("w:type"): "dxa",
                }

            elif isinstance(
                width_info,
                dict,
            ):
                width_attributes = {
                    qn("w:w"): str(
                        width_info.get(
                            "value",
                            0,
                        )
                    ),
                    qn("w:type"): str(
                        width_info.get(
                            "type",
                            "auto",
                        )
                    ),
                }

            else:
                width_attributes = {
                    qn("w:w"): "0",
                    qn("w:type"): "auto",
                }

            ET.SubElement(
                table_properties,
                qn("w:tblW"),
                width_attributes,
            )

        # --------------------------------
        # Table Alignment
        # --------------------------------

        alignment_value = (
            properties.get("alignment")
            or properties.get("align")
            or properties.get("jc")
        )

        if alignment_value:
            alignment_string = str(
                alignment_value
            ).lower()

            alignment_map = {
                "center": "center",
                "left": "left",
                "right": "right",
                "start": "left",
                "end": "right",
            }

            ET.SubElement(
                table_properties,
                qn("w:jc"),
                {
                    qn("w:val"): alignment_map.get(
                        alignment_string,
                        str(alignment_value),
                    )
                },
            )

        # --------------------------------
        # Cell Spacing
        # --------------------------------

        spacing_info = (
            properties.get(
                "tableCellSpacing"
            )
            or properties.get(
                "cellSpacing"
            )
        )

        if spacing_info:
            spacing_attributes = {
                qn("w:w"): str(
                    spacing_info.get(
                        "value",
                        0,
                    )
                ),
                qn("w:type"): str(
                    spacing_info.get(
                        "type",
                        "dxa",
                    )
                ),
            }

            ET.SubElement(
                table_properties,
                qn("w:tblCellSpacing"),
                spacing_attributes,
            )

        # --------------------------------
        # Table Indent
        # --------------------------------

        indent_info = (
            properties.get("tableIndent")
            or properties.get("indent")
        )

        if indent_info:
            indent_attributes = {
                qn("w:w"): str(
                    indent_info.get(
                        "value",
                        0,
                    )
                ),
                qn("w:type"): str(
                    indent_info.get(
                        "type",
                        "dxa",
                    )
                ),
            }

            ET.SubElement(
                table_properties,
                qn("w:tblInd"),
                indent_attributes,
            )

        # --------------------------------
        # Table Borders
        # --------------------------------

        borders_info = (
            properties.get("tableBorders")
            or properties.get("borders")
        )

        if isinstance(
            borders_info,
            dict,
        ):
            borders_element = ET.SubElement(
                table_properties,
                qn("w:tblBorders"),
            )

            for side, side_attributes in (
                borders_info.items()
            ):
                if not isinstance(
                    side_attributes,
                    dict,
                ):
                    continue

                attributes = {
                    qn(f"w:{key}"): str(value)
                    for key, value
                    in side_attributes.items()
                }

                ET.SubElement(
                    borders_element,
                    qn(f"w:{side}"),
                    attributes,
                )

        # --------------------------------
        # Table Shading
        # --------------------------------

        shading_info = properties.get(
            "shading"
        )

        if shading_info:
            shading_attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in shading_info.items()
            }

            ET.SubElement(
                table_properties,
                qn("w:shd"),
                shading_attributes,
            )

        # --------------------------------
        # Table Layout
        # --------------------------------

        layout_value = (
            properties.get("tableLayout")
            or properties.get("layout")
        )

        if layout_value:
            ET.SubElement(
                table_properties,
                qn("w:tblLayout"),
                {
                    qn("w:type"): str(
                        layout_value
                    ),
                },
            )

        # --------------------------------
        # Cell Margins
        # --------------------------------

        margins_info = (
            properties.get(
                "tableCellMargins"
            )
            or properties.get(
                "cellMargins"
            )
        )

        if margins_info:
            margins_element = ET.SubElement(
                table_properties,
                qn("w:tblCellMar"),
            )

            for side, side_data in (
                margins_info.items()
            ):
                if not isinstance(
                    side_data,
                    dict,
                ):
                    continue

                side_attributes = {
                    qn("w:w"): str(
                        side_data.get(
                            "value",
                            0,
                        )
                    ),
                    qn("w:type"): str(
                        side_data.get(
                            "type",
                            "dxa",
                        )
                    ),
                }

                ET.SubElement(
                    margins_element,
                    qn(f"w:{side}"),
                    side_attributes,
                )

            from handlers.base import (
                TBLCELLMAR_ORDER,
                sort_children_by_schema,
            )

            sort_children_by_schema(
                margins_element,
                TBLCELLMAR_ORDER,
            )

        # --------------------------------
        # Table Look
        # --------------------------------

        look_info = (
            properties.get("tableLook")
            or properties.get("look")
        )

        if look_info:
            look_attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in look_info.items()
            }

            ET.SubElement(
                table_properties,
                qn("w:tblLook"),
                look_attributes,
            )

        # --------------------------------
        # Table Property Ordering
        # --------------------------------

        from handlers.base import (
            TBLPR_ORDER,
            sort_children_by_schema,
        )

        sort_children_by_schema(
            table_properties,
            TBLPR_ORDER,
        )

        # --------------------------------
        # Table Grid
        # --------------------------------

        grid_data = (
            data.get("tableGrid")
            or data.get("grid")
        )

        if grid_data:
            table_grid = ET.SubElement(
                table,
                qn("w:tblGrid"),
            )

            for column_width in grid_data:
                ET.SubElement(
                    table_grid,
                    qn("w:gridCol"),
                    {
                        qn("w:w"): str(
                            column_width
                        )
                    },
                )

        # --------------------------------
        # Rows
        # --------------------------------

        for row_data in data.get(
            "rows",
            [],
        ):
            row = ET.SubElement(
                table,
                qn("w:tr"),
            )

            if isinstance(
                row_data,
                list,
            ):
                cells_list = row_data
                row_properties = {}

            elif isinstance(
                row_data,
                dict,
            ):
                cells_list = row_data.get(
                    "cells",
                    [],
                )

                row_properties = (
                    row_data.get(
                        "tableRowProperties"
                    )
                    or row_data.get(
                        "properties",
                        {},
                    )
                )

            else:
                cells_list = []
                row_properties = {}

            # --------------------------------
            # Row Properties
            # --------------------------------

            if row_properties:
                row_properties_element = ET.SubElement(
                    row,
                    qn("w:trPr"),
                )

                if (
                    row_properties.get(
                        "tableHeader"
                    )
                    or row_properties.get(
                        "header"
                    )
                ):
                    ET.SubElement(
                        row_properties_element,
                        qn("w:tblHeader"),
                    )

                if (
                    row_properties.get(
                        "cantSplitRow"
                    )
                    or row_properties.get(
                        "cantSplit"
                    )
                ):
                    ET.SubElement(
                        row_properties_element,
                        qn("w:cantSplit"),
                    )

                if row_properties.get(
                    "alignment"
                ):
                    ET.SubElement(
                        row_properties_element,
                        qn("w:jc"),
                        {
                            qn("w:val"): str(
                                row_properties[
                                    "alignment"
                                ]
                            )
                        },
                    )

                row_spacing = (
                    row_properties.get(
                        "tableCellSpacing"
                    )
                    or row_properties.get(
                        "cellSpacing"
                    )
                )

                if row_spacing:
                    spacing_attributes = {
                        qn("w:w"): str(
                            row_spacing.get(
                                "value",
                                0,
                            )
                        ),
                        qn("w:type"): str(
                            row_spacing.get(
                                "type",
                                "dxa",
                            )
                        ),
                    }

                    ET.SubElement(
                        row_properties_element,
                        qn("w:tblCellSpacing"),
                        spacing_attributes,
                    )

                row_height = (
                    row_properties.get(
                        "tableRowHeight"
                    )
                    or row_properties.get(
                        "height"
                    )
                )

                if row_height is not None:
                    height_attributes = {
                        qn("w:val"): str(
                            row_height
                        )
                    }

                    if row_properties.get(
                        "heightRule"
                    ):
                        height_attributes[
                            qn("w:hRule")
                        ] = str(
                            row_properties[
                                "heightRule"
                            ]
                        )

                    ET.SubElement(
                        row_properties_element,
                        qn("w:trHeight"),
                        height_attributes,
                    )

                from handlers.base import (
                    TRPR_ORDER,
                    sort_children_by_schema,
                )

                sort_children_by_schema(
                    row_properties_element,
                    TRPR_ORDER,
                )

            # --------------------------------
            # Cells
            # --------------------------------

            for cell_data in cells_list:

                cell = ET.SubElement(
                    row,
                    qn("w:tc"),
                )

                # --------------------------------
                # Plain String Cell
                # --------------------------------

                if isinstance(
                    cell_data,
                    str,
                ):
                    paragraph = ET.SubElement(
                        cell,
                        qn("w:p"),
                    )

                    if cell_data:
                        run = ET.SubElement(
                            paragraph,
                            qn("w:r"),
                        )

                        text = ET.SubElement(
                            run,
                            qn("w:t"),
                        )

                        text.text = cell_data

                        if (
                            cell_data.startswith(" ")
                            or cell_data.endswith(" ")
                        ):
                            text.set(
                                qn("xml:space"),
                                "preserve",
                            )

                    continue

                # --------------------------------
                # Object Cell
                # --------------------------------

                if isinstance(
                    cell_data,
                    dict,
                ):
                    cell_properties = dict(
                        cell_data.get(
                            "tableCellProperties"
                        )
                        or cell_data.get(
                            "properties",
                            {},
                        )
                    )

                    # Collect flat cell properties.
                    cell_property_keys = (
                        "colSpan",
                        "gridSpan",
                        "columnSpan",
                        "rowSpan",
                        "vMerge",
                        "verticalMerge",
                        "vAlign",
                        "verticalAlignment",
                        "width",
                        "cellWidth",
                        "bg",
                        "background",
                        "shading",
                        "borders",
                        "tableCellBorders",
                        "hideMark",
                        "hideEndMark",
                    )

                    for key in cell_property_keys:
                        if (
                            key in cell_data
                            and key not in cell_properties
                        ):
                            cell_properties[key] = (
                                cell_data[key]
                            )

                    # --------------------------------
                    # Cell Properties XML
                    # --------------------------------

                    if cell_properties:
                        cell_properties_element = ET.SubElement(
                            cell,
                            qn("w:tcPr"),
                        )

                        # Cell width
                        cell_width = (
                            cell_properties.get(
                                "cellWidth"
                            )
                            or cell_properties.get(
                                "width"
                            )
                        )

                        if cell_width is not None:

                            if (
                                isinstance(
                                    cell_width,
                                    (int, str),
                                )
                                and str(
                                    cell_width
                                ).isdigit()
                            ):
                                width_attributes = {
                                    qn("w:w"): str(
                                        cell_width
                                    ),
                                    qn("w:type"): "dxa",
                                }

                            elif isinstance(
                                cell_width,
                                dict,
                            ):
                                width_attributes = {
                                    qn("w:w"): str(
                                        cell_width.get(
                                            "value",
                                            0,
                                        )
                                    ),
                                    qn("w:type"): str(
                                        cell_width.get(
                                            "type",
                                            "auto",
                                        )
                                    ),
                                }

                            else:
                                width_attributes = {
                                    qn("w:w"): "0",
                                    qn("w:type"): "auto",
                                }

                            ET.SubElement(
                                cell_properties_element,
                                qn("w:tcW"),
                                width_attributes,
                            )

                        # Column span
                        span_value = (
                            cell_properties.get(
                                "colSpan"
                            )
                            or cell_properties.get(
                                "columnSpan"
                            )
                            or cell_properties.get(
                                "gridSpan"
                            )
                        )

                        if span_value:
                            ET.SubElement(
                                cell_properties_element,
                                qn("w:gridSpan"),
                                {
                                    qn("w:val"): str(
                                        span_value
                                    )
                                },
                            )

                        # Vertical merge
                        vertical_merge = (
                            cell_properties.get(
                                "rowSpan"
                            )
                            or cell_properties.get(
                                "verticalMerge"
                            )
                            or cell_properties.get(
                                "vMerge"
                            )
                        )

                        if vertical_merge:
                            merge_attributes = {}

                            if str(
                                vertical_merge
                            ) not in (
                                "continue",
                                "true",
                                "1",
                            ):
                                merge_attributes[
                                    qn("w:val")
                                ] = str(
                                    vertical_merge
                                )

                            ET.SubElement(
                                cell_properties_element,
                                qn("w:vMerge"),
                                merge_attributes,
                            )

                        # Vertical alignment
                        vertical_alignment = (
                            cell_properties.get(
                                "verticalAlignment"
                            )
                            or cell_properties.get(
                                "vAlign"
                            )
                        )

                        if vertical_alignment:
                            ET.SubElement(
                                cell_properties_element,
                                qn("w:vAlign"),
                                {
                                    qn("w:val"): str(
                                        vertical_alignment
                                    )
                                },
                            )

                        # Hide mark
                        if (
                            cell_properties.get(
                                "hideEndMark"
                            )
                            or cell_properties.get(
                                "hideMark"
                            )
                        ):
                            ET.SubElement(
                                cell_properties_element,
                                qn("w:hideMark"),
                            )

                        # --------------------------------
                        # Cell Shading
                        # --------------------------------

                        background = (
                            cell_properties.get("bg")
                            or cell_properties.get(
                                "background"
                            )
                            or cell_properties.get(
                                "shading"
                            )
                        )

                        if background:

                            if isinstance(
                                background,
                                str,
                            ):
                                ET.SubElement(
                                    cell_properties_element,
                                    qn("w:shd"),
                                    {
                                        qn("w:val"): "clear",
                                        qn("w:color"): "auto",
                                        qn("w:fill"): (
                                            background
                                            .lstrip("#")
                                        ),
                                    },
                                )

                            elif isinstance(
                                background,
                                dict,
                            ):
                                shading_attributes = {
                                    qn(f"w:{key}"): str(
                                        value
                                    )
                                    for key, value
                                    in background.items()
                                }

                                ET.SubElement(
                                    cell_properties_element,
                                    qn("w:shd"),
                                    shading_attributes,
                                )

                        # --------------------------------
                        # Cell Borders
                        # --------------------------------

                        cell_borders = (
                            cell_properties.get(
                                "tableCellBorders"
                            )
                            if cell_properties.get(
                                "tableCellBorders"
                            ) is not None
                            else cell_properties.get(
                                "borders"
                            )
                        )

                        if isinstance(
                            cell_borders,
                            dict,
                        ):
                            borders_element = ET.SubElement(
                                cell_properties_element,
                                qn("w:tcBorders"),
                            )

                            for side, side_attributes in (
                                cell_borders.items()
                            ):
                                if not isinstance(
                                    side_attributes,
                                    dict,
                                ):
                                    continue

                                attributes = {
                                    qn(f"w:{key}"): str(
                                        value
                                    )
                                    for key, value
                                    in side_attributes.items()
                                }

                                ET.SubElement(
                                    borders_element,
                                    qn(f"w:{side}"),
                                    attributes,
                                )

                        # --------------------------------
                        # Cell Property Ordering
                        # --------------------------------

                        from handlers.base import (
                            TCPR_ORDER,
                            sort_children_by_schema,
                        )

                        sort_children_by_schema(
                            cell_properties_element,
                            TCPR_ORDER,
                        )

                    # --------------------------------
                    # Cell Content
                    # --------------------------------

                    cell_content = cell_data.get(
                        "content"
                    )

                    if cell_content is not None:

                        if not cell_content:
                            cell.append(
                                ET.Element(
                                    qn("w:p")
                                )
                            )

                        else:
                            for item in cell_content:

                                # Plain text
                                if isinstance(
                                    item,
                                    str,
                                ):
                                    cell.append(
                                        self.paragraph_handler.to_xml(
                                            {
                                                "text": item
                                            }
                                        )
                                    )
                                    continue

                                if not isinstance(
                                    item,
                                    dict,
                                ):
                                    continue

                                item_type = item.get(
                                    "type",
                                    "",
                                )

                                # Nested table
                                if (
                                    item_type
                                    in (
                                        "table",
                                        "w:tbl",
                                        self.tag_to_name(
                                            "w:tbl"
                                        ),
                                        "tbl",
                                    )
                                    or "rows" in item
                                ):
                                    cell.append(
                                        self.to_xml(item)
                                    )

                                # Media
                                elif item_type in (
                                    "image",
                                    "drawing",
                                    "shape",
                                    "shapeGroup",
                                ):
                                    paragraph = ET.Element(
                                        qn("w:p")
                                    )

                                    run = ET.SubElement(
                                        paragraph,
                                        qn("w:r"),
                                    )

                                    from handlers.media import (
                                        MediaHandler,
                                    )

                                    run.append(
                                        MediaHandler().to_xml(
                                            item
                                        )
                                    )

                                    cell.append(
                                        paragraph
                                    )

                                # List
                                elif (
                                    item_type == "list"
                                    and "items" in item
                                    and isinstance(
                                        item["items"],
                                        list,
                                    )
                                ):
                                    ordered = item.get(
                                        "ordered",
                                        False,
                                    )

                                    base_level = item.get(
                                        "level",
                                        0,
                                    )

                                    for list_item in item[
                                        "items"
                                    ]:

                                        if isinstance(
                                            list_item,
                                            str,
                                        ):
                                            list_item_data = {
                                                "text": list_item,
                                                "level": base_level,
                                                (
                                                    "numbered"
                                                    if ordered
                                                    else "bullet"
                                                ): True,
                                            }

                                        elif isinstance(
                                            list_item,
                                            dict,
                                        ):
                                            list_item_data = dict(
                                                list_item
                                            )

                                            if "level" not in (
                                                list_item_data
                                            ):
                                                list_item_data[
                                                    "level"
                                                ] = base_level

                                            if not any(
                                                key in list_item_data
                                                for key in (
                                                    "bullet",
                                                    "numbered",
                                                    "list",
                                                    "numbering",
                                                )
                                            ):
                                                list_item_data[
                                                    (
                                                        "numbered"
                                                        if ordered
                                                        else "bullet"
                                                    )
                                                ] = True

                                        else:
                                            continue

                                        cell.append(
                                            self.paragraph_handler.to_xml(
                                                list_item_data
                                            )
                                        )

                                # Normal paragraph
                                else:
                                    cell.append(
                                        self.paragraph_handler.to_xml(
                                            item
                                        )
                                    )

                    # --------------------------------
                    # Flattened Simple Cell
                    # --------------------------------

                    elif (
                        "text" in cell_data
                        or "runs" in cell_data
                        or any(
                            key in cell_data
                            for key in (
                                "spacing",
                                "indent",
                                "indentation",
                                "alignment",
                                "align",
                                "style",
                                "pStyle",
                                "characterStyle",
                                "rStyle",
                                "markProperties",
                                "numbering",
                                "tabs",
                                "breaks",
                                "bullet",
                                "heading",
                            )
                        )
                    ):
                        paragraph_data = dict(
                            cell_data
                        )

                        paragraph_data.pop(
                            "type",
                            None,
                        )

                        # Remove cell-only properties.
                        cell_only_keys = (
                            "colSpan",
                            "gridSpan",
                            "columnSpan",
                            "rowSpan",
                            "vMerge",
                            "verticalMerge",
                            "vAlign",
                            "verticalAlignment",
                            "width",
                            "cellWidth",
                            "bg",
                            "background",
                            "borders",
                            "tableCellBorders",
                            "hideMark",
                        )

                        for key in cell_only_keys:
                            paragraph_data.pop(
                                key,
                                None,
                            )

                        cell.append(
                            self.paragraph_handler.to_xml(
                                paragraph_data
                            )
                        )

                    else:
                        cell.append(
                            ET.Element(
                                qn("w:p")
                            )
                        )

                # --------------------------------
                # Invalid Cell Fallback
                # --------------------------------

                else:
                    cell.append(
                        ET.Element(
                            qn("w:p")
                        )
                    )

        return table