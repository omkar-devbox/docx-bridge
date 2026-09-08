"""Handler for w:tbl (table) elements."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name
from handlers.paragraph import ParagraphHandler


class TableHandler(BaseHandler):
    """Handles w:tbl table element conversion to/from JSON."""

    def __init__(self, paragraph_handler: ParagraphHandler | None = None):
        self.paragraph_handler = paragraph_handler or ParagraphHandler()

    def to_json(self, element: ET.Element, simple: bool = False) -> dict[str, Any]:
        """Convert w:tbl element to JSON dictionary with master-tags values as keys."""
        table_properties: dict[str, Any] = {}
        tbl_pr = element.find(qn("w:tblPr"))
        if tbl_pr is not None:
            # Table Style
            tbl_style = tbl_pr.find(qn("w:tblStyle"))
            if tbl_style is not None:
                table_properties["style"] = tbl_style.attrib.get(qn("w:val"), "")

            # Table Width
            tbl_w = tbl_pr.find(qn("w:tblW"))
            if tbl_w is not None:
                w_val = tbl_w.attrib.get(qn("w:w"), "")
                width_dict = {
                    "value": int(w_val) if w_val.isdigit() else w_val,
                    "type": tbl_w.attrib.get(qn("w:type"), "auto"),
                }
                table_properties["width"] = width_dict

            # Alignment
            jc = tbl_pr.find(qn("w:jc"))
            if jc is not None:
                table_properties["alignment"] = jc.attrib.get(qn("w:val"), "")

            # Floating Table Position Properties (w:tblpPr)
            tblp_pr = tbl_pr.find(qn("w:tblpPr"))
            if tblp_pr is not None:
                tblp_dict: dict[str, Any] = {}
                for k, v in tblp_pr.attrib.items():
                    key = local_name(k)
                    val = int(v) if v.isdigit() or (v.startswith("-") and v[1:].isdigit()) else v
                    tblp_dict[key] = val
                table_properties["positionProperties"] = tblp_dict

            # Table Cell Margins (w:tblCellMar)
            tbl_cell_mar = tbl_pr.find(qn("w:tblCellMar"))
            if tbl_cell_mar is not None:
                mar_dict: dict[str, Any] = {}
                for side in ("top", "left", "bottom", "right"):
                    side_el = tbl_cell_mar.find(qn(f"w:{side}"))
                    if side_el is not None:
                        w_val = side_el.attrib.get(qn("w:w"), "0")
                        mar_dict[side] = {
                            "value": int(w_val) if w_val.isdigit() else w_val,
                            "type": side_el.attrib.get(qn("w:type"), "dxa"),
                        }
                if mar_dict:
                    table_properties["cellMargins"] = mar_dict

            # Table Cell Spacing (w:tblCellSpacing)
            tbl_spacing = tbl_pr.find(qn("w:tblCellSpacing"))
            if tbl_spacing is not None:
                w_val = tbl_spacing.attrib.get(qn("w:w"), "")
                sp_dict = {
                    "value": int(w_val) if w_val.isdigit() else w_val,
                    "type": tbl_spacing.attrib.get(qn("w:type"), "dxa"),
                }
                table_properties["cellSpacing"] = sp_dict

            # Table Indent (w:tblInd)
            tbl_ind = tbl_pr.find(qn("w:tblInd"))
            if tbl_ind is not None:
                w_val = tbl_ind.attrib.get(qn("w:w"), "")
                ind_dict = {
                    "value": int(w_val) if w_val.isdigit() else w_val,
                    "type": tbl_ind.attrib.get(qn("w:type"), "dxa"),
                }
                table_properties["indent"] = ind_dict

            # Table Layout (w:tblLayout)
            tbl_layout = tbl_pr.find(qn("w:tblLayout"))
            if tbl_layout is not None:
                table_properties["layout"] = tbl_layout.attrib.get(qn("w:type"), "fixed")

            # Table Look (w:tblLook)
            tbl_look = tbl_pr.find(qn("w:tblLook"))
            if tbl_look is not None:
                look_dict: dict[str, Any] = {}
                for k, v in tbl_look.attrib.items():
                    look_dict[local_name(k)] = v
                table_properties["look"] = look_dict

            # Table Shading (w:shd)
            tbl_shd = tbl_pr.find(qn("w:shd"))
            if tbl_shd is not None:
                shd_dict: dict[str, Any] = {}
                for k, v in tbl_shd.attrib.items():
                    shd_dict[local_name(k)] = v
                table_properties["shading"] = shd_dict

            # Table Borders (w:tblBorders)
            tbl_borders = tbl_pr.find(qn("w:tblBorders"))
            if tbl_borders is not None:
                bdr_dict: dict[str, Any] = {}
                for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                    b_el = tbl_borders.find(qn(f"w:{side}"))
                    if b_el is not None:
                        bdr_dict[side] = {local_name(k): v for k, v in b_el.attrib.items()}
                if bdr_dict:
                    table_properties["borders"] = bdr_dict

        # Table Grid (w:tblGrid -> grid)
        grid_cols: list[int | str] = []
        tbl_grid = element.find(qn("w:tblGrid"))
        if tbl_grid is not None:
            for col in tbl_grid.findall(qn("w:gridCol")):
                w_val = col.attrib.get(qn("w:w"), "")
                grid_cols.append(int(w_val) if w_val.isdigit() else w_val)

        # Rows (w:tr -> tableRow)
        rows: list[Any] = []
        for tr in element.findall(qn("w:tr")):
            row_properties: dict[str, Any] = {}
            tr_pr = tr.find(qn("w:trPr"))
            if tr_pr is not None:
                if tr_pr.find(qn("w:tblHeader")) is not None:
                    row_properties["header"] = True
                if tr_pr.find(qn("w:cantSplit")) is not None:
                    row_properties["cantSplit"] = True
                jc = tr_pr.find(qn("w:jc"))
                if jc is not None:
                    row_properties["alignment"] = jc.attrib.get(qn("w:val"), "")
                tbl_spacing = tr_pr.find(qn("w:tblCellSpacing"))
                if tbl_spacing is not None:
                    w_val = tbl_spacing.attrib.get(qn("w:w"), "")
                    sp_dict = {
                        "value": int(w_val) if w_val.isdigit() else w_val,
                        "type": tbl_spacing.attrib.get(qn("w:type"), "dxa"),
                    }
                    row_properties["cellSpacing"] = sp_dict
                tr_height = tr_pr.find(qn("w:trHeight"))
                if tr_height is not None:
                    h_val = tr_height.attrib.get(qn("w:val"), "")
                    height_num = int(h_val) if h_val.isdigit() else h_val
                    h_rule = tr_height.attrib.get(qn("w:hRule"))
                    row_properties["height"] = height_num
                    if h_rule:
                        row_properties["heightRule"] = h_rule

            # Cells (w:tc -> tableCell)
            cells: list[Any] = []
            for tc in tr.findall(qn("w:tc")):
                cell_properties: dict[str, Any] = {}
                tc_pr = tc.find(qn("w:tcPr"))
                if tc_pr is not None:
                    tc_w = tc_pr.find(qn("w:tcW"))
                    if tc_w is not None:
                        w_val = tc_w.attrib.get(qn("w:w"), "")
                        cell_w_dict = {
                            "value": int(w_val) if w_val.isdigit() else w_val,
                            "type": tc_w.attrib.get(qn("w:type"), "auto"),
                        }
                        cell_properties["width"] = cell_w_dict

                    grid_span = tc_pr.find(qn("w:gridSpan"))
                    if grid_span is not None:
                        span_val = grid_span.attrib.get(qn("w:val"), "1")
                        span_num = int(span_val) if span_val.isdigit() else span_val
                        cell_properties["gridSpan"] = span_num

                    v_merge = tc_pr.find(qn("w:vMerge"))
                    if v_merge is not None:
                        merge_val = v_merge.attrib.get(qn("w:val"), "continue")
                        cell_properties["vMerge"] = merge_val

                    v_align = tc_pr.find(qn("w:vAlign"))
                    if v_align is not None:
                        cell_properties["vAlign"] = v_align.attrib.get(qn("w:val"), "")

                    hide_mark = tc_pr.find(qn("w:hideMark"))
                    if hide_mark is not None:
                        cell_properties["hideMark"] = True

                    # Cell Shading (w:shd)
                    tc_shd = tc_pr.find(qn("w:shd"))
                    if tc_shd is not None:
                        c_shd_dict: dict[str, Any] = {}
                        for k, v in tc_shd.attrib.items():
                            c_shd_dict[local_name(k)] = v
                        cell_properties["shading"] = c_shd_dict

                    # Cell Borders (w:tcBorders) - only if not simple or has custom borders
                    tc_borders = tc_pr.find(qn("w:tcBorders"))
                    if tc_borders is not None:
                        tc_bdr_dict: dict[str, Any] = {}
                        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                            b_el = tc_borders.find(qn(f"w:{side}"))
                            if b_el is not None:
                                tc_bdr_dict[side] = {local_name(k): v for k, v in b_el.attrib.items()}
                        if tc_bdr_dict:
                            cell_properties["borders"] = tc_bdr_dict

                # Cell content: iterate through direct children in order (paragraphs AND nested tables)
                content: list[dict[str, Any]] = []
                for child in tc:
                    if child.tag == qn("w:p"):
                        content.append(self.paragraph_handler.to_json(child, simple=simple))
                    elif child.tag == qn("w:tbl"):
                        content.append(self.to_json(child, simple=simple))

                if simple:
                    # In simple mode, simplify cell representation
                    # Detect a single paragraph: in simple mode paragraphs don't have type field,
                    # tables have 'rows'. So a single non-table content item is a paragraph.
                    def _is_simple_para(item):
                        """Return True if item is a paragraph in simple mode (no 'rows' key)."""
                        return isinstance(item, dict) and "rows" not in item

                    if len(content) == 1 and _is_simple_para(content[0]):
                        p0 = content[0]
                        # Check if p0 has only 'text' or simple styling
                        p_keys = set(p0.keys())
                        if not cell_properties and p_keys == {"text"}:
                            cells.append(p0["text"])
                        elif not cell_properties and not p_keys:
                            cells.append("")
                        else:
                            # Flatten into single cell object
                            c_obj: dict[str, Any] = {}
                            if "width" in cell_properties:
                                c_obj["width"] = cell_properties["width"]
                            if "gridSpan" in cell_properties:
                                c_obj["colSpan"] = cell_properties["gridSpan"]
                            if "vMerge" in cell_properties:
                                c_obj["rowSpan"] = cell_properties["vMerge"]
                            if "vAlign" in cell_properties:
                                c_obj["vAlign"] = cell_properties["vAlign"]
                            if "shading" in cell_properties and "fill" in cell_properties["shading"]:
                                c_obj["bg"] = cell_properties["shading"]["fill"]
                            if "borders" in cell_properties:
                                c_obj["borders"] = cell_properties["borders"]
                            for pk in p_keys:
                                c_obj[pk] = p0[pk]
                            cells.append(c_obj)
                    elif not content and not cell_properties:
                        cells.append("")
                    else:
                        c_dict: dict[str, Any] = {}
                        if "width" in cell_properties:
                            c_dict["width"] = cell_properties["width"]
                        if "gridSpan" in cell_properties:
                            c_dict["colSpan"] = cell_properties["gridSpan"]
                        if "vMerge" in cell_properties:
                            c_dict["rowSpan"] = cell_properties["vMerge"]
                        if "vAlign" in cell_properties:
                            c_dict["vAlign"] = cell_properties["vAlign"]
                        if "shading" in cell_properties and "fill" in cell_properties["shading"]:
                            c_dict["bg"] = cell_properties["shading"]["fill"]
                        if "borders" in cell_properties:
                            c_dict["borders"] = cell_properties["borders"]
                        c_dict["content"] = content
                        cells.append(c_dict)
                else:
                    cells.append({
                        "type": self.tag_to_name("w:tc"),
                        "properties": cell_properties,
                        "content": content,
                    })

            if simple and not row_properties:
                # Row is directly the list of cells
                rows.append(cells)
            else:
                rows.append({
                    "type": self.tag_to_name("w:tr"),
                    "properties": row_properties,
                    "cells": cells,
                })

        if simple:
            result: dict[str, Any] = {
                "type": "table",
                "rows": rows,
            }
            if "style" in table_properties:
                result["style"] = table_properties["style"]
            if "alignment" in table_properties:
                result["align"] = table_properties["alignment"]
            if "width" in table_properties:
                result["width"] = table_properties["width"]
            if "borders" in table_properties:
                result["borders"] = table_properties["borders"]
            if "cellMargins" in table_properties:
                result["cellMargins"] = table_properties["cellMargins"]
            if "indent" in table_properties:
                result["indent"] = table_properties["indent"]
            if "layout" in table_properties:
                result["layout"] = table_properties["layout"]
            if "look" in table_properties:
                result["look"] = table_properties["look"]
            if "shading" in table_properties:
                result["shading"] = table_properties["shading"]
            if grid_cols:
                result["grid"] = grid_cols
        else:
            result: dict[str, Any] = {
                "type": self.tag_to_name("w:tbl"),
                "properties": table_properties,
                "rows": rows,
            }
            if grid_cols:
                result["grid"] = grid_cols

        return result

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert JSON table representation to w:tbl XML element."""
        tbl = ET.Element(qn("w:tbl"))
        props = dict(data.get("tableProperties") or data.get("properties") or {})
        for k in (
            "style", "tableStyle", "alignment", "align", "width", "tableWidth",
            "borders", "layout", "cellMargins", "tableCellMargins",
            "indent", "tableIndent", "look", "tableLook",
            "cellSpacing", "tableCellSpacing", "shading", "positionProperties",
        ):
            if k in data and k not in props:
                props[k] = data[k]

        # w:tblPr
        tbl_pr = ET.SubElement(tbl, qn("w:tblPr"))

        # Floating table position (tblpPr)
        pos_props = props.get("tablePositionProperties") or props.get("positionProperties")
        if pos_props:
            tblp_attrs: dict[str, str] = {}
            for k, v in pos_props.items():
                tblp_attrs[qn(f"w:{k}")] = str(v)
            ET.SubElement(tbl_pr, qn("w:tblpPr"), tblp_attrs)

        # Style
        style_val = props.get("tableStyle") or props.get("style")
        if style_val:
            ET.SubElement(tbl_pr, qn("w:tblStyle"), {qn("w:val"): str(style_val)})

        # Width
        w_info = props.get("tableWidth") or props.get("width")
        if w_info is not None:
            if isinstance(w_info, (int, str)) and str(w_info).isdigit():
                tbl_w_attrs = {qn("w:w"): str(w_info), qn("w:type"): "dxa"}
            elif isinstance(w_info, dict):
                tbl_w_attrs = {
                    qn("w:w"): str(w_info.get("value", 0)),
                    qn("w:type"): str(w_info.get("type", "auto")),
                }
            else:
                tbl_w_attrs = {qn("w:w"): "0", qn("w:type"): "auto"}
            ET.SubElement(tbl_pr, qn("w:tblW"), tbl_w_attrs)

        # Alignment
        align_val = props.get("alignment") or props.get("align")
        if align_val:
            ET.SubElement(tbl_pr, qn("w:jc"), {qn("w:val"): str(align_val)})

        # Cell Spacing
        sp_info = props.get("tableCellSpacing") or props.get("cellSpacing")
        if sp_info:
            sp_attrs = {
                qn("w:w"): str(sp_info.get("value", 0)),
                qn("w:type"): str(sp_info.get("type", "dxa")),
            }
            ET.SubElement(tbl_pr, qn("w:tblCellSpacing"), sp_attrs)

        # Indent
        ind_info = props.get("tableIndent") or props.get("indent")
        if ind_info:
            ind_attrs = {
                qn("w:w"): str(ind_info.get("value", 0)),
                qn("w:type"): str(ind_info.get("type", "dxa")),
            }
            ET.SubElement(tbl_pr, qn("w:tblInd"), ind_attrs)

        # Borders
        borders_info = props.get("tableBorders") or props.get("borders")
        if borders_info:
            if isinstance(borders_info, dict):
                bdr_el = ET.SubElement(tbl_pr, qn("w:tblBorders"))
                for side, side_attrs in borders_info.items():
                    if isinstance(side_attrs, dict):
                        q_attrs = {qn(f"w:{k}"): str(v) for k, v in side_attrs.items()}
                        ET.SubElement(bdr_el, qn(f"w:{side}"), q_attrs)

        # Shading
        shd_info = props.get("shading")
        if shd_info:
            shd_attrs = {qn(f"w:{k}"): str(v) for k, v in shd_info.items()}
            ET.SubElement(tbl_pr, qn("w:shd"), shd_attrs)

        # Layout
        layout_val = props.get("tableLayout") or props.get("layout")
        if layout_val:
            ET.SubElement(tbl_pr, qn("w:tblLayout"), {qn("w:type"): str(layout_val)})

        # Cell Margins
        mar_info = props.get("tableCellMargins") or props.get("cellMargins")
        if mar_info:
            mar_el = ET.SubElement(tbl_pr, qn("w:tblCellMar"))
            for side, side_data in mar_info.items():
                if isinstance(side_data, dict):
                    side_attrs = {
                        qn("w:w"): str(side_data.get("value", 0)),
                        qn("w:type"): str(side_data.get("type", "dxa")),
                    }
                    ET.SubElement(mar_el, qn(f"w:{side}"), side_attrs)

        # Look
        look_info = props.get("tableLook") or props.get("look")
        if look_info:
            look_attrs = {qn(f"w:{k}"): str(v) for k, v in look_info.items()}
            ET.SubElement(tbl_pr, qn("w:tblLook"), look_attrs)

        # w:tblGrid
        grid_data = data.get("tableGrid") or data.get("grid")
        if grid_data:
            tbl_grid = ET.SubElement(tbl, qn("w:tblGrid"))
            for col_w in grid_data:
                ET.SubElement(tbl_grid, qn("w:gridCol"), {qn("w:w"): str(col_w)})

        # Rows
        for row_data in data.get("rows", []):
            tr = ET.SubElement(tbl, qn("w:tr"))
            if isinstance(row_data, list):
                cells_list = row_data
                r_props = {}
            elif isinstance(row_data, dict):
                cells_list = row_data.get("cells", [])
                r_props = row_data.get("tableRowProperties") or row_data.get("properties", {})
            else:
                cells_list = []
                r_props = {}

            if r_props:
                tr_pr = ET.SubElement(tr, qn("w:trPr"))
                if r_props.get("tableHeader") or r_props.get("header"):
                    ET.SubElement(tr_pr, qn("w:tblHeader"))
                if r_props.get("cantSplitRow") or r_props.get("cantSplit"):
                    ET.SubElement(tr_pr, qn("w:cantSplit"))
                if r_props.get("alignment"):
                    ET.SubElement(tr_pr, qn("w:jc"), {qn("w:val"): str(r_props["alignment"])})
                sp_info = r_props.get("tableCellSpacing") or r_props.get("cellSpacing")
                if sp_info:
                    sp_attrs = {
                        qn("w:w"): str(sp_info.get("value", 0)),
                        qn("w:type"): str(sp_info.get("type", "dxa")),
                    }
                    ET.SubElement(tr_pr, qn("w:tblCellSpacing"), sp_attrs)
                height_val = r_props.get("tableRowHeight") or r_props.get("height")
                if height_val is not None:
                    h_attrs = {qn("w:val"): str(height_val)}
                    if r_props.get("heightRule"):
                        h_attrs[qn("w:hRule")] = str(r_props["heightRule"])
                    ET.SubElement(tr_pr, qn("w:trHeight"), h_attrs)

            for cell_data in cells_list:
                tc = ET.SubElement(tr, qn("w:tc"))
                if isinstance(cell_data, str):
                    # Plain string cell
                    tc_p = ET.SubElement(tc, qn("w:p"))
                    if cell_data:
                        tc_r = ET.SubElement(tc_p, qn("w:r"))
                        tc_t = ET.SubElement(tc_r, qn("w:t"))
                        tc_t.text = cell_data
                        if cell_data.startswith(" ") or cell_data.endswith(" "):
                            tc_t.set(qn("xml:space"), "preserve")
                    continue
                elif isinstance(cell_data, dict):
                    c_props = dict(cell_data.get("tableCellProperties") or cell_data.get("properties") or {})
                    # Collect flat properties directly on cell_data
                    for k in ("colSpan", "gridSpan", "columnSpan", "rowSpan", "vMerge", "verticalMerge",
                              "vAlign", "verticalAlignment", "width", "cellWidth", "bg", "background",
                              "shading", "borders", "tableCellBorders", "hideMark", "hideEndMark"):
                        if k in cell_data and k not in c_props:
                            c_props[k] = cell_data[k]

                    if c_props:
                        tc_pr = ET.SubElement(tc, qn("w:tcPr"))
                        cell_w_info = c_props.get("cellWidth") or c_props.get("width")
                        if cell_w_info is not None:
                            if isinstance(cell_w_info, (int, str)) and str(cell_w_info).isdigit():
                                tc_w_attrs = {qn("w:w"): str(cell_w_info), qn("w:type"): "dxa"}
                            elif isinstance(cell_w_info, dict):
                                tc_w_attrs = {
                                    qn("w:w"): str(cell_w_info.get("value", 0)),
                                    qn("w:type"): str(cell_w_info.get("type", "auto")),
                                }
                            else:
                                tc_w_attrs = {qn("w:w"): "0", qn("w:type"): "auto"}
                            ET.SubElement(tc_pr, qn("w:tcW"), tc_w_attrs)

                        span_val = c_props.get("colSpan") or c_props.get("columnSpan") or c_props.get("gridSpan")
                        if span_val:
                            ET.SubElement(tc_pr, qn("w:gridSpan"), {qn("w:val"): str(span_val)})

                        v_merge_val = c_props.get("rowSpan") or c_props.get("verticalMerge") or c_props.get("vMerge")
                        if v_merge_val:
                            v_attrs = {} if str(v_merge_val) in ("continue", "true", "1") else {qn("w:val"): str(v_merge_val)}
                            ET.SubElement(tc_pr, qn("w:vMerge"), v_attrs)

                        v_align_val = c_props.get("verticalAlignment") or c_props.get("vAlign")
                        if v_align_val:
                            ET.SubElement(tc_pr, qn("w:vAlign"), {qn("w:val"): str(v_align_val)})

                        if c_props.get("hideEndMark") or c_props.get("hideMark"):
                            ET.SubElement(tc_pr, qn("w:hideMark"))

                        # Shading / Background
                        bg_val = c_props.get("bg") or c_props.get("background") or c_props.get("shading")
                        if bg_val:
                            if isinstance(bg_val, str):
                                ET.SubElement(tc_pr, qn("w:shd"), {
                                    qn("w:val"): "clear",
                                    qn("w:color"): "auto",
                                    qn("w:fill"): bg_val.lstrip("#")
                                })
                            elif isinstance(bg_val, dict):
                                c_shd_attrs = {qn(f"w:{k}"): str(v) for k, v in bg_val.items()}
                                ET.SubElement(tc_pr, qn("w:shd"), c_shd_attrs)

                        # Cell borders
                        c_bdr_info = c_props.get("tableCellBorders") or c_props.get("borders")
                        if c_bdr_info and isinstance(c_bdr_info, dict):
                            c_bdr_el = ET.SubElement(tc_pr, qn("w:tcBorders"))
                            for side, side_attrs in c_bdr_info.items():
                                if isinstance(side_attrs, dict):
                                    q_attrs = {qn(f"w:{k}"): str(v) for k, v in side_attrs.items()}
                                    ET.SubElement(c_bdr_el, qn(f"w:{side}"), q_attrs)

                    # Cell content
                    cell_content = cell_data.get("content")
                    if cell_content is not None:
                        if not cell_content:
                            tc.append(ET.Element(qn("w:p")))
                        else:
                            for item in cell_content:
                                if isinstance(item, str):
                                    tc.append(self.paragraph_handler.to_xml({"text": item}))
                                elif isinstance(item, dict):
                                    item_type = item.get("type", "paragraph")
                                    if item_type in ("paragraph", "w:p", self.tag_to_name("w:p"), "p"):
                                        tc.append(self.paragraph_handler.to_xml(item))
                                    elif item_type in ("table", "w:tbl", self.tag_to_name("w:tbl"), "tbl"):
                                        tc.append(self.to_xml(item))
                    elif "text" in cell_data or "runs" in cell_data or any(
                        k in cell_data for k in (
                            "spacing", "indent", "indentation", "alignment", "align",
                            "style", "markProperties", "numbering", "tabs", "breaks"
                        )
                    ):
                        # Direct styled paragraph from flattened cell_data (simple mode)
                        p_dict = dict(cell_data)
                        p_dict.pop("type", None)  # remove type:table if present
                        # Filter out cell-level properties so they don't corrupt paragraph
                        for cp_key in ("colSpan", "gridSpan", "columnSpan", "rowSpan",
                                       "vMerge", "verticalMerge", "vAlign", "verticalAlignment",
                                       "width", "cellWidth", "bg", "background",
                                       "borders", "tableCellBorders", "hideMark"):
                            p_dict.pop(cp_key, None)
                        tc.append(self.paragraph_handler.to_xml(p_dict))
                    else:
                        tc.append(ET.Element(qn("w:p")))
                else:
                    tc.append(ET.Element(qn("w:p")))

        return tbl
