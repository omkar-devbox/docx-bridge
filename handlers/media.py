# --------------------------------
# Imports
# --------------------------------

import base64
from typing import Any
import xml.etree.ElementTree as ET

from handlers.base import BaseHandler, qn, local_name


# --------------------------------
# Media Handler
# --------------------------------

class MediaHandler(BaseHandler):

    # --------------------------------
    # Base64 Helpers
    # --------------------------------

    @staticmethod
    def encode_media_to_base64(
        raw_bytes: bytes,
    ) -> str:
        return base64.b64encode(
            raw_bytes
        ).decode("ascii")


    @staticmethod
    def decode_media_from_base64(
        encoded_str: str,
    ) -> bytes:
        return base64.b64decode(
            encoded_str.encode("ascii")
        )


    @classmethod
    def media_map_to_json(
        cls,
        media_dict: dict[str, bytes],
    ) -> dict[str, str]:

        return {
            name: cls.encode_media_to_base64(data)
            for name, data in media_dict.items()
        }


    @classmethod
    def media_map_to_bytes(
        cls,
        data: dict[str, str],
    ) -> dict[str, bytes]:

        return {
            name: cls.decode_media_from_base64(b64)
            for name, b64 in data.items()
        }


    # --------------------------------
    # VML Style Parsing
    # --------------------------------

    @staticmethod
    def parse_vml_style(
        style_str: str,
    ) -> dict[str, Any]:

        if not style_str or not isinstance(style_str, str):
            return {}

        result: dict[str, Any] = {}
        position: dict[str, Any] = {}
        size: dict[str, Any] = {}

        parts = [
            part.strip()
            for part in style_str.split(";")
            if part.strip()
        ]

        for part in parts:

            if ":" not in part:
                continue

            key, value = part.split(":", 1)

            key = key.strip().lower()
            value = value.strip()

            if key in ("margin-left", "left"):
                position["x"] = value

            elif key in ("margin-top", "top"):
                position["y"] = value

            elif key == "position":
                position["type"] = value

            elif key == "width":
                size["width"] = value

            elif key == "height":
                size["height"] = value

            elif key == "z-index":
                if (
                    value.isdigit()
                    or (
                        value.startswith("-")
                        and value[1:].isdigit()
                    )
                ):
                    result["zIndex"] = int(value)
                else:
                    result["zIndex"] = value

            elif key == "mso-wrap-style":
                result["wrap"] = value

            elif key == "mso-position-horizontal":
                result["horizontalPosition"] = value

            elif key == "mso-position-vertical":
                result["verticalPosition"] = value

            elif key == "v-text-anchor":
                result["verticalAnchor"] = value

            else:
                result[key] = value

        if position:
            result["position"] = position

        if size:
            result["size"] = size

        return result


    # --------------------------------
    # VML Style Building
    # --------------------------------

    @staticmethod
    def build_vml_style(
        style_obj: dict[str, Any] | str,
    ) -> str:

        if isinstance(style_obj, str):
            return style_obj

        if not isinstance(style_obj, dict):
            return ""

        parts: list[str] = []

        position = style_obj.get("position")

        if isinstance(position, dict):

            if "type" in position:
                parts.append(
                    f"position:{position['type']}"
                )

            if "x" in position:
                parts.append(
                    f"margin-left:{position['x']}"
                )

            if "y" in position:
                parts.append(
                    f"margin-top:{position['y']}"
                )

        size = style_obj.get("size")

        if isinstance(size, dict):

            if "width" in size:
                parts.append(
                    f"width:{size['width']}"
                )

            if "height" in size:
                parts.append(
                    f"height:{size['height']}"
                )

        if "zIndex" in style_obj:
            parts.append(
                f"z-index:{style_obj['zIndex']}"
            )

        if "wrap" in style_obj:
            parts.append(
                f"mso-wrap-style:{style_obj['wrap']}"
            )

        if "horizontalPosition" in style_obj:
            parts.append(
                f"mso-position-horizontal:"
                f"{style_obj['horizontalPosition']}"
            )

        if "verticalPosition" in style_obj:
            parts.append(
                f"mso-position-vertical:"
                f"{style_obj['verticalPosition']}"
            )

        if "verticalAnchor" in style_obj:
            parts.append(
                f"v-text-anchor:{style_obj['verticalAnchor']}"
            )

        reserved_keys = {
            "position",
            "size",
            "zIndex",
            "wrap",
            "horizontalPosition",
            "verticalPosition",
            "verticalAnchor",
        }

        for key, value in style_obj.items():

            if key not in reserved_keys:
                parts.append(
                    f"{key}:{value}"
                )

        return ";".join(parts)


    # --------------------------------
    # Path Helpers
    # --------------------------------

    @staticmethod
    def _parse_number(
        value: Any,
        default: int = 0,
    ) -> int | str:

        value_str = str(value)

        if (
            value_str.isdigit()
            or (
                value_str.startswith("-")
                and value_str[1:].isdigit()
            )
        ):
            return int(value_str)

        return value_str if value_str else default


    @staticmethod
    def _parse_path_element(
        path_elem: ET.Element,
    ) -> dict[str, Any]:

        width = path_elem.attrib.get(
            "w",
            "",
        )

        height = path_elem.attrib.get(
            "h",
            "",
        )

        commands: list[str] = []

        for command in path_elem:

            tag = local_name(
                command.tag
            )

            if tag == "moveTo":

                point = command.find(
                    qn("a:pt")
                )

                if point is not None:
                    commands.append(
                        f"M "
                        f"{point.attrib.get('x', '0')} "
                        f"{point.attrib.get('y', '0')}"
                    )

            elif tag == "lnTo":

                point = command.find(
                    qn("a:pt")
                )

                if point is not None:
                    commands.append(
                        f"L "
                        f"{point.attrib.get('x', '0')} "
                        f"{point.attrib.get('y', '0')}"
                    )

            elif tag == "cubicBezTo":

                points = [
                    f"{point.attrib.get('x', '0')} "
                    f"{point.attrib.get('y', '0')}"
                    for point in command.findall(
                        qn("a:pt")
                    )
                ]

                if points:
                    commands.append(
                        f"C {' '.join(points)}"
                    )

            elif tag == "quadBezTo":

                points = [
                    f"{point.attrib.get('x', '0')} "
                    f"{point.attrib.get('y', '0')}"
                    for point in command.findall(
                        qn("a:pt")
                    )
                ]

                if points:
                    commands.append(
                        f"Q {' '.join(points)}"
                    )

            elif tag == "close":
                commands.append("Z")

        result: dict[str, Any] = {
            "d": " ".join(commands),
        }

        if width:
            result["width"] = MediaHandler._parse_number(
                width
            )

        if height:
            result["height"] = MediaHandler._parse_number(
                height
            )

        return result


    # --------------------------------
    # Color Helpers
    # --------------------------------

    @staticmethod
    def _parse_color_element(
        color_element: ET.Element,
    ) -> str | dict[str, Any] | None:

        srgb = color_element.find(
            qn("a:srgbClr")
        )

        if srgb is not None:
            return srgb.attrib.get(
                "val",
                "",
            )

        scheme = color_element.find(
            qn("a:schemeClr")
        )

        if scheme is not None:

            result: dict[str, Any] = {
                "schemeColor": scheme.attrib.get(
                    "val",
                    "",
                )
            }

            for modifier in (
                "lumMod",
                "lumOff",
                "shade",
                "tint",
            ):
                element = scheme.find(
                    qn(f"a:{modifier}")
                )

                if element is not None:
                    value = element.attrib.get(
                        "val",
                        "",
                    )

                    result[modifier] = (
                        int(value)
                        if value.isdigit()
                        else value
                    )

            return result

        preset = color_element.find(
            qn("a:prstClr")
        )

        if preset is not None:
            return preset.attrib.get(
                "val",
                "",
            )

        return None


    # --------------------------------
    # Shape Parsing
    # --------------------------------

    def _parse_shape(
        self,
        wsp: ET.Element,
    ) -> dict[str, Any]:

        shape: dict[str, Any] = {
            "type": "shape",
        }

        # Shape metadata.
        c_nv_pr = wsp.find(
            qn("wps:cNvPr")
        )

        if c_nv_pr is not None:

            shape_id = c_nv_pr.attrib.get("id")

            if shape_id:
                shape["id"] = self._parse_number(
                    shape_id
                )

            name = c_nv_pr.attrib.get("name")

            if name:
                shape["name"] = name

        # Shape properties.
        sp_pr = wsp.find(
            qn("wps:spPr")
        )

        if sp_pr is not None:
            self._parse_shape_transform(
                sp_pr,
                shape,
            )

            self._parse_shape_fill(
                sp_pr,
                shape,
            )

            self._parse_shape_stroke(
                sp_pr,
                shape,
            )

            self._parse_shape_geometry(
                sp_pr,
                shape,
            )

        self._parse_shape_style(
            wsp,
            shape,
        )

        self._parse_shape_body_properties(
            wsp,
            shape,
        )

        return shape


    # --------------------------------
    # Shape Transform Parsing
    # --------------------------------

    def _parse_shape_transform(
        self,
        sp_pr: ET.Element,
        shape: dict[str, Any],
    ) -> None:

        xfrm = sp_pr.find(
            qn("a:xfrm")
        )

        if xfrm is None:
            return

        offset = xfrm.find(
            qn("a:off")
        )

        if offset is not None:
            shape["offset"] = {
                "x": self._parse_number(
                    offset.attrib.get("x", 0)
                ),
                "y": self._parse_number(
                    offset.attrib.get("y", 0)
                ),
            }

        extent = xfrm.find(
            qn("a:ext")
        )

        if extent is not None:
            shape["extent"] = {
                "cx": self._parse_number(
                    extent.attrib.get("cx", 0)
                ),
                "cy": self._parse_number(
                    extent.attrib.get("cy", 0)
                ),
            }


    # --------------------------------
    # Shape Fill Parsing
    # --------------------------------

    def _parse_shape_fill(
        self,
        sp_pr: ET.Element,
        shape: dict[str, Any],
    ) -> None:

        solid_fill = sp_pr.find(
            qn("a:solidFill")
        )

        if solid_fill is not None:

            color = self._parse_color_element(
                solid_fill
            )

            if color is not None:
                shape["fill"] = color

        elif sp_pr.find(
            qn("a:noFill")
        ) is not None:

            shape["fill"] = "none"


    # --------------------------------
    # Shape Stroke Parsing
    # --------------------------------

    def _parse_shape_stroke(
        self,
        sp_pr: ET.Element,
        shape: dict[str, Any],
    ) -> None:

        line = sp_pr.find(
            qn("a:ln")
        )

        if line is None:
            return

        if line.find(
            qn("a:noFill")
        ) is not None:

            shape["stroke"] = "none"
            return

        line_data: dict[str, Any] = {}

        width = line.attrib.get("w")

        if width:
            line_data["width"] = self._parse_number(
                width
            )

        solid_fill = line.find(
            qn("a:solidFill")
        )

        if solid_fill is not None:

            color = self._parse_color_element(
                solid_fill
            )

            if color is not None:
                line_data["color"] = color

        shape["stroke"] = (
            line_data
            if line_data
            else "solid"
        )


    # --------------------------------
    # Shape Geometry Parsing
    # --------------------------------

    def _parse_shape_geometry(
        self,
        sp_pr: ET.Element,
        shape: dict[str, Any],
    ) -> None:

        custom_geometry = sp_pr.find(
            qn("a:custGeom")
        )

        if custom_geometry is not None:

            path_list = custom_geometry.find(
                qn("a:pathLst")
            )

            if path_list is not None:

                shape["paths"] = [
                    self._parse_path_element(path)
                    for path in path_list.findall(
                        qn("a:path")
                    )
                ]

            return

        preset_geometry = sp_pr.find(
            qn("a:prstGeom")
        )

        if preset_geometry is not None:
            shape["geometry"] = (
                preset_geometry.attrib.get(
                    "prst",
                    "rect",
                )
            )


    # --------------------------------
    # Shape Style Parsing
    # --------------------------------

    def _parse_shape_style(
        self,
        wsp: ET.Element,
        shape: dict[str, Any],
    ) -> None:

        style_element = wsp.find(
            qn("wps:style")
        )

        if style_element is None:
            return

        style_data: dict[str, Any] = {}

        references = (
            ("lnRef", "lineReference"),
            ("fillRef", "fillReference"),
            ("effectRef", "effectReference"),
            ("fontRef", "fontReference"),
        )

        for reference_tag, key_name in references:

            reference = style_element.find(
                qn(f"a:{reference_tag}")
            )

            if reference is None:
                continue

            index = reference.attrib.get(
                "idx",
                "",
            )

            reference_data: dict[str, Any] = {
                "index": self._parse_number(
                    index
                )
            }

            color = self._parse_color_element(
                reference
            )

            if isinstance(color, dict):
                reference_data.update(color)

            elif isinstance(color, str):
                reference_data["color"] = color

            style_data[key_name] = reference_data

        if style_data:
            shape["style"] = style_data


    # --------------------------------
    # Shape Body Properties Parsing
    # --------------------------------

    def _parse_shape_body_properties(
        self,
        wsp: ET.Element,
        shape: dict[str, Any],
    ) -> None:

        body_properties = wsp.find(
            qn("wps:bodyPr")
        )

        if body_properties is None:
            return

        result: dict[str, Any] = {
            local_name(key): value
            for key, value
            in body_properties.attrib.items()
        }

        text_warp = body_properties.find(
            qn("a:prstTxWarp")
        )

        if text_warp is not None:
            result["presetTextWarp"] = (
                text_warp.attrib.get(
                    "prst",
                    "textNoShape",
                )
            )

        if result:
            shape["bodyProperties"] = result


    # --------------------------------
    # Drawing JSON Parsing
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
    ) -> dict[str, Any]:

        result: dict[str, Any] = {
            "type": self.tag_to_name(
                "w:drawing",
                "drawing",
            ),
        }

        inline = element.find(
            qn("wp:inline")
        )

        anchor = element.find(
            qn("wp:anchor")
        )

        container = (
            inline
            if inline is not None
            else anchor
        )

        if anchor is not None:
            self._parse_anchor(
                anchor,
                result,
            )

        elif inline is not None:
            self._parse_inline(
                inline,
                result,
            )

        if container is not None:
            self._parse_container_data(
                container,
                result,
            )

        return result


    # --------------------------------
    # Anchor Parsing
    # --------------------------------

    def _parse_anchor(
        self,
        anchor: ET.Element,
        result: dict[str, Any],
    ) -> None:

        result["container"] = "anchor"
        result["drawingType"] = "anchor"

        numeric_attributes = (
            "distT",
            "distB",
            "distL",
            "distR",
            "relativeHeight",
        )

        boolean_attributes = (
            "behindDoc",
            "locked",
            "layoutInCell",
            "allowOverlap",
            "simplePos",
        )

        for attribute in numeric_attributes:

            if attribute not in anchor.attrib:
                continue

            value = anchor.attrib[attribute]

            result[attribute] = self._parse_number(
                value
            )

        for attribute in boolean_attributes:

            if attribute not in anchor.attrib:
                continue

            value = anchor.attrib[attribute]

            result[attribute] = (
                value == "1"
                or value == "true"
            )

        self._parse_position(
            anchor,
            result,
            "positionH",
            "column",
        )

        self._parse_position(
            anchor,
            result,
            "positionV",
            "paragraph",
        )

        for wrap_tag in (
            "wrapNone",
            "wrapSquare",
            "wrapTight",
            "wrapThrough",
            "wrapTopAndBottom",
        ):

            if anchor.find(
                qn(f"wp:{wrap_tag}")
            ) is not None:

                result["wrap"] = (
                    wrap_tag
                    .replace(
                        "wrap",
                        "",
                    )
                    .lower()
                )

                break


    # --------------------------------
    # Inline Parsing
    # --------------------------------

    def _parse_inline(
        self,
        inline: ET.Element,
        result: dict[str, Any],
    ) -> None:

        result["container"] = "inline"
        result["drawingType"] = "inline"

        for attribute in (
            "distT",
            "distB",
            "distL",
            "distR",
        ):

            if attribute not in inline.attrib:
                continue

            result[attribute] = self._parse_number(
                inline.attrib[attribute]
            )


    # --------------------------------
    # Position Parsing
    # --------------------------------

    def _parse_position(
        self,
        container: ET.Element,
        result: dict[str, Any],
        tag_name: str,
        default_relative: str,
    ) -> None:

        position = container.find(
            qn(f"wp:{tag_name}")
        )

        if position is None:
            return

        position_data: dict[str, Any] = {
            "relativeFrom": position.attrib.get(
                "relativeFrom",
                default_relative,
            )
        }

        offset = position.find(
            qn("wp:posOffset")
        )

        if offset is not None and offset.text:

            value = offset.text.strip()

            position_data["offset"] = (
                self._parse_number(value)
            )

        align = position.find(
            qn("wp:align")
        )

        if align is not None and align.text:
            position_data["align"] = (
                align.text.strip()
            )

        result[tag_name] = position_data


    # --------------------------------
    # Container Data Parsing
    # --------------------------------

    def _parse_container_data(
        self,
        container: ET.Element,
        result: dict[str, Any],
    ) -> None:

        extent = container.find(
            qn("wp:extent")
        )

        if extent is not None:

            cx = self._parse_number(
                extent.attrib.get(
                    "cx",
                    "",
                )
            )

            cy = self._parse_number(
                extent.attrib.get(
                    "cy",
                    "",
                )
            )

            result["extent"] = {
                "cx": cx,
                "cy": cy,
                "width": cx,
                "height": cy,
            }

        doc_pr = container.find(
            qn("wp:docPr")
        )

        if doc_pr is not None:

            name = doc_pr.attrib.get("name")

            if name:
                result["name"] = name

            drawing_id = doc_pr.attrib.get("id")

            if drawing_id:
                result["id"] = self._parse_number(
                    drawing_id
                )

        self._parse_picture_relationship(
            container,
            result,
        )

        self._parse_shape_group(
            container,
            result,
        )

        self._parse_diagram(
            container,
            result,
        )

        if (
            "shapes" not in result
            and "relationshipId" not in result
            and "diagram" not in result
        ):
            self._parse_single_shape(
                container,
                result,
            )


    # --------------------------------
    # Picture Relationship Parsing
    # --------------------------------

    @staticmethod
    def _parse_picture_relationship(
        container: ET.Element,
        result: dict[str, Any],
    ) -> None:

        for blip in container.iter(
            qn("a:blip")
        ):

            relationship_id = blip.attrib.get(
                qn("r:embed")
            )

            if relationship_id:
                result["relationshipId"] = (
                    relationship_id
                )

                break


    # --------------------------------
    # Shape Group Parsing
    # --------------------------------

    def _parse_shape_group(
        self,
        container: ET.Element,
        result: dict[str, Any],
    ) -> None:

        for group in container.iter(
            qn("wpg:wgp")
        ):

            group_properties = group.find(
                qn("wpg:grpSpPr")
            )

            if group_properties is not None:

                self._parse_group_transform(
                    group_properties,
                    result,
                )

            shapes = [
                self._parse_shape(shape)
                for shape in group.findall(
                    qn("wps:wsp")
                )
            ]

            if shapes:
                result["shapes"] = shapes
                result["drawingType"] = (
                    "shapeGroup"
                )


    # --------------------------------
    # Group Transform Parsing
    # --------------------------------

    def _parse_group_transform(
        self,
        group_properties: ET.Element,
        result: dict[str, Any],
    ) -> None:

        transform = group_properties.find(
            qn("a:xfrm")
        )

        if transform is None:
            return

        group_transform: dict[str, Any] = {}

        offset = transform.find(
            qn("a:off")
        )

        if offset is not None:
            group_transform["offset"] = {
                "x": self._parse_number(
                    offset.attrib.get(
                        "x",
                        0,
                    )
                ),
                "y": self._parse_number(
                    offset.attrib.get(
                        "y",
                        0,
                    )
                ),
            }

        extent = transform.find(
            qn("a:ext")
        )

        if extent is not None:
            group_transform["extent"] = {
                "cx": self._parse_number(
                    extent.attrib.get(
                        "cx",
                        0,
                    )
                ),
                "cy": self._parse_number(
                    extent.attrib.get(
                        "cy",
                        0,
                    )
                ),
            }

        child_offset = transform.find(
            qn("a:chOff")
        )

        if child_offset is not None:
            group_transform["childOffset"] = {
                "x": self._parse_number(
                    child_offset.attrib.get(
                        "x",
                        0,
                    )
                ),
                "y": self._parse_number(
                    child_offset.attrib.get(
                        "y",
                        0,
                    )
                ),
            }

        child_extent = transform.find(
            qn("a:chExt")
        )

        if child_extent is not None:
            group_transform["childExtent"] = {
                "cx": self._parse_number(
                    child_extent.attrib.get(
                        "cx",
                        0,
                    )
                ),
                "cy": self._parse_number(
                    child_extent.attrib.get(
                        "cy",
                        0,
                    )
                ),
            }

        if group_transform:
            result["groupTransform"] = (
                group_transform
            )


    # --------------------------------
    # Diagram Parsing
    # --------------------------------

    @staticmethod
    def _parse_diagram(
        container: ET.Element,
        result: dict[str, Any],
    ) -> None:

        for rel_ids in container.iter(
            qn("dgm:relIds")
        ):

            result["drawingType"] = "diagram"

            result["diagram"] = {
                local_name(key): value
                for key, value
                in rel_ids.attrib.items()
            }

            break


    # --------------------------------
    # Single Shape Parsing
    # --------------------------------

    def _parse_single_shape(
        self,
        container: ET.Element,
        result: dict[str, Any],
    ) -> None:

        for shape in container.iter(
            qn("wps:wsp")
        ):

            shape_data = self._parse_shape(
                shape
            )

            result.update(
                shape_data
            )

            result["drawingType"] = "shape"

            break


    # --------------------------------
    # Shape XML Building
    # --------------------------------

    def _build_shape_element(
        self,
        shape_data: dict[str, Any],
    ) -> ET.Element:

        wsp = ET.Element(
            qn("wps:wsp")
        )

        shape_id = str(
            shape_data.get(
                "id",
                1,
            )
        )

        shape_name = str(
            shape_data.get(
                "name",
                f"Shape {shape_id}",
            )
        )

        ET.SubElement(
            wsp,
            qn("wps:cNvPr"),
            {
                "id": shape_id,
                "name": shape_name,
            },
        )

        ET.SubElement(
            wsp,
            qn("wps:cNvSpPr"),
        )

        sp_pr = ET.SubElement(
            wsp,
            qn("wps:spPr"),
        )

        offset = shape_data.get(
            "offset",
            {
                "x": 0,
                "y": 0,
            },
        )

        extent = shape_data.get(
            "extent",
            shape_data.get(
                "dimensions",
                {
                    "cx": 100000,
                    "cy": 100000,
                },
            ),
        )

        xfrm = ET.SubElement(
            sp_pr,
            qn("a:xfrm"),
        )

        ET.SubElement(
            xfrm,
            qn("a:off"),
            {
                "x": str(
                    offset.get(
                        "x",
                        0,
                    )
                ),
                "y": str(
                    offset.get(
                        "y",
                        0,
                    )
                ),
            },
        )

        ET.SubElement(
            xfrm,
            qn("a:ext"),
            {
                "cx": str(
                    extent.get(
                        "cx",
                        extent.get(
                            "width",
                            100000,
                        ),
                    )
                ),
                "cy": str(
                    extent.get(
                        "cy",
                        extent.get(
                            "height",
                            100000,
                        ),
                    )
                ),
            },
        )

        self._build_shape_geometry(
            sp_pr,
            shape_data,
            extent,
        )

        self._build_shape_fill(
            sp_pr,
            shape_data,
        )

        self._build_shape_stroke(
            sp_pr,
            shape_data,
        )

        self._build_shape_style(
            wsp,
            shape_data,
        )

        self._build_shape_body_properties(
            wsp,
            shape_data,
        )

        return wsp


    # --------------------------------
    # Shape Geometry Building
    # --------------------------------

    def _build_shape_geometry(
        self,
        sp_pr: ET.Element,
        shape_data: dict[str, Any],
        extent: dict[str, Any],
    ) -> None:

        paths = shape_data.get("paths")

        if paths:

            custom_geometry = ET.SubElement(
                sp_pr,
                qn("a:custGeom"),
            )

            ET.SubElement(
                custom_geometry,
                qn("a:avLst"),
            )

            ET.SubElement(
                custom_geometry,
                qn("a:gdLst"),
            )

            ET.SubElement(
                custom_geometry,
                qn("a:ahLst"),
            )

            ET.SubElement(
                custom_geometry,
                qn("a:cxnLst"),
            )

            ET.SubElement(
                custom_geometry,
                qn("a:rect"),
                {
                    "l": "0",
                    "t": "0",
                    "r": "0",
                    "b": "0",
                },
            )

            path_list = ET.SubElement(
                custom_geometry,
                qn("a:pathLst"),
            )

            for path_data in paths:
                self._build_path_element(
                    path_list,
                    path_data,
                    extent,
                )

            return

        geometry_name = shape_data.get(
            "geometry",
            "rect",
        )

        preset_geometry = ET.SubElement(
            sp_pr,
            qn("a:prstGeom"),
            {
                "prst": str(
                    geometry_name
                )
            },
        )

        ET.SubElement(
            preset_geometry,
            qn("a:avLst"),
        )


    # --------------------------------
    # Path XML Building
    # --------------------------------

    def _build_path_element(
        self,
        path_list: ET.Element,
        path_data: dict[str, Any],
        extent: dict[str, Any],
    ) -> None:

        width = str(
            path_data.get(
                "width",
                extent.get(
                    "cx",
                    100000,
                ),
            )
        )

        height = str(
            path_data.get(
                "height",
                extent.get(
                    "cy",
                    100000,
                ),
            )
        )

        path_element = ET.SubElement(
            path_list,
            qn("a:path"),
            {
                "w": width,
                "h": height,
            },
        )

        path_string = path_data.get(
            "d",
            "",
        )

        tokens = path_string.split()
        index = 0

        while index < len(tokens):

            command = tokens[index]

            if (
                command == "M"
                and index + 2 < len(tokens)
            ):

                move_to = ET.SubElement(
                    path_element,
                    qn("a:moveTo"),
                )

                ET.SubElement(
                    move_to,
                    qn("a:pt"),
                    {
                        "x": tokens[index + 1],
                        "y": tokens[index + 2],
                    },
                )

                index += 3

            elif (
                command == "L"
                and index + 2 < len(tokens)
            ):

                line_to = ET.SubElement(
                    path_element,
                    qn("a:lnTo"),
                )

                ET.SubElement(
                    line_to,
                    qn("a:pt"),
                    {
                        "x": tokens[index + 1],
                        "y": tokens[index + 2],
                    },
                )

                index += 3

            elif (
                command == "C"
                and index + 6 < len(tokens)
            ):

                cubic = ET.SubElement(
                    path_element,
                    qn("a:cubicBezTo"),
                )

                for offset in (
                    1,
                    3,
                    5,
                ):

                    ET.SubElement(
                        cubic,
                        qn("a:pt"),
                        {
                            "x": tokens[
                                index + offset
                            ],
                            "y": tokens[
                                index + offset + 1
                            ],
                        },
                    )

                index += 7

            elif (
                command == "Q"
                and index + 4 < len(tokens)
            ):

                quadratic = ET.SubElement(
                    path_element,
                    qn("a:quadBezTo"),
                )

                for offset in (
                    1,
                    3,
                ):

                    ET.SubElement(
                        quadratic,
                        qn("a:pt"),
                        {
                            "x": tokens[
                                index + offset
                            ],
                            "y": tokens[
                                index + offset + 1
                            ],
                        },
                    )

                index += 5

            elif command == "Z":

                ET.SubElement(
                    path_element,
                    qn("a:close"),
                )

                index += 1

            else:
                index += 1


    # --------------------------------
    # Shape Fill Building
    # --------------------------------

    def _build_shape_fill(
        self,
        sp_pr: ET.Element,
        shape_data: dict[str, Any],
    ) -> None:

        fill = shape_data.get("fill")

        if fill == "none":

            ET.SubElement(
                sp_pr,
                qn("a:noFill"),
            )

            return

        if (
            isinstance(fill, dict)
            and "schemeColor" in fill
        ):

            solid_fill = ET.SubElement(
                sp_pr,
                qn("a:solidFill"),
            )

            scheme = ET.SubElement(
                solid_fill,
                qn("a:schemeClr"),
                {
                    "val": str(
                        fill["schemeColor"]
                    )
                },
            )

            self._append_color_modifiers(
                scheme,
                fill,
            )

            return

        if fill:

            solid_fill = ET.SubElement(
                sp_pr,
                qn("a:solidFill"),
            )

            ET.SubElement(
                solid_fill,
                qn("a:srgbClr"),
                {
                    "val": str(fill).replace(
                        "#",
                        "",
                    )
                },
            )


    # --------------------------------
    # Shape Stroke Building
    # --------------------------------

    def _build_shape_stroke(
        self,
        sp_pr: ET.Element,
        shape_data: dict[str, Any],
    ) -> None:

        stroke = shape_data.get(
            "stroke"
        )

        if stroke == "none":

            line = ET.SubElement(
                sp_pr,
                qn("a:ln"),
                {
                    "w": "0",
                },
            )

            ET.SubElement(
                line,
                qn("a:noFill"),
            )

            return

        if isinstance(stroke, dict):

            line_width = str(
                stroke.get(
                    "width",
                    "12700",
                )
            )

            line = ET.SubElement(
                sp_pr,
                qn("a:ln"),
                {
                    "w": line_width,
                },
            )

            color = stroke.get(
                "color"
            )

            self._append_line_color(
                line,
                color,
            )

            return

        if stroke and stroke != "solid":

            line = ET.SubElement(
                sp_pr,
                qn("a:ln"),
                {
                    "w": "12700",
                },
            )

            solid_fill = ET.SubElement(
                line,
                qn("a:solidFill"),
            )

            ET.SubElement(
                solid_fill,
                qn("a:srgbClr"),
                {
                    "val": str(stroke).replace(
                        "#",
                        "",
                    )
                },
            )


    # --------------------------------
    # Color Modifier Building
    # --------------------------------

    @staticmethod
    def _append_color_modifiers(
        color_element: ET.Element,
        color_data: dict[str, Any],
    ) -> None:

        for modifier in (
            "lumMod",
            "lumOff",
            "shade",
            "tint",
        ):

            if modifier in color_data:

                ET.SubElement(
                    color_element,
                    qn(f"a:{modifier}"),
                    {
                        "val": str(
                            color_data[modifier]
                        )
                    },
                )


    # --------------------------------
    # Line Color Building
    # --------------------------------

    def _append_line_color(
        self,
        line: ET.Element,
        color: Any,
    ) -> None:

        if not color:
            return

        solid_fill = ET.SubElement(
            line,
            qn("a:solidFill"),
        )

        if (
            isinstance(color, dict)
            and "schemeColor" in color
        ):

            scheme = ET.SubElement(
                solid_fill,
                qn("a:schemeClr"),
                {
                    "val": str(
                        color["schemeColor"]
                    )
                },
            )

            self._append_color_modifiers(
                scheme,
                color,
            )

        elif color != "solid":

            ET.SubElement(
                solid_fill,
                qn("a:srgbClr"),
                {
                    "val": str(color).replace(
                        "#",
                        "",
                    )
                },
            )


    # --------------------------------
    # Shape Style Building
    # --------------------------------

    def _build_shape_style(
        self,
        wsp: ET.Element,
        shape_data: dict[str, Any],
    ) -> None:

        style_data = shape_data.get(
            "style"
        )

        if not isinstance(
            style_data,
            dict,
        ):
            return

        style_element = ET.SubElement(
            wsp,
            qn("wps:style"),
        )

        references = (
            ("lineReference", "lnRef"),
            ("fillReference", "fillRef"),
            ("effectReference", "effectRef"),
            ("fontReference", "fontRef"),
        )

        for key_name, tag_name in references:

            reference = style_data.get(
                key_name
            )

            if not isinstance(
                reference,
                dict,
            ):
                continue

            index = str(
                reference.get(
                    "index",
                    reference.get(
                        "idx",
                        0,
                    ),
                )
            )

            reference_element = ET.SubElement(
                style_element,
                qn(f"a:{tag_name}"),
                {
                    "idx": index,
                },
            )

            if "schemeColor" in reference:

                scheme = ET.SubElement(
                    reference_element,
                    qn("a:schemeClr"),
                    {
                        "val": str(
                            reference[
                                "schemeColor"
                            ]
                        )
                    },
                )

                self._append_color_modifiers(
                    scheme,
                    reference,
                )

            elif "color" in reference:

                ET.SubElement(
                    reference_element,
                    qn("a:srgbClr"),
                    {
                        "val": str(
                            reference["color"]
                        ).replace(
                            "#",
                            "",
                        )
                    },
                )


    # --------------------------------
    # Shape Body Properties Building
    # --------------------------------

    def _build_shape_body_properties(
        self,
        wsp: ET.Element,
        shape_data: dict[str, Any],
    ) -> None:

        body_data = shape_data.get(
            "bodyProperties",
            shape_data.get(
                "bodyPr",
                {},
            ),
        )

        if not isinstance(
            body_data,
            dict,
        ):
            body_data = {}

        attributes = {
            key: str(value)
            for key, value in body_data.items()
            if key != "presetTextWarp"
        }

        body_properties = ET.SubElement(
            wsp,
            qn("wps:bodyPr"),
            attributes,
        )

        if "presetTextWarp" in body_data:

            text_warp = ET.SubElement(
                body_properties,
                qn("a:prstTxWarp"),
                {
                    "prst": str(
                        body_data[
                            "presetTextWarp"
                        ]
                    )
                },
            )

            ET.SubElement(
                text_warp,
                qn("a:avLst"),
            )


    # --------------------------------
    # Drawing XML Building
    # --------------------------------

    def to_xml(
        self,
        data: dict[str, Any],
    ) -> ET.Element:

        drawing = ET.Element(
            qn("w:drawing")
        )

        is_anchor = (
            "positionH" in data
            or "positionV" in data
            or data.get("container") == "anchor"
            or data.get("placement") == "anchor"
            or data.get("drawingType") == "anchor"
        )

        container_tag = qn(
            "wp:anchor"
            if is_anchor
            else "wp:inline"
        )

        extent = data.get(
            "extent",
            {},
        )

        if not isinstance(
            extent,
            dict,
        ):
            extent = {}

        cx = str(
            extent.get(
                "cx",
                extent.get(
                    "width",
                    1905000,
                ),
            )
        )

        cy = str(
            extent.get(
                "cy",
                extent.get(
                    "height",
                    1905000,
                ),
            )
        )

        if is_anchor:
            container = self._build_anchor_container(
                drawing,
                container_tag,
                data,
                cx,
                cy,
            )
        else:
            container = self._build_inline_container(
                drawing,
                container_tag,
                data,
                cx,
                cy,
            )

        self._build_doc_properties(
            container,
            data,
        )

        self._build_graphic(
            container,
            data,
            cx,
            cy,
        )

        return drawing


    # --------------------------------
    # Distance Helper
    # --------------------------------

    @staticmethod
    def _get_distance(
        data: dict[str, Any],
        key: str,
    ) -> str:

        value = data.get(
            key,
            0,
        )

        if isinstance(
            value,
            (int, float),
        ):
            return str(
                int(value)
            )

        if isinstance(
            value,
            str,
        ):

            if (
                value.isdigit()
                or (
                    value.startswith("-")
                    and value[1:].isdigit()
                )
            ):
                return value

        return "0"


    # --------------------------------
    # Anchor Container Building
    # --------------------------------

    def _build_anchor_container(
        self,
        drawing: ET.Element,
        container_tag: str,
        data: dict[str, Any],
        cx: str,
        cy: str,
    ) -> ET.Element:

        container_attributes = {
            "distT": self._get_distance(
                data,
                "distT",
            ),
            "distB": self._get_distance(
                data,
                "distB",
            ),
            "distL": self._get_distance(
                data,
                "distL",
            ),
            "distR": self._get_distance(
                data,
                "distR",
            ),
            "simplePos": "0",
            "relativeHeight": str(
                data.get(
                    "relativeHeight",
                    2,
                )
            ),
            "behindDoc": (
                "1"
                if data.get(
                    "behindDoc"
                ) in (
                    True,
                    "1",
                    1,
                )
                else "0"
            ),
            "locked": (
                "1"
                if data.get(
                    "locked"
                ) in (
                    True,
                    "1",
                    1,
                )
                else "0"
            ),
            "layoutInCell": (
                "1"
                if data.get(
                    "layoutInCell"
                ) in (
                    True,
                    "1",
                    1,
                )
                else "0"
            ),
            "allowOverlap": (
                "0"
                if data.get(
                    "allowOverlap"
                ) in (
                    False,
                    "0",
                    0,
                )
                else "1"
            ),
        }

        container = ET.SubElement(
            drawing,
            container_tag,
            container_attributes,
        )

        ET.SubElement(
            container,
            qn("wp:simplePos"),
            {
                "x": "0",
                "y": "0",
            },
        )

        self._build_anchor_position(
            container,
            data,
            "positionH",
            "column",
        )

        self._build_anchor_position(
            container,
            data,
            "positionV",
            "paragraph",
        )

        self._append_container_extent(
            container,
            cx,
            cy,
        )

        wrap = str(
            data.get(
                "wrap",
                data.get(
                    "wrapType",
                    "none",
                ),
            )
        ).lower()

        wrap_map = {
            "none": "wrapNone",
            "square": "wrapSquare",
            "tight": "wrapTight",
            "through": "wrapThrough",
            "topandbottom": "wrapTopAndBottom",
        }

        ET.SubElement(
            container,
            qn(
                f"wp:{wrap_map.get(
                    wrap,
                    'wrapNone',
                )}"
            ),
        )

        return container


    # --------------------------------
    # Anchor Position Building
    # --------------------------------

    def _build_anchor_position(
        self,
        container: ET.Element,
        data: dict[str, Any],
        key: str,
        default_relative: str,
    ) -> None:

        position_data = data.get(
            key,
            {},
        )

        if not isinstance(
            position_data,
            dict,
        ):
            position_data = {}

        position = ET.SubElement(
            container,
            qn(f"wp:{key}"),
            {
                "relativeFrom": str(
                    position_data.get(
                        "relativeFrom",
                        default_relative,
                    )
                )
            },
        )

        if "align" in position_data:

            align = ET.SubElement(
                position,
                qn("wp:align"),
            )

            align.text = str(
                position_data["align"]
            )

        else:

            offset = position_data.get(
                "offset",
                position_data.get(
                    "posOffset",
                    0,
                ),
            )

            offset_element = ET.SubElement(
                position,
                qn("wp:posOffset"),
            )

            offset_element.text = str(
                offset
            )


    # --------------------------------
    # Inline Container Building
    # --------------------------------

    def _build_inline_container(
        self,
        drawing: ET.Element,
        container_tag: str,
        data: dict[str, Any],
        cx: str,
        cy: str,
    ) -> ET.Element:

        container = ET.SubElement(
            drawing,
            container_tag,
            {
                "distT": self._get_distance(
                    data,
                    "distT",
                ),
                "distB": self._get_distance(
                    data,
                    "distB",
                ),
                "distL": self._get_distance(
                    data,
                    "distL",
                ),
                "distR": self._get_distance(
                    data,
                    "distR",
                ),
            },
        )

        self._append_container_extent(
            container,
            cx,
            cy,
        )

        return container


    # --------------------------------
    # Container Extent
    # --------------------------------

    @staticmethod
    def _append_container_extent(
        container: ET.Element,
        cx: str,
        cy: str,
    ) -> None:

        ET.SubElement(
            container,
            qn("wp:extent"),
            {
                "cx": cx,
                "cy": cy,
            },
        )

        ET.SubElement(
            container,
            qn("wp:effectExtent"),
            {
                "l": "0",
                "t": "0",
                "r": "0",
                "b": "0",
            },
        )


    # --------------------------------
    # Drawing Properties
    # --------------------------------

    @staticmethod
    def _build_doc_properties(
        container: ET.Element,
        data: dict[str, Any],
    ) -> None:

        doc_properties = ET.SubElement(
            container,
            qn("wp:docPr"),
            {
                "id": str(
                    data.get(
                        "id",
                        1,
                    )
                ),
                "name": str(
                    data.get(
                        "name",
                        "Drawing 1",
                    )
                ),
            },
        )

        frame_properties = ET.SubElement(
            container,
            qn("wp:cNvGraphicFramePr"),
        )

        ET.SubElement(
            frame_properties,
            qn("a:graphicFrameLocks"),
            {
                "noChangeAspect": "1",
            },
        )


    # --------------------------------
    # Graphic Building
    # --------------------------------

    def _build_graphic(
        self,
        container: ET.Element,
        data: dict[str, Any],
        cx: str,
        cy: str,
    ) -> None:

        graphic = ET.SubElement(
            container,
            qn("a:graphic"),
        )

        if (
            "shapes" in data
            or data.get("drawingType")
            == "shapeGroup"
        ):

            self._build_shape_group(
                graphic,
                data,
                cx,
                cy,
            )

        elif (
            data.get("type") == "shape"
            or "paths" in data
            or "geometry" in data
        ):

            self._build_single_shape(
                graphic,
                data,
            )

        elif (
            data.get("drawingType")
            == "diagram"
            or "diagram" in data
        ):

            self._build_diagram(
                graphic,
                data,
            )

        elif data.get(
            "graphicDataXml"
        ):

            self._build_raw_graphic(
                graphic,
                data,
            )

        else:

            self._build_picture(
                graphic,
                data,
                cx,
                cy,
            )


    # --------------------------------
    # Shape Group Building
    # --------------------------------

    def _build_shape_group(
        self,
        graphic: ET.Element,
        data: dict[str, Any],
        cx: str,
        cy: str,
    ) -> None:

        graphic_data = ET.SubElement(
            graphic,
            qn("a:graphicData"),
            {
                "uri":
                    "http://schemas.microsoft.com/"
                    "office/word/2010/"
                    "wordprocessingGroup",
            },
        )

        group = ET.SubElement(
            graphic_data,
            qn("wpg:wgp"),
        )

        ET.SubElement(
            group,
            qn("wpg:cNvGrpSpPr"),
        )

        group_properties = ET.SubElement(
            group,
            qn("wpg:grpSpPr"),
        )

        transform = ET.SubElement(
            group_properties,
            qn("a:xfrm"),
        )

        group_data = data.get(
            "groupTransform",
            {},
        )

        if not isinstance(
            group_data,
            dict,
        ):
            group_data = {}

        offset = group_data.get(
            "offset",
            data.get(
                "offset",
                {
                    "x": 0,
                    "y": 0,
                },
            ),
        )

        extent = group_data.get(
            "extent",
            data.get(
                "extent",
                {
                    "cx": cx,
                    "cy": cy,
                },
            ),
        )

        child_offset = group_data.get(
            "childOffset",
            data.get(
                "childOffset",
                {
                    "x": 0,
                    "y": 0,
                },
            ),
        )

        child_extent = group_data.get(
            "childExtent",
            data.get(
                "childExtent",
                {
                    "cx": cx,
                    "cy": cy,
                },
            ),
        )

        self._append_transform_element(
            transform,
            "a:off",
            offset,
            "x",
            "y",
        )

        self._append_transform_element(
            transform,
            "a:ext",
            extent,
            "cx",
            "cy",
        )

        self._append_transform_element(
            transform,
            "a:chOff",
            child_offset,
            "x",
            "y",
        )

        self._append_transform_element(
            transform,
            "a:chExt",
            child_extent,
            "cx",
            "cy",
        )

        shapes = data.get(
            "shapes",
            [],
        )

        if isinstance(
            shapes,
            list,
        ):

            for shape_data in shapes:

                if isinstance(
                    shape_data,
                    dict,
                ):
                    group.append(
                        self._build_shape_element(
                            shape_data
                        )
                    )


    # --------------------------------
    # Transform Element
    # --------------------------------

    @staticmethod
    def _append_transform_element(
        transform: ET.Element,
        tag_name: str,
        data: Any,
        first_key: str,
        second_key: str,
    ) -> None:

        if not isinstance(
            data,
            dict,
        ):
            data = {}

        ET.SubElement(
            transform,
            qn(tag_name),
            {
                first_key: str(
                    data.get(
                        first_key,
                        0,
                    )
                ),
                second_key: str(
                    data.get(
                        second_key,
                        0,
                    )
                ),
            },
        )


    # --------------------------------
    # Single Shape Building
    # --------------------------------

    def _build_single_shape(
        self,
        graphic: ET.Element,
        data: dict[str, Any],
    ) -> None:

        graphic_data = ET.SubElement(
            graphic,
            qn("a:graphicData"),
            {
                "uri":
                    "http://schemas.microsoft.com/"
                    "office/word/2010/"
                    "wordprocessingShape",
            },
        )

        graphic_data.append(
            self._build_shape_element(
                data
            )
        )


    # --------------------------------
    # Diagram Building
    # --------------------------------

    def _build_diagram(
        self,
        graphic: ET.Element,
        data: dict[str, Any],
    ) -> None:

        diagram_data = data.get(
            "diagram",
            {},
        )

        if not isinstance(
            diagram_data,
            dict,
        ):
            diagram_data = {}

        graphic_data = ET.SubElement(
            graphic,
            qn("a:graphicData"),
            {
                "uri":
                    "http://schemas.openxmlformats.org/"
                    "drawingml/2006/diagram",
            },
        )

        relationship_attributes = {
            qn(f"r:{key}"): str(value)
            for key, value
            in diagram_data.items()
        }

        ET.SubElement(
            graphic_data,
            qn("dgm:relIds"),
            relationship_attributes,
        )


    # --------------------------------
    # Raw Graphic XML
    # --------------------------------

    def _build_raw_graphic(
        self,
        graphic: ET.Element,
        data: dict[str, Any],
    ) -> None:

        from utils.xml import parse_xml_string

        raw_xml = data.get(
            "graphicDataXml"
        )

        if not raw_xml:
            return

        graphic.append(
            parse_xml_string(
                raw_xml
            )
        )


    # --------------------------------
    # Picture Building
    # --------------------------------

    def _build_picture(
        self,
        graphic: ET.Element,
        data: dict[str, Any],
        cx: str,
        cy: str,
    ) -> None:

        graphic_data = ET.SubElement(
            graphic,
            qn("a:graphicData"),
            {
                "uri": self.get_namespace(
                    "pic"
                )
            },
        )

        picture = ET.SubElement(
            graphic_data,
            qn("pic:pic"),
        )

        non_visual = ET.SubElement(
            picture,
            qn("pic:nvPicPr"),
        )

        ET.SubElement(
            non_visual,
            qn("pic:cNvPr"),
            {
                "id": str(
                    data.get(
                        "id",
                        1,
                    )
                ),
                "name": str(
                    data.get(
                        "name",
                        "Picture 1",
                    )
                ),
            },
        )

        c_nv_pic_pr = ET.SubElement(
            non_visual,
            qn("pic:cNvPicPr"),
        )

        ET.SubElement(
            c_nv_pic_pr,
            qn("a:picLocks"),
            {
                "noChangeAspect": "1",
                "noChangeArrowheads": "1",
            },
        )

        self._build_picture_blip(
            picture,
            data,
        )

        self._build_picture_shape(
            picture,
            cx,
            cy,
        )


    # --------------------------------
    # Picture Relationship
    # --------------------------------

    @staticmethod
    def _build_picture_blip(
        picture: ET.Element,
        data: dict[str, Any],
    ) -> None:

        blip_fill = ET.SubElement(
            picture,
            qn("pic:blipFill"),
        )

        relationship_id = data.get(
            "relationshipId",
            data.get(
                "src",
                "",
            ),
        )

        blip = ET.SubElement(
            blip_fill,
            qn("a:blip"),
            {
                qn("r:embed"): str(
                    relationship_id
                )
            },
        )

        ET.SubElement(
            blip,
            qn("a:extLst"),
        )

        ET.SubElement(
            blip_fill,
            qn("a:srcRect"),
        )

        stretch = ET.SubElement(
            blip_fill,
            qn("a:stretch"),
        )

        ET.SubElement(
            stretch,
            qn("a:fillRect"),
        )


    # --------------------------------
    # Picture Shape
    # --------------------------------

    @staticmethod
    def _build_picture_shape(
        picture: ET.Element,
        cx: str,
        cy: str,
    ) -> None:

        shape_properties = ET.SubElement(
            picture,
            qn("pic:spPr"),
            {
                "bwMode": "auto",
            },
        )

        transform = ET.SubElement(
            shape_properties,
            qn("a:xfrm"),
        )

        ET.SubElement(
            transform,
            qn("a:off"),
            {
                "x": "0",
                "y": "0",
            },
        )

        ET.SubElement(
            transform,
            qn("a:ext"),
            {
                "cx": cx,
                "cy": cy,
            },
        )

        preset_geometry = ET.SubElement(
            shape_properties,
            qn("a:prstGeom"),
            {
                "prst": "rect",
            },
        )

        ET.SubElement(
            preset_geometry,
            qn("a:avLst"),
        )

        ET.SubElement(
            shape_properties,
            qn("a:noFill"),
        )


# --------------------------------
# Public API
# --------------------------------

__all__ = [
    "MediaHandler",
]