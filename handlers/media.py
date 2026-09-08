"""Handler for embedded media, drawings, and images in docx packages."""

import base64
from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name


class MediaHandler(BaseHandler):
    """Handles extraction and encoding of embedded media assets and w:drawing elements."""

    @staticmethod
    def encode_media_to_base64(raw_bytes: bytes) -> str:
        """Encode binary media content to a base64 string."""
        return base64.b64encode(raw_bytes).decode("ascii")

    @staticmethod
    def decode_media_from_base64(encoded_str: str) -> bytes:
        """Decode base64 string back to binary media bytes."""
        return base64.b64decode(encoded_str.encode("ascii"))

    @classmethod
    def media_map_to_json(cls, media_dict: dict[str, bytes]) -> dict[str, str]:
        """Convert a map of {filename: raw_bytes} to JSON-serializable base64 strings."""
        return {name: cls.encode_media_to_base64(data) for name, data in media_dict.items()}

    @classmethod
    def media_map_to_bytes(cls, data: dict[str, str]) -> dict[str, bytes]:
        """Convert a map of {filename: base64_str} back to raw bytes."""
        return {name: cls.decode_media_from_base64(b64) for name, b64 in data.items()}

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert w:drawing element to JSON dictionary."""
        result: dict[str, Any] = {
            "type": "drawing",
            "drawingType": "inline",
            "name": "",
            "relationshipId": "",
        }

        # Check inline vs anchor
        inline = element.find(qn("wp:inline"))
        anchor = element.find(qn("wp:anchor"))
        container = inline if inline is not None else anchor

        if anchor is not None:
            result["drawingType"] = "anchor"
            anchor_attrs: dict[str, Any] = {}
            for k, v in anchor.attrib.items():
                anchor_attrs[local_name(k)] = int(v) if v.isdigit() or (v.startswith("-") and v[1:].isdigit()) else v
            result["anchorProperties"] = anchor_attrs

            # SimplePos
            sp_el = anchor.find(qn("wp:simplePos"))
            if sp_el is not None:
                result["simplePos"] = {
                    "x": int(sp_el.attrib.get("x", "0")),
                    "y": int(sp_el.attrib.get("y", "0")),
                }

            # PositionH
            pos_h = anchor.find(qn("wp:positionH"))
            if pos_h is not None:
                h_dict: dict[str, Any] = {"relativeFrom": pos_h.attrib.get("relativeFrom", "column")}
                offset_el = pos_h.find(qn("wp:posOffset"))
                if offset_el is not None and offset_el.text:
                    val = offset_el.text.strip()
                    h_dict["posOffset"] = int(val) if val.isdigit() or (val.startswith("-") and val[1:].isdigit()) else val
                align_el = pos_h.find(qn("wp:align"))
                if align_el is not None and align_el.text:
                    h_dict["align"] = align_el.text.strip()
                result["positionH"] = h_dict

            # PositionV
            pos_v = anchor.find(qn("wp:positionV"))
            if pos_v is not None:
                v_dict: dict[str, Any] = {"relativeFrom": pos_v.attrib.get("relativeFrom", "paragraph")}
                offset_el = pos_v.find(qn("wp:posOffset"))
                if offset_el is not None and offset_el.text:
                    val = offset_el.text.strip()
                    v_dict["posOffset"] = int(val) if val.isdigit() or (val.startswith("-") and val[1:].isdigit()) else val
                align_el = pos_v.find(qn("wp:align"))
                if align_el is not None and align_el.text:
                    v_dict["align"] = align_el.text.strip()
                result["positionV"] = v_dict

            # Wrap type
            for wrap_tag in ("wrapNone", "wrapSquare", "wrapTight", "wrapThrough", "wrapTopAndBottom"):
                if anchor.find(qn(f"wp:{wrap_tag}")) is not None:
                    result["wrapType"] = wrap_tag
                    break
        elif inline is not None:
            inline_attrs: dict[str, Any] = {}
            for k, v in inline.attrib.items():
                inline_attrs[local_name(k)] = int(v) if v.isdigit() else v
            if inline_attrs:
                result["inlineProperties"] = inline_attrs

        if container is not None:
            # Extent (dimensions)
            extent = container.find(qn("wp:extent"))
            if extent is not None:
                cx = extent.attrib.get("cx", "")
                cy = extent.attrib.get("cy", "")
                result["extent"] = {
                    "cx": int(cx) if cx.isdigit() else cx,
                    "cy": int(cy) if cy.isdigit() else cy,
                }

            # Effect Extent
            effect_extent = container.find(qn("wp:effectExtent"))
            if effect_extent is not None:
                result["effectExtent"] = {
                    local_name(k): (int(v) if v.isdigit() or (v.startswith("-") and v[1:].isdigit()) else v)
                    for k, v in effect_extent.attrib.items()
                }

            # DocPr (ID, name, descr)
            doc_pr = container.find(qn("wp:docPr"))
            if doc_pr is not None:
                result["name"] = doc_pr.attrib.get("name", "")
                d_id = doc_pr.attrib.get("id")
                if d_id:
                    result["id"] = int(d_id) if d_id.isdigit() else d_id
                if doc_pr.attrib.get("descr"):
                    result["description"] = doc_pr.attrib.get("descr")

            # Blip (r:embed)
            for blip in container.iter(qn("a:blip")):
                r_embed = blip.attrib.get(qn("r:embed"))
                if r_embed:
                    result["relationshipId"] = r_embed
                    break

            # Preserve non-standard graphic inner XML (e.g. shapes / wsp)
            graphic = container.find(qn("a:graphic"))
            if graphic is not None:
                graphic_data = graphic.find(qn("a:graphicData"))
                if graphic_data is not None:
                    is_pic = graphic_data.find(qn("pic:pic")) is not None
                    if not is_pic:
                        result["graphicDataXml"] = ET.tostring(graphic_data, encoding="utf-8").decode("utf-8")

        return result

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert JSON drawing representation back to w:drawing XML element."""
        drawing = ET.Element(qn("w:drawing"))
        d_type = data.get("drawingType", "inline")
        container_tag = qn(f"wp:{d_type}")

        if d_type == "anchor":
            anchor_props = data.get("anchorProperties", {})
            container_attrs: dict[str, str] = {
                "distT": str(anchor_props.get("distT", "0")),
                "distB": str(anchor_props.get("distB", "0")),
                "distL": str(anchor_props.get("distL", "114300")),
                "distR": str(anchor_props.get("distR", "114300")),
                "simplePos": str(anchor_props.get("simplePos", "0")),
                "relativeHeight": str(anchor_props.get("relativeHeight", "251648000")),
                "behindDoc": str(anchor_props.get("behindDoc", "1")),
                "locked": str(anchor_props.get("locked", "0")),
                "layoutInCell": str(anchor_props.get("layoutInCell", "0")),
                "allowOverlap": str(anchor_props.get("allowOverlap", "1")),
            }
            container = ET.SubElement(drawing, container_tag, container_attrs)

            # simplePos
            sp_data = data.get("simplePos", {"x": 0, "y": 0})
            ET.SubElement(container, qn("wp:simplePos"), {
                "x": str(sp_data.get("x", 0)),
                "y": str(sp_data.get("y", 0)),
            })

            # positionH
            pos_h = data.get("positionH", {})
            h_el = ET.SubElement(container, qn("wp:positionH"), {
                "relativeFrom": str(pos_h.get("relativeFrom", "column"))
            })
            if "posOffset" in pos_h:
                offset_el = ET.SubElement(h_el, qn("wp:posOffset"))
                offset_el.text = str(pos_h["posOffset"])
            elif "align" in pos_h:
                align_el = ET.SubElement(h_el, qn("wp:align"))
                align_el.text = str(pos_h["align"])

            # positionV
            pos_v = data.get("positionV", {})
            v_el = ET.SubElement(container, qn("wp:positionV"), {
                "relativeFrom": str(pos_v.get("relativeFrom", "paragraph"))
            })
            if "posOffset" in pos_v:
                offset_el = ET.SubElement(v_el, qn("wp:posOffset"))
                offset_el.text = str(pos_v["posOffset"])
            elif "align" in pos_v:
                align_el = ET.SubElement(v_el, qn("wp:align"))
                align_el.text = str(pos_v["align"])
        else:
            inline_props = data.get("inlineProperties", {})
            container_attrs = {
                "distT": str(inline_props.get("distT", "0")),
                "distB": str(inline_props.get("distB", "0")),
                "distL": str(inline_props.get("distL", "0")),
                "distR": str(inline_props.get("distR", "0")),
            }
            container = ET.SubElement(drawing, container_tag, container_attrs)

        # Extent
        extent_data = data.get("extent", {})
        cx = str(extent_data.get("cx", 1905000))
        cy = str(extent_data.get("cy", 1905000))
        ET.SubElement(container, qn("wp:extent"), {"cx": cx, "cy": cy})

        # Effect Extent
        eff = data.get("effectExtent", {"l": 0, "t": 0, "r": 0, "b": 0})
        ET.SubElement(container, qn("wp:effectExtent"), {
            "l": str(eff.get("l", 0)),
            "t": str(eff.get("t", 0)),
            "r": str(eff.get("r", 0)),
            "b": str(eff.get("b", 0)),
        })

        # Wrap type (for anchor)
        if d_type == "anchor":
            wrap_type = data.get("wrapType", "wrapNone")
            ET.SubElement(container, qn(f"wp:{wrap_type}"))

        # DocPr
        doc_pr_attrs = {
            "id": str(data.get("id", 1)),
            "name": str(data.get("name", "Picture 1")),
        }
        if data.get("description"):
            doc_pr_attrs["descr"] = str(data["description"])
        ET.SubElement(container, qn("wp:docPr"), doc_pr_attrs)

        # cNvGraphicFramePr
        frame_pr = ET.SubElement(container, qn("wp:cNvGraphicFramePr"))
        ET.SubElement(frame_pr, qn("a:graphicFrameLocks"), {"noChangeAspect": "1"})

        # Graphic
        graphic = ET.SubElement(container, qn("a:graphic"))
        if data.get("graphicDataXml"):
            from utils.xml import parse_xml_string
            g_data_elem = parse_xml_string(data["graphicDataXml"])
            graphic.append(g_data_elem)
        else:
            graphic_data = ET.SubElement(
                graphic,
                qn("a:graphicData"),
                {"uri": self.get_namespace("pic")},
            )
            pic = ET.SubElement(graphic_data, qn("pic:pic"))
            # nvPicPr
            nv_pic_pr = ET.SubElement(pic, qn("pic:nvPicPr"))
            ET.SubElement(nv_pic_pr, qn("pic:cNvPr"), {
                "id": str(data.get("id", 0)),
                "name": str(data.get("name", "Picture 1")),
            })
            cNvPicPr = ET.SubElement(nv_pic_pr, qn("pic:cNvPicPr"))
            ET.SubElement(cNvPicPr, qn("a:picLocks"), {
                "noChangeAspect": "1",
                "noChangeArrowheads": "1",
            })
            # blipFill
            blip_fill = ET.SubElement(pic, qn("pic:blipFill"))
            rel_id = data.get("relationshipId", "")
            blip = ET.SubElement(blip_fill, qn("a:blip"), {qn("r:embed"): rel_id})
            ET.SubElement(blip, qn("a:extLst"))
            ET.SubElement(blip_fill, qn("a:srcRect"))
            stretch = ET.SubElement(blip_fill, qn("a:stretch"))
            ET.SubElement(stretch, qn("a:fillRect"))
            # spPr
            sp_pr = ET.SubElement(pic, qn("pic:spPr"), {"bwMode": "auto"})
            xfrm = ET.SubElement(sp_pr, qn("a:xfrm"))
            ET.SubElement(xfrm, qn("a:off"), {"x": "0", "y": "0"})
            ET.SubElement(xfrm, qn("a:ext"), {"cx": cx, "cy": cy})
            prst_geom = ET.SubElement(sp_pr, qn("a:prstGeom"), {"prst": "rect"})
            ET.SubElement(prst_geom, qn("a:avLst"))
            ET.SubElement(sp_pr, qn("a:noFill"))

        return drawing
