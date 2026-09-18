"""Handler for Structured Document Tags / Content Controls (w:sdt, w:sdtPr, w:sdtContent)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class ContentControlsHandler(BaseHandler):
    """Handles parsing and reconstructing Structured Document Tags (SDT)."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a w:sdt element to a JSON content control AST dictionary."""
        sdt_dict: dict[str, Any] = {"type": "contentControl"}
        sdt_pr = element.find(qn("w:sdtPr"))

        if sdt_pr is not None:
            props: dict[str, Any] = {}

            # Tag & Alias
            tag_el = sdt_pr.find(qn("w:tag"))
            if tag_el is not None:
                props["tag"] = tag_el.attrib.get(qn("w:val"), "")

            alias_el = sdt_pr.find(qn("w:alias"))
            if alias_el is not None:
                props["alias"] = alias_el.attrib.get(qn("w:val"), "")

            id_el = sdt_pr.find(qn("w:id"))
            if id_el is not None:
                props["id"] = id_el.attrib.get(qn("w:val"), "")

            # Control type
            for c_type in ("date", "dropDownList", "comboBox", "checkbox", "text", "equation"):
                c_el = sdt_pr.find(qn(f"w:{c_type}"))
                if c_el is not None:
                    props["controlType"] = c_type
                    break

            if props:
                sdt_dict["properties"] = props

        return sdt_dict

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a w:sdt element from a content control AST dictionary."""
        sdt = ET.Element(qn("w:sdt"))
        props = data.get("properties", {})

        sdt_pr = ET.SubElement(sdt, qn("w:sdtPr"))
        if "alias" in props:
            ET.SubElement(sdt_pr, qn("w:alias"), {qn("w:val"): str(props["alias"])})
        if "tag" in props:
            ET.SubElement(sdt_pr, qn("w:tag"), {qn("w:val"): str(props["tag"])})
        if "id" in props:
            ET.SubElement(sdt_pr, qn("w:id"), {qn("w:val"): str(props["id"])})

        c_type = props.get("controlType")
        if c_type:
            ET.SubElement(sdt_pr, qn(f"w:{c_type}"))

        # Content container
        ET.SubElement(sdt, qn("w:sdtContent"))

        return sdt


__all__ = ["ContentControlsHandler"]
