"""Handler for DrawingML layout frames (w:drawing, wp:inline, wp:anchor)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class DrawingHandler(BaseHandler):
    """Handles parsing and reconstructing w:drawing, wp:inline, and wp:anchor layout structures."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a w:drawing element to a JSON drawing frame AST dictionary."""
        drawing_dict: dict[str, Any] = {"type": "drawing"}

        inline = element.find(qn("wp:inline"))
        anchor = element.find(qn("wp:anchor"))
        frame = inline if inline is not None else anchor

        if frame is not None:
            drawing_dict["layout"] = "inline" if inline is not None else "anchor"

            # Extent (wp:extent -> cx, cy)
            extent = frame.find(qn("wp:extent"))
            if extent is not None:
                cx = extent.attrib.get("cx")
                cy = extent.attrib.get("cy")
                drawing_dict["extent"] = {
                    "cx": int(cx) if cx and cx.isdigit() else cx,
                    "cy": int(cy) if cy and cy.isdigit() else cy,
                }

            # DocPr (wp:docPr -> id, name, descr)
            doc_pr = frame.find(qn("wp:docPr"))
            if doc_pr is not None:
                d_id = doc_pr.attrib.get("id")
                drawing_dict["docProperties"] = {
                    "id": int(d_id) if d_id and d_id.isdigit() else d_id,
                    "name": doc_pr.attrib.get("name", ""),
                    "description": doc_pr.attrib.get("descr", ""),
                }

        return drawing_dict

    def to_xml(self, data: dict[str, Any], graphic_element: ET.Element | None = None) -> ET.Element:
        """Construct a w:drawing element with inline/anchor frame."""
        drawing = ET.Element(qn("w:drawing"))
        layout = data.get("layout", "inline")
        tag = qn("wp:inline") if layout == "inline" else qn("wp:anchor")
        frame = ET.SubElement(drawing, tag)

        if layout == "anchor":
            frame.set("distT", "0")
            frame.set("distB", "0")
            frame.set("distL", "0")
            frame.set("distR", "0")
            frame.set("simplePos", "0")
            frame.set("relativeHeight", "251658240")
            frame.set("behindDoc", "0")
            frame.set("locked", "0")
            frame.set("layoutInCell", "1")
            frame.set("allowOverlap", "1")

        # Extent
        extent_data = data.get("extent", {})
        cx = str(extent_data.get("cx", 914400))
        cy = str(extent_data.get("cy", 914400))
        ET.SubElement(frame, qn("wp:extent"), {"cx": cx, "cy": cy})

        # Effect Extent
        ET.SubElement(frame, qn("wp:effectExtent"), {"l": "0", "t": "0", "r": "0", "b": "0"})

        # DocPr
        doc_pr_data = data.get("docProperties", {})
        d_id = str(doc_pr_data.get("id", "1"))
        d_name = str(doc_pr_data.get("name", "Picture 1"))
        d_attrib = {"id": d_id, "name": d_name}
        if "description" in doc_pr_data:
            d_attrib["descr"] = str(doc_pr_data["description"])
        ET.SubElement(frame, qn("wp:docPr"), d_attrib)

        # Non-visual graphic frame properties
        ET.SubElement(frame, qn("wp:cNvGraphicFramePr"))

        # Graphic child element
        if graphic_element is not None:
            frame.append(graphic_element)

        return drawing


__all__ = ["DrawingHandler"]
