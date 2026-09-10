from typing import Any
import xml.etree.ElementTree as ET

from handlers.base import BaseHandler, qn, local_name


from config import (
    PAGE_SIZES,
    PAGE_SIZE_MAP,
    DEFAULT_PAGE_WIDTH,
    DEFAULT_PAGE_HEIGHT,
    DEFAULT_ORIENTATION,
)


# --------------------------------
# Sections Handler
# --------------------------------

class SectionsHandler(BaseHandler):

    # --------------------------------
    # JSON Conversion
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> dict[str, Any]:

        result: dict[str, Any] = {}

        if not simple:
            result["type"] = self.tag_to_name("w:sectPr")

        # --------------------------------
        # Page Size
        # --------------------------------

        pg_sz = element.find(qn("w:pgSz"))

        w_val = None
        h_val = None
        orientation = DEFAULT_ORIENTATION
        code_val = None

        if pg_sz is not None:
            w_raw = pg_sz.attrib.get(qn("w:w"), "")
            h_raw = pg_sz.attrib.get(qn("w:h"), "")

            w_val = (
                int(w_raw)
                if w_raw.isdigit()
                else w_raw
            )

            h_val = (
                int(h_raw)
                if h_raw.isdigit()
                else h_raw
            )

            orientation = pg_sz.attrib.get(
                qn("w:orient"),
                DEFAULT_ORIENTATION,
            )

            code_raw = pg_sz.attrib.get(qn("w:code"))

            if code_raw:
                code_val = (
                    int(code_raw)
                    if code_raw.isdigit()
                    else code_raw
                )

        # --------------------------------
        # Page Margins
        # --------------------------------

        pg_mar = element.find(qn("w:pgMar"))
        margins: dict[str, Any] = {}

        if pg_mar is not None:
            margin_attributes = [
                ("w:top", "top"),
                ("w:right", "right"),
                ("w:bottom", "bottom"),
                ("w:left", "left"),
                ("w:header", "header"),
                ("w:footer", "footer"),
                ("w:gutter", "gutter"),
            ]

            for attr, key in margin_attributes:
                value = pg_mar.attrib.get(qn(attr))

                if value is None:
                    continue

                if value.isdigit() or (
                    value.startswith("-")
                    and value[1:].isdigit()
                ):
                    margins[key] = int(value)
                else:
                    margins[key] = value

        # --------------------------------
        # Simple Page Representation
        # --------------------------------

        if simple:
            page_obj: dict[str, Any] = {}

            if w_val and h_val:
                standard_size = PAGE_SIZES.get((w_val, h_val))

                if standard_size:
                    page_obj["size"] = standard_size
                else:
                    page_obj["size"] = {
                        "width": w_val,
                        "height": h_val,
                    }

            if orientation and orientation != DEFAULT_ORIENTATION:
                page_obj["orientation"] = orientation
            elif "size" in page_obj and orientation:
                page_obj["orientation"] = orientation

            if code_val is not None:
                page_obj["code"] = code_val

            if margins:
                page_obj["margins"] = margins

            if page_obj:
                result["page"] = page_obj

        # --------------------------------
        # Full Page Representation
        # --------------------------------

        else:
            if w_val is not None and h_val is not None:
                size_data = {
                    "width": w_val,
                    "height": h_val,
                    "orientation": orientation,
                }

                if code_val is not None:
                    size_data["code"] = code_val

                result["pageSize"] = size_data

            if margins:
                result["margins"] = margins

        # --------------------------------
        # Columns
        # --------------------------------

        cols = element.find(qn("w:cols"))

        if cols is not None:
            columns_data: dict[str, Any] = {}

            for key, value in cols.attrib.items():
                clean_key = local_name(key)

                if value.isdigit() or (
                    value.startswith("-")
                    and value[1:].isdigit()
                ):
                    columns_data[clean_key] = int(value)
                else:
                    columns_data[clean_key] = value

            column_list: list[dict[str, Any]] = []

            for column in cols.findall(qn("w:col")):
                column_data: dict[str, Any] = {}

                for key, value in column.attrib.items():
                    clean_key = local_name(key)

                    if value.isdigit():
                        column_data[clean_key] = int(value)
                    else:
                        column_data[clean_key] = value

                column_list.append(column_data)

            if column_list:
                columns_data["columns"] = column_list

            if columns_data:
                result["columns"] = columns_data

        # --------------------------------
        # Section Type
        # --------------------------------

        section_type = element.find(qn("w:type"))

        if section_type is not None:
            result["sectionType"] = section_type.attrib.get(
                qn("w:val"),
                "",
            )

        # --------------------------------
        # Headers
        # --------------------------------

        headers: list[dict[str, str]] = []

        for header in element.findall(qn("w:headerReference")):
            headers.append(
                {
                    "type": header.attrib.get(
                        qn("w:type"),
                        "default",
                    ),
                    "relationshipId": header.attrib.get(
                        qn("r:id"),
                        "",
                    ),
                }
            )

        if headers:
            result["headers"] = headers

        # --------------------------------
        # Footers
        # --------------------------------

        footers: list[dict[str, str]] = []

        for footer in element.findall(qn("w:footerReference")):
            footers.append(
                {
                    "type": footer.attrib.get(
                        qn("w:type"),
                        "default",
                    ),
                    "relationshipId": footer.attrib.get(
                        qn("r:id"),
                        "",
                    ),
                }
            )

        if footers:
            result["footers"] = footers

        # --------------------------------
        # Different First Page
        # --------------------------------

        if element.find(qn("w:titlePg")) is not None:
            result["titlePg"] = True

        # --------------------------------
        # Page Number Type
        # --------------------------------

        pg_num = element.find(qn("w:pgNumType"))

        if pg_num is not None:
            result["pgNumType"] = {
                local_name(key): (
                    int(value)
                    if value.isdigit()
                    else value
                )
                for key, value in pg_num.attrib.items()
            }

        # --------------------------------
        # Document Grid
        # --------------------------------

        doc_grid = element.find(qn("w:docGrid"))

        if doc_grid is not None:
            result["docGrid"] = {
                local_name(key): (
                    int(value)
                    if value.isdigit()
                    else value
                )
                for key, value in doc_grid.attrib.items()
            }

        # --------------------------------
        # Form Protection
        # --------------------------------

        form_protection = element.find(qn("w:formProt"))

        if form_protection is not None:
            value = form_protection.attrib.get(
                qn("w:val"),
                "true",
            )

            if value not in ("0", "false"):
                result["formProt"] = True

        # --------------------------------
        # Text Direction
        # --------------------------------

        text_direction = element.find(qn("w:textDirection"))

        if text_direction is not None:
            result["textDirection"] = text_direction.attrib.get(
                qn("w:val"),
                "",
            )

        # --------------------------------
        # Vertical Alignment
        # --------------------------------

        vertical_alignment = element.find(qn("w:vAlign"))

        if vertical_alignment is not None:
            result["vAlign"] = vertical_alignment.attrib.get(
                qn("w:val"),
                "",
            )

        # --------------------------------
        # RTL Gutter
        # --------------------------------

        if element.find(qn("w:rtlGutter")) is not None:
            result["rtlGutter"] = True

        # --------------------------------
        # Bidirectional Section
        # --------------------------------

        if element.find(qn("w:bidi")) is not None:
            result["bidi"] = True

        return result

    # --------------------------------
    # XML Conversion
    # --------------------------------

    def to_xml(self, data: dict[str, Any]) -> ET.Element:

        sect_pr = ET.Element(qn("w:sectPr"))

        # --------------------------------
        # Headers
        # --------------------------------

        header_list = (
            data.get("headerReference")
            or data.get("headers", [])
        )

        for header in header_list:
            attrs = {
                qn("w:type"): header.get(
                    "type",
                    "default",
                )
            }

            relationship_id = header.get("relationshipId")

            if relationship_id:
                attrs[qn("r:id")] = relationship_id

            ET.SubElement(
                sect_pr,
                qn("w:headerReference"),
                attrs,
            )

        # --------------------------------
        # Footers
        # --------------------------------

        footer_list = (
            data.get("footerReference")
            or data.get("footers", [])
        )

        for footer in footer_list:
            attrs = {
                qn("w:type"): footer.get(
                    "type",
                    "default",
                )
            }

            relationship_id = footer.get("relationshipId")

            if relationship_id:
                attrs[qn("r:id")] = relationship_id

            ET.SubElement(
                sect_pr,
                qn("w:footerReference"),
                attrs,
            )

        # --------------------------------
        # Different First Page
        # --------------------------------

        if data.get("titlePg") or data.get("differentFirstPage"):
            ET.SubElement(
                sect_pr,
                qn("w:titlePg"),
            )

        # --------------------------------
        # Section Type
        # --------------------------------

        section_type = (
            data.get("sectionType")
            or data.get("type")
        )

        if section_type and section_type not in (
            "section",
            "sectionProperties",
        ):
            ET.SubElement(
                sect_pr,
                qn("w:type"),
                {
                    qn("w:val"): str(section_type),
                },
            )

        # --------------------------------
        # Page Size
        # --------------------------------

        page_size = data.get("pageSize")
        page_info = data.get("page")

        width = DEFAULT_PAGE_WIDTH
        height = DEFAULT_PAGE_HEIGHT
        orientation = DEFAULT_ORIENTATION

        # --------------------------------
        # Simple Page Format
        # --------------------------------

        if isinstance(page_info, dict):
            raw_size = page_info.get(
                "size",
                "a4",
            )

            orientation = page_info.get(
                "orientation",
                DEFAULT_ORIENTATION,
            ).lower()

            if (
                isinstance(raw_size, str)
                and raw_size.lower() in PAGE_SIZE_MAP
            ):
                width, height = PAGE_SIZE_MAP[
                    raw_size.lower()
                ]

            elif isinstance(raw_size, dict):
                width = raw_size.get(
                    "width",
                    width,
                )
                height = raw_size.get(
                    "height",
                    height,
                )

            # Keep width/height consistent with landscape.
            if orientation == "landscape" and width < height:
                width, height = height, width

            size_attrs = {
                qn("w:w"): str(width),
                qn("w:h"): str(height),
            }

            if orientation != DEFAULT_ORIENTATION:
                size_attrs[qn("w:orient")] = orientation

            if "code" in page_info:
                size_attrs[qn("w:code")] = str(
                    page_info["code"]
                )

            ET.SubElement(
                sect_pr,
                qn("w:pgSz"),
                size_attrs,
            )

        # --------------------------------
        # Full Page Size Format
        # --------------------------------

        elif page_size:
            size_attrs: dict[str, str] = {}

            if "width" in page_size:
                size_attrs[qn("w:w")] = str(
                    page_size["width"]
                )

            if "height" in page_size:
                size_attrs[qn("w:h")] = str(
                    page_size["height"]
                )

            if (
                page_size.get("orientation")
                and page_size["orientation"] != DEFAULT_ORIENTATION
            ):
                size_attrs[qn("w:orient")] = str(
                    page_size["orientation"]
                )

            if "code" in page_size:
                size_attrs[qn("w:code")] = str(
                    page_size["code"]
                )

            ET.SubElement(
                sect_pr,
                qn("w:pgSz"),
                size_attrs,
            )

        # --------------------------------
        # Margins
        # --------------------------------

        margins = (
            page_info.get("margins")
            if isinstance(page_info, dict)
            else None
        )

        margins = (
            margins
            or data.get("pageMargins")
            or data.get("margins")
        )

        if margins:
            margin_attrs: dict[str, str] = {}

            margin_mapping = [
                ("top", "w:top"),
                ("right", "w:right"),
                ("bottom", "w:bottom"),
                ("left", "w:left"),
                ("header", "w:header"),
                ("footer", "w:footer"),
                ("gutter", "w:gutter"),
            ]

            for key, attr in margin_mapping:
                if key not in margins:
                    continue

                value = margins[key]

                # Convert point values to twips.
                if isinstance(value, str):
                    if value.endswith("pt"):
                        try:
                            value = int(
                                float(value[:-2]) * 20
                            )
                        except ValueError:
                            pass

                    elif value.endswith("in"):
                        try:
                            value = int(
                                float(value[:-2]) * 1440
                            )
                        except ValueError:
                            pass

                elif isinstance(value, (int, float)):
                    # Simple page config may use common point values.
                    if (
                        isinstance(page_info, dict)
                        and isinstance(
                            page_info.get("size"),
                            str,
                        )
                        and value in (
                            72,
                            36,
                            54,
                            18,
                            108,
                        )
                    ):
                        value = int(value * 20)

                margin_attrs[qn(attr)] = str(value)

            ET.SubElement(
                sect_pr,
                qn("w:pgMar"),
                margin_attrs,
            )

        # --------------------------------
        # Columns
        # --------------------------------

        columns = data.get("columns")

        if columns:
            columns_attrs: dict[str, str] = {}

            for key, value in columns.items():
                if key == "columns":
                    continue

                columns_attrs[
                    qn(f"w:{key}")
                ] = str(value)

            cols_element = ET.SubElement(
                sect_pr,
                qn("w:cols"),
                columns_attrs,
            )

            for column_info in columns.get(
                "columns",
                [],
            ):
                column_attrs = {
                    qn(f"w:{key}"): str(value)
                    for key, value in column_info.items()
                }

                ET.SubElement(
                    cols_element,
                    qn("w:col"),
                    column_attrs,
                )

        # --------------------------------
        # Page Number Type
        # --------------------------------

        if data.get("pgNumType"):
            page_number_attrs = {
                qn(f"w:{key}"): str(value)
                for key, value in data["pgNumType"].items()
            }

            ET.SubElement(
                sect_pr,
                qn("w:pgNumType"),
                page_number_attrs,
            )

        # --------------------------------
        # Form Protection
        # --------------------------------

        if data.get("formProt"):
            ET.SubElement(
                sect_pr,
                qn("w:formProt"),
            )

        # --------------------------------
        # Vertical Alignment
        # --------------------------------

        if data.get("vAlign"):
            ET.SubElement(
                sect_pr,
                qn("w:vAlign"),
                {
                    qn("w:val"): str(
                        data["vAlign"]
                    )
                },
            )

        # --------------------------------
        # Text Direction
        # --------------------------------

        if data.get("textDirection"):
            ET.SubElement(
                sect_pr,
                qn("w:textDirection"),
                {
                    qn("w:val"): str(
                        data["textDirection"]
                    )
                },
            )

        # --------------------------------
        # RTL Gutter
        # --------------------------------

        if data.get("rtlGutter"):
            ET.SubElement(
                sect_pr,
                qn("w:rtlGutter"),
            )

        # --------------------------------
        # Bidirectional Section
        # --------------------------------

        if data.get("bidi"):
            ET.SubElement(
                sect_pr,
                qn("w:bidi"),
            )

        # --------------------------------
        # Document Grid
        # --------------------------------

        if data.get("docGrid"):
            grid_attrs = {
                qn(f"w:{key}"): str(value)
                for key, value in data["docGrid"].items()
            }

            ET.SubElement(
                sect_pr,
                qn("w:docGrid"),
                grid_attrs,
            )

        # --------------------------------
        # Schema Ordering
        # --------------------------------

        from handlers.base import (
            SECTPR_ORDER,
            sort_children_by_schema,
        )

        sort_children_by_schema(
            sect_pr,
            SECTPR_ORDER,
        )

        return sect_pr