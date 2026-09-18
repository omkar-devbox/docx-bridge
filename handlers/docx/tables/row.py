"""Handler for table rows (w:tr, w:trPr)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name, TRPR_ORDER, sort_children_by_schema
from handlers.docx.tables.cell import TableCellHandler


class TableRowHandler(BaseHandler):
    """Handles parsing and reconstructing w:tr and w:trPr elements."""

    def __init__(self, cell_handler: TableCellHandler | None = None):
        self.cell_handler = cell_handler or TableCellHandler()

    def to_json(self, element: ET.Element, simple: bool = False) -> dict[str, Any]:
        """Convert a w:tr element to a JSON row AST dictionary."""
        row_dict: dict[str, Any] = {"type": "tableRow"}
        tr_pr = element.find(qn("w:trPr"))

        if tr_pr is not None:
            props: dict[str, Any] = {}

            # Row height
            tr_height = tr_pr.find(qn("w:trHeight"))
            if tr_height is not None:
                h_val = tr_height.attrib.get(qn("w:val"))
                props["height"] = {
                    "value": int(h_val) if h_val and h_val.isdigit() else h_val,
                    "rule": tr_height.attrib.get(qn("w:hRule"), "auto"),
                }

            # Cant split
            cant_split = tr_pr.find(qn("w:cantSplit"))
            if cant_split is not None:
                props["cantSplit"] = True

            # Table header
            tbl_header = tr_pr.find(qn("w:tblHeader"))
            if tbl_header is not None:
                props["tblHeader"] = True

            if props:
                row_dict["properties"] = props

        # Parse cells
        cells: list[dict[str, Any]] = []
        for child in element:
            if local_name(child.tag) == "tc":
                c_data = self.cell_handler.to_json(child, simple=simple)
                if c_data:
                    cells.append(c_data)
        if cells:
            row_dict["cells"] = cells

        return row_dict

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a w:tr element from a JSON row AST dictionary."""
        tr = ET.Element(qn("w:tr"))
        props = data.get("properties", {})

        if props:
            tr_pr = ET.SubElement(tr, qn("w:trPr"))

            # Cant Split
            if props.get("cantSplit"):
                ET.SubElement(tr_pr, qn("w:cantSplit"))

            # Table Header
            if props.get("tblHeader"):
                ET.SubElement(tr_pr, qn("w:tblHeader"))

            # Height
            h_info = props.get("height")
            if isinstance(h_info, dict):
                attrib = {qn("w:val"): str(h_info.get("value", 0))}
                if "rule" in h_info:
                    attrib[qn("w:hRule")] = str(h_info["rule"])
                ET.SubElement(tr_pr, qn("w:trHeight"), attrib)

            sort_children_by_schema(tr_pr, TRPR_ORDER)

        # Cells
        for cell_data in data.get("cells", []):
            tr.append(self.cell_handler.to_xml(cell_data))

        return tr


__all__ = ["TableRowHandler"]
