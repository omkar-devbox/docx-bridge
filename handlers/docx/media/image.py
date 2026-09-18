"""Handler for picture and image elements (pic:pic, a:blip, pic:blipFill)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class ImageHandler(BaseHandler):
    """Handles parsing and reconstructing pic:pic image elements and blip fills."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert a pic:pic or a:blip element into a JSON image AST dictionary."""
        img_dict: dict[str, Any] = {"type": "image"}

        blip = element.find(f".//{qn('a:blip')}")
        if blip is not None:
            r_id = blip.attrib.get(qn("r:embed")) or blip.attrib.get(qn("r:link"))
            if r_id:
                img_dict["relationshipId"] = r_id

        # Non-visual properties (name, id, descr)
        c_nv_pr = element.find(f".//{qn('pic:cNvPr')}")
        if c_nv_pr is not None:
            img_dict["id"] = c_nv_pr.attrib.get("id", "")
            img_dict["name"] = c_nv_pr.attrib.get("name", "")
            descr = c_nv_pr.attrib.get("descr")
            if descr:
                img_dict["description"] = descr

        # SpPr Extents
        xfrm = element.find(f".//{qn('a:xfrm')}")
        if xfrm is not None:
            ext = xfrm.find(qn("a:ext"))
            if ext is not None:
                cx = ext.attrib.get("cx")
                cy = ext.attrib.get("cy")
                img_dict["extent"] = {
                    "cx": int(cx) if cx and cx.isdigit() else cx,
                    "cy": int(cy) if cy and cy.isdigit() else cy,
                }

        return img_dict

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Construct a pic:pic element from an image AST dictionary."""
        pic = ET.Element(qn("pic:pic"))

        # Non-visual picture properties
        nv_pic_pr = ET.SubElement(pic, qn("pic:nvPicPr"))
        c_nv_pr = ET.SubElement(
            nv_pic_pr,
            qn("pic:cNvPr"),
            {
                "id": str(data.get("id", "0")),
                "name": str(data.get("name", "Picture")),
            },
        )
        if "description" in data:
            c_nv_pr.set("descr", str(data["description"]))
        ET.SubElement(nv_pic_pr, qn("pic:cNvPicPr"))

        # Blip fill
        blip_fill = ET.SubElement(pic, qn("pic:blipFill"))
        rel_id = str(data.get("relationshipId", "rId1"))
        ET.SubElement(blip_fill, qn("a:blip"), {qn("r:embed"): rel_id})
        stretch = ET.SubElement(blip_fill, qn("a:stretch"))
        ET.SubElement(stretch, qn("a:fillRect"))

        # Shape properties
        sp_pr = ET.SubElement(pic, qn("pic:spPr"))
        xfrm = ET.SubElement(sp_pr, qn("a:xfrm"))
        ET.SubElement(xfrm, qn("a:off"), {"x": "0", "y": "0"})
        extent = data.get("extent", {})
        cx = str(extent.get("cx", 914400))
        cy = str(extent.get("cy", 914400))
        ET.SubElement(xfrm, qn("a:ext"), {"cx": cx, "cy": cy})

        prst_geom = ET.SubElement(sp_pr, qn("a:prstGeom"), {"prst": "rect"})
        ET.SubElement(prst_geom, qn("a:avLst"))

        return pic


__all__ = ["ImageHandler"]
