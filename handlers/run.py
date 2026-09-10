from typing import Any
import xml.etree.ElementTree as ET

from handlers.base import BaseHandler, qn, local_name


# --------------------------------
# Run Handler
# --------------------------------

class RunHandler(BaseHandler):

    # --------------------------------
    # Value Conversion
    # --------------------------------

    @staticmethod
    def _to_number(
        value: Any,
    ) -> Any:

        if value is None:
            return None

        value = str(value)

        if (
            value.isdigit()
            or (
                value.startswith("-")
                and value[1:].isdigit()
            )
        ):
            return int(value)

        return value


    @staticmethod
    def _to_bool(
        value: Any,
    ) -> bool:

        return str(value).lower() not in (
            "0",
            "false",
            "off",
        )


    # --------------------------------
    # Property Attribute Helper
    # --------------------------------

    @staticmethod
    def _read_value(
        element: ET.Element,
        attribute: str = "val",
    ) -> Any:

        return element.attrib.get(
            qn(f"w:{attribute}"),
            "",
        )


    # --------------------------------
    # Simple Boolean Properties
    # --------------------------------

    def _parse_boolean_property(
        self,
        r_pr: ET.Element,
        xml_name: str,
        json_name: str,
        properties: dict[str, Any],
    ) -> None:

        element = r_pr.find(
            qn(f"w:{xml_name}")
        )

        if element is None:
            return

        value = self._to_bool(
            self._read_value(element)
            or "true"
        )

        if value:
            properties[json_name] = True


    # --------------------------------
    # Bold / Italic Parsing
    # --------------------------------

    def _parse_bold_italic(
        self,
        r_pr: ET.Element,
        properties: dict[str, Any],
    ) -> None:

        bold = r_pr.find(
            qn("w:b")
        )

        if bold is not None:

            value = self._to_bool(
                self._read_value(bold)
                or "true"
            )

            properties[
                self.tag_to_name("w:b")
            ] = value

        bold_cs = r_pr.find(
            qn("w:bCs")
        )

        if bold_cs is not None:
            properties["boldCs"] = self._to_bool(
                self._read_value(bold_cs)
                or "true"
            )

        italic = r_pr.find(
            qn("w:i")
        )

        if italic is not None:

            value = self._to_bool(
                self._read_value(italic)
                or "true"
            )

            properties[
                self.tag_to_name("w:i")
            ] = value

        italic_cs = r_pr.find(
            qn("w:iCs")
        )

        if italic_cs is not None:
            properties["italicCs"] = self._to_bool(
                self._read_value(italic_cs)
                or "true"
            )


    # --------------------------------
    # Underline Parsing
    # --------------------------------

    def _parse_underline(
        self,
        r_pr: ET.Element,
        properties: dict[str, Any],
    ) -> None:

        underline = r_pr.find(
            qn("w:u")
        )

        if underline is None:
            return

        values = {
            local_name(key): value
            for key, value
            in underline.attrib.items()
        }

        if (
            len(values) == 1
            and "val" in values
        ):
            properties[
                self.tag_to_name("w:u")
            ] = values["val"]

        elif values:
            properties[
                self.tag_to_name("w:u")
            ] = values


    # --------------------------------
    # Font Parsing
    # --------------------------------

    def _parse_fonts(
        self,
        r_pr: ET.Element,
        properties: dict[str, Any],
    ) -> None:

        fonts = r_pr.find(
            qn("w:rFonts")
        )

        if fonts is None:
            return

        font_data: dict[str, str] = {
            local_name(key): value
            for key, value
            in fonts.attrib.items()
        }

        if not font_data:
            return

        primary_font = (
            font_data.get("ascii")
            or font_data.get("hAnsi")
            or font_data.get("asciiTheme")
            or font_data.get("hAnsiTheme")
            or font_data.get("cstheme")
            or font_data.get("cs")
            or font_data.get("eastAsia")
            or font_data.get("eastAsiaTheme")
            or next(
                iter(font_data.values())
            )
        )

        properties["fontFamily"] = primary_font
        properties["fonts"] = font_data


    # --------------------------------
    # Color Parsing
    # --------------------------------

    def _parse_color(
        self,
        r_pr: ET.Element,
        properties: dict[str, Any],
    ) -> None:

        color = r_pr.find(
            qn("w:color")
        )

        if color is None:
            return

        color_data = {
            local_name(key): value
            for key, value
            in color.attrib.items()
        }

        if (
            len(color_data) == 1
            and "val" in color_data
        ):
            properties[
                self.tag_to_name("w:color")
            ] = color_data["val"]

        elif color_data:
            properties[
                self.tag_to_name("w:color")
            ] = color_data


    # --------------------------------
    # Language Parsing
    # --------------------------------

    @staticmethod
    def _parse_language(
        r_pr: ET.Element,
        properties: dict[str, Any],
    ) -> None:

        language = r_pr.find(
            qn("w:lang")
        )

        if language is None:
            return

        properties["language"] = {
            local_name(key): value
            for key, value
            in language.attrib.items()
        }


    # --------------------------------
    # Shading Parsing
    # --------------------------------

    @staticmethod
    def _parse_shading(
        r_pr: ET.Element,
        properties: dict[str, Any],
    ) -> None:

        shading = r_pr.find(
            qn("w:shd")
        )

        if shading is None:
            return

        properties["shading"] = {
            local_name(key): value
            for key, value
            in shading.attrib.items()
        }


    # --------------------------------
    # Run Properties Parsing
    # --------------------------------

    def _parse_run_properties(
        self,
        r_pr: ET.Element,
    ) -> dict[str, Any]:

        properties: dict[str, Any] = {}

        self._parse_bold_italic(
            r_pr,
            properties,
        )

        self._parse_underline(
            r_pr,
            properties,
        )

        self._parse_boolean_property(
            r_pr,
            "strike",
            self.tag_to_name("w:strike"),
            properties,
        )

        self._parse_boolean_property(
            r_pr,
            "dstrike",
            "dstrike",
            properties,
        )

        self._parse_boolean_property(
            r_pr,
            "caps",
            "caps",
            properties,
        )

        self._parse_boolean_property(
            r_pr,
            "smallCaps",
            "smallCaps",
            properties,
        )

        # Outline / shadow / emboss / imprint.
        for tag_name in (
            "outline",
            "shadow",
            "emboss",
            "imprint",
        ):

            if r_pr.find(
                qn(f"w:{tag_name}")
            ) is not None:
                properties[tag_name] = True

        self._parse_color(
            r_pr,
            properties,
        )

        # Kerning.
        kern = r_pr.find(
            qn("w:kern")
        )

        if kern is not None:
            properties["kern"] = self._to_number(
                self._read_value(kern)
            )

        # Position.
        position = r_pr.find(
            qn("w:position")
        )

        if position is not None:
            properties["position"] = self._to_number(
                self._read_value(position)
            )

        # Border.
        border = r_pr.find(
            qn("w:bdr")
        )

        if border is not None:
            properties["border"] = {
                local_name(key): value
                for key, value
                in border.attrib.items()
            }

        # Font size.
        size = r_pr.find(
            qn("w:sz")
        )

        if size is not None:

            properties[
                self.tag_to_name("w:sz")
            ] = self._to_number(
                self._read_value(size)
            )

        # Complex-script font size.
        size_cs = r_pr.find(
            qn("w:szCs")
        )

        if size_cs is not None:
            properties["fontSizeCs"] = self._to_number(
                self._read_value(size_cs)
            )

        self._parse_fonts(
            r_pr,
            properties,
        )

        # Character style.
        style = r_pr.find(
            qn("w:rStyle")
        )

        if style is not None:
            properties["style"] = style.attrib.get(
                qn("w:val"),
                "",
            )

        # Character spacing.
        spacing = r_pr.find(
            qn("w:spacing")
        )

        if spacing is not None:
            properties["characterSpacing"] = (
                self._to_number(
                    self._read_value(spacing)
                )
            )

        # Character scale.
        width = r_pr.find(
            qn("w:w")
        )

        if width is not None:
            properties["scale"] = self._to_number(
                self._read_value(width)
            )

        # Vertical alignment.
        vertical_alignment = r_pr.find(
            qn("w:vertAlign")
        )

        if vertical_alignment is not None:
            properties[
                self.tag_to_name(
                    "w:vertAlign"
                )
            ] = vertical_alignment.attrib.get(
                qn("w:val"),
                "",
            )

        # Highlight.
        highlight = r_pr.find(
            qn("w:highlight")
        )

        if highlight is not None:
            properties[
                self.tag_to_name(
                    "w:highlight"
                )
            ] = highlight.attrib.get(
                qn("w:val"),
                "",
            )

        self._parse_shading(
            r_pr,
            properties,
        )

        # Hidden / no-proof.
        if r_pr.find(
            qn("w:vanish")
        ) is not None:
            properties["vanish"] = True

        if r_pr.find(
            qn("w:noProof")
        ) is not None:
            properties["noProof"] = True

        self._parse_language(
            r_pr,
            properties,
        )

        return properties


    # --------------------------------
    # XML → JSON
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> dict[str, Any]:

        run_properties: dict[str, Any] = {}

        r_pr = (
            element
            if element.tag == qn("w:rPr")
            else element.find(
                qn("w:rPr")
            )
        )

        if r_pr is not None:
            run_properties = (
                self._parse_run_properties(
                    r_pr
                )
            )

        # Text content.
        texts: list[str] = []

        for text_element in element.findall(
            qn("w:t")
        ):

            if text_element.text:
                texts.append(
                    text_element.text
                )

        text_content = "".join(
            texts
        )

        # Breaks.
        breaks: list[
            dict[str, str]
        ] = []

        for break_element in element.findall(
            qn("w:br")
        ):

            break_type = break_element.attrib.get(
                qn("w:type"),
                "textWrapping",
            )

            break_data = {
                "type": break_type
            }

            clear_value = break_element.attrib.get(
                qn("w:clear")
            )

            if clear_value:
                break_data["clear"] = (
                    clear_value
                )

            breaks.append(
                break_data
            )

        # Symbols.
        symbols: list[
            dict[str, str]
        ] = []

        for symbol_element in element.findall(
            qn("w:sym")
        ):

            symbols.append(
                {
                    local_name(key): value
                    for key, value
                    in symbol_element.attrib.items()
                }
            )

        # Carriage return.
        has_carriage_return = (
            element.find(
                qn("w:cr")
            )
            is not None
        )

        # Tab.
        has_tab = (
            element.find(
                qn("w:tab")
            )
            is not None
        )

        # Drawings.
        drawings: list[
            dict[str, Any]
        ] = []

        drawing_elements = element.iter(
            qn("w:drawing")
        )

        for drawing in drawing_elements:

            from handlers.media import MediaHandler

            drawings.append(
                MediaHandler().to_json(
                    drawing
                )
            )

        # VML shapes.
        shapes: list[
            dict[str, Any]
        ] = []

        for pict in element.findall(
            qn("w:pict")
        ):

            for child in pict:

                shape_type = local_name(
                    child.tag
                )

                raw_attributes = {
                    local_name(key): value
                    for key, value
                    in child.attrib.items()
                }

                shape_entry: dict[str, Any] = {
                    "shapeType": shape_type
                }

                style_value = raw_attributes.pop(
                    "style",
                    None,
                )

                if style_value:

                    from handlers.media import MediaHandler

                    shape_entry["style"] = (
                        MediaHandler.parse_vml_style(
                            style_value
                        )
                    )

                image_data = child.find(
                    qn("v:imagedata")
                )

                if image_data is not None:

                    raw_attributes[
                        "relationshipId"
                    ] = (
                        image_data.attrib.get(
                            qn("r:id")
                        )
                        or image_data.attrib.get(
                            qn("r:href"),
                            "",
                        )
                    )

                if raw_attributes:
                    shape_entry["attributes"] = (
                        raw_attributes
                    )

                shapes.append(
                    shape_entry
                )

        # Build JSON result.
        if simple:

            result: dict[str, Any] = {
                "text": text_content
            }

            for key, value in (
                run_properties.items()
            ):

                if key == "fontFamily":
                    result["font"] = value

                elif key == "fontSize":
                    result["size"] = value

                else:
                    result[key] = value

        else:

            result = {
                "type": self.tag_to_name(
                    "w:r"
                ),
                "text": text_content,
            }

            if run_properties:
                result["properties"] = (
                    run_properties
                )

        if breaks:
            result["breaks"] = breaks

        if symbols:
            result["symbols"] = symbols

        if has_carriage_return:
            result[
                "hasCarriageReturn"
            ] = True

        if has_tab:
            result["hasTab"] = True

        if drawings:
            result["drawings"] = drawings

        if shapes:
            result["shapes"] = shapes

        return result


    # --------------------------------
    # Property Collection
    # --------------------------------

    @staticmethod
    def _collect_flat_properties(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        properties = dict(
            data.get(
                "runProperties"
            )
            or data.get(
                "properties"
            )
            or {}
        )

        property_names = (
            "bold",
            "b",
            "boldCs",
            "italic",
            "i",
            "italicCs",
            "underline",
            "u",
            "strike",
            "strikethrough",
            "dstrike",
            "caps",
            "smallCaps",
            "outline",
            "shadow",
            "emboss",
            "imprint",
            "color",
            "fontSize",
            "size",
            "sz",
            "fontSizeCs",
            "szCs",
            "fontFamily",
            "font",
            "rFonts",
            "fonts",
            "fontCs",
            "highlight",
            "style",
            "rStyle",
            "characterStyle",
            "shading",
            "verticalAlignment",
            "vanish",
            "noProof",
            "subscript",
            "superscript",
            "characterSpacing",
            "scale",
            "w",
            "spacing",
            "kern",
            "position",
            "border",
            "language",
        )

        for key in property_names:

            if key in data and key not in properties:
                properties[key] = data[key]

        return properties


    # --------------------------------
    # Font XML
    # --------------------------------

    @staticmethod
    def _build_fonts(
        r_pr: ET.Element,
        props: dict[str, Any],
    ) -> None:

        fonts_data = props.get(
            "fonts"
        )

        font_family = (
            props.get("font")
            or props.get("fontFamily")
            or props.get("rFonts")
        )

        if (
            fonts_data
            and isinstance(
                fonts_data,
                dict,
            )
        ):

            attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in fonts_data.items()
            }

            ET.SubElement(
                r_pr,
                qn("w:rFonts"),
                attributes,
            )

            return

        if not font_family:
            return

        font_string = str(
            font_family
        )

        theme_fonts = (
            "minorHAnsi",
            "majorHAnsi",
            "minorAscii",
            "majorAscii",
            "minorBidi",
            "majorBidi",
            "minorEastAsia",
            "majorEastAsia",
        )

        if (
            font_string.lower()
            in {
                value.lower()
                for value in theme_fonts
            }
            or "theme" in font_string.lower()
        ):

            ET.SubElement(
                r_pr,
                qn("w:rFonts"),
                {
                    qn("w:asciiTheme"):
                        font_string,
                    qn("w:hAnsiTheme"):
                        font_string,
                    qn("w:cstheme"):
                        font_string,
                },
            )

            return

        attributes = {
            qn("w:ascii"):
                font_string,
            qn("w:hAnsi"):
                font_string,
        }

        if props.get("fontCs"):
            attributes[
                qn("w:cs")
            ] = str(
                props["fontCs"]
            )

        ET.SubElement(
            r_pr,
            qn("w:rFonts"),
            attributes,
        )


    # --------------------------------
    # Boolean Property XML
    # --------------------------------

    @staticmethod
    def _append_boolean(
        r_pr: ET.Element,
        tag_name: str,
        value: Any,
    ) -> None:

        if value:
            ET.SubElement(
                r_pr,
                qn(f"w:{tag_name}")
            )


    # --------------------------------
    # Color XML
    # --------------------------------

    @staticmethod
    def _build_color(
        r_pr: ET.Element,
        value: Any,
    ) -> None:

        if not value:
            return

        if isinstance(
            value,
            dict,
        ):

            attributes = {
                qn(f"w:{key}"):
                    (
                        str(item).lstrip("#")
                        if key == "val"
                        else str(item)
                    )
                for key, item
                in value.items()
            }

        else:

            attributes = {
                qn("w:val"):
                    str(value).lstrip("#")
            }

        ET.SubElement(
            r_pr,
            qn("w:color"),
            attributes,
        )


    # --------------------------------
    # Underline XML
    # --------------------------------

    @staticmethod
    def _build_underline(
        r_pr: ET.Element,
        value: Any,
    ) -> None:

        if not value:
            return

        if isinstance(
            value,
            dict,
        ):

            attributes = {
                qn(f"w:{key}"): str(item)
                for key, item
                in value.items()
            }

        else:

            underline_value = (
                "single"
                if isinstance(
                    value,
                    bool,
                )
                else str(value)
            )

            attributes = {
                qn("w:val"):
                    underline_value
            }

        ET.SubElement(
            r_pr,
            qn("w:u"),
            attributes,
        )


    # --------------------------------
    # Run Properties XML
    # --------------------------------

    def _build_run_properties(
        self,
        r: ET.Element,
        props: dict[str, Any],
    ) -> None:

        if not props:
            return

        r_pr = ET.SubElement(
            r,
            qn("w:rPr"),
        )

        # Character style.
        style = (
            props.get("style")
            or props.get("rStyle")
            or props.get("characterStyle")
        )

        if style:
            ET.SubElement(
                r_pr,
                qn("w:rStyle"),
                {
                    qn("w:val"):
                        str(style)
                },
            )

        # Fonts.
        self._build_fonts(
            r_pr,
            props,
        )

        # Character spacing.
        character_spacing = (
            props.get("characterSpacing")
            if props.get(
                "characterSpacing"
            ) is not None
            else props.get("spacing")
        )

        if (
            character_spacing is not None
            and (
                str(
                    character_spacing
                ).isdigit()
                or (
                    str(
                        character_spacing
                    ).startswith("-")
                    and str(
                        character_spacing
                    )[1:].isdigit()
                )
            )
        ):

            ET.SubElement(
                r_pr,
                qn("w:spacing"),
                {
                    qn("w:val"):
                        str(character_spacing)
                },
            )

        # Character scale.
        scale = (
            props.get("scale")
            if props.get("scale") is not None
            else (
                props.get(
                    "characterScale"
                )
                or props.get("w")
            )
        )

        if (
            scale is not None
            and str(scale).isdigit()
        ):

            ET.SubElement(
                r_pr,
                qn("w:w"),
                {
                    qn("w:val"):
                        str(scale)
                },
            )

        # Kerning.
        if props.get("kern") is not None:

            ET.SubElement(
                r_pr,
                qn("w:kern"),
                {
                    qn("w:val"):
                        str(props["kern"])
                },
            )

        # Position.
        if props.get("position") is not None:

            ET.SubElement(
                r_pr,
                qn("w:position"),
                {
                    qn("w:val"):
                        str(props["position"])
                },
            )

        # Bold.
        bold = (
            props.get("bold")
            if props.get("bold") is not None
            else props.get("b")
        )

        if bold:
            ET.SubElement(
                r_pr,
                qn("w:b")
            )

        if props.get("boldCs"):
            ET.SubElement(
                r_pr,
                qn("w:bCs")
            )

        # Italic.
        italic = (
            props.get("italic")
            if props.get("italic") is not None
            else props.get("i")
        )

        if italic:
            ET.SubElement(
                r_pr,
                qn("w:i")
            )

        if props.get("italicCs"):
            ET.SubElement(
                r_pr,
                qn("w:iCs")
            )

        # Caps.
        if props.get("caps"):
            ET.SubElement(
                r_pr,
                qn("w:caps")
            )

        if props.get("smallCaps"):
            ET.SubElement(
                r_pr,
                qn("w:smallCaps")
            )

        # Strike.
        if (
            props.get("strikethrough")
            or props.get("strike")
        ):
            ET.SubElement(
                r_pr,
                qn("w:strike")
            )

        if (
            props.get("dstrike")
            or props.get(
                "doubleStrikethrough"
            )
        ):
            ET.SubElement(
                r_pr,
                qn("w:dstrike")
            )

        # Outline / shadow / emboss / imprint.
        for tag_name in (
            "outline",
            "shadow",
            "emboss",
            "imprint",
        ):

            if props.get(tag_name):
                ET.SubElement(
                    r_pr,
                    qn(f"w:{tag_name}")
                )

        # Underline.
        underline = (
            props.get("underline")
            if props.get(
                "underline"
            ) is not None
            else props.get("u")
        )

        self._build_underline(
            r_pr,
            underline,
        )

        # Color.
        self._build_color(
            r_pr,
            props.get("color"),
        )

        # Font size.
        font_size = (
            props.get("fontSize")
            if props.get(
                "fontSize"
            ) is not None
            else (
                props.get("size")
                if props.get(
                    "size"
                ) is not None
                else props.get("sz")
            )
        )

        if font_size is not None:

            if (
                isinstance(
                    font_size,
                    str,
                )
                and font_size.endswith(
                    "pt"
                )
            ):

                try:
                    font_size = int(
                        float(
                            font_size[:-2]
                        )
                        * 2
                    )
                except ValueError:
                    pass

            ET.SubElement(
                r_pr,
                qn("w:sz"),
                {
                    qn("w:val"):
                        str(font_size)
                },
            )

        font_size_cs = (
            props.get("fontSizeCs")
            or props.get("szCs")
        )

        if font_size_cs:

            ET.SubElement(
                r_pr,
                qn("w:szCs"),
                {
                    qn("w:val"):
                        str(font_size_cs)
                },
            )

        # Highlight.
        if props.get("highlight"):

            ET.SubElement(
                r_pr,
                qn("w:highlight"),
                {
                    qn("w:val"):
                        str(
                            props["highlight"]
                        )
                },
            )

        # Border.
        if props.get("border"):

            attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in props["border"].items()
            }

            ET.SubElement(
                r_pr,
                qn("w:bdr"),
                attributes,
            )

        # Shading.
        if props.get("shading"):

            attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in props["shading"].items()
            }

            ET.SubElement(
                r_pr,
                qn("w:shd"),
                attributes,
            )

        # Hidden / no-proof.
        if props.get("vanish"):
            ET.SubElement(
                r_pr,
                qn("w:vanish")
            )

        if props.get("noProof"):
            ET.SubElement(
                r_pr,
                qn("w:noProof")
            )

        # Language.
        if props.get("language"):

            attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in props["language"].items()
            }

            ET.SubElement(
                r_pr,
                qn("w:lang"),
                attributes,
            )

        # Vertical alignment.
        vertical_alignment = props.get(
            "verticalAlignment"
        )

        if props.get("subscript"):
            vertical_alignment = "subscript"

        elif props.get("superscript"):
            vertical_alignment = "superscript"

        if vertical_alignment:

            ET.SubElement(
                r_pr,
                qn("w:vertAlign"),
                {
                    qn("w:val"):
                        str(vertical_alignment)
                },
            )

        # Apply OpenXML schema ordering.
        from handlers.base import (
            RPR_ORDER,
            sort_children_by_schema,
        )

        sort_children_by_schema(
            r_pr,
            RPR_ORDER,
        )


    # --------------------------------
    # Symbols XML
    # --------------------------------

    @staticmethod
    def _append_symbols(
        r: ET.Element,
        symbols: Any,
    ) -> None:

        if not isinstance(
            symbols,
            list,
        ):
            return

        for symbol_data in symbols:

            if not isinstance(
                symbol_data,
                dict,
            ):
                continue

            attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in symbol_data.items()
            }

            ET.SubElement(
                r,
                qn("w:sym"),
                attributes,
            )


    # --------------------------------
    # Breaks XML
    # --------------------------------

    @staticmethod
    def _append_breaks(
        r: ET.Element,
        breaks: Any,
    ) -> None:

        if not isinstance(
            breaks,
            list,
        ):
            return

        for break_data in breaks:

            if not isinstance(
                break_data,
                dict,
            ):
                continue

            attributes: dict[str, str] = {}

            break_type = break_data.get(
                "type"
            )

            if (
                break_type
                and break_type
                != "textWrapping"
            ):
                attributes[
                    qn("w:type")
                ] = str(
                    break_type
                )

            clear_value = break_data.get(
                "clear"
            )

            if clear_value:
                attributes[
                    qn("w:clear")
                ] = str(
                    clear_value
                )

            ET.SubElement(
                r,
                qn("w:br"),
                attributes,
            )


    # --------------------------------
    # VML Shapes XML
    # --------------------------------

    @staticmethod
    def _append_shapes(
        r: ET.Element,
        shapes: Any,
    ) -> None:

        if not isinstance(
            shapes,
            list,
        ):
            return

        for shape_data in shapes:

            if not isinstance(
                shape_data,
                dict,
            ):
                continue

            if "xml" in shape_data:

                from utils.xml import parse_xml_string

                r.append(
                    parse_xml_string(
                        shape_data["xml"]
                    )
                )

                continue

            pict = ET.SubElement(
                r,
                qn("w:pict"),
            )

            shape_type = shape_data.get(
                "shapeType",
                "shape",
            )

            attributes: dict[str, str] = {}

            raw_attributes = (
                shape_data.get(
                    "attributes",
                    {},
                )
            )

            if isinstance(
                raw_attributes,
                dict,
            ):

                for key, value in raw_attributes.items():

                    if key == "spid":
                        attributes[
                            qn("o:spid")
                        ] = str(value)

                    elif key == "allowincell":
                        attributes[
                            qn("o:allowincell")
                        ] = str(value)

                    elif key != "relationshipId":
                        attributes[key] = str(value)

            # VML style.
            if "style" in shape_data:

                from handlers.media import MediaHandler

                style_value = (
                    MediaHandler.build_vml_style(
                        shape_data["style"]
                    )
                )

                if style_value:
                    attributes["style"] = (
                        style_value
                    )

            shape_element = ET.SubElement(
                pict,
                qn(
                    f"v:{shape_type}"
                ),
                attributes,
            )

            relationship_id = (
                raw_attributes.get(
                    "relationshipId"
                )
                if isinstance(
                    raw_attributes,
                    dict,
                )
                else None
            ) or shape_data.get(
                "relationshipId"
            )

            if relationship_id:

                ET.SubElement(
                    shape_element,
                    qn("v:imagedata"),
                    {
                        qn("r:id"):
                            str(
                                relationship_id
                            )
                    },
                )


    # --------------------------------
    # JSON → XML
    # --------------------------------

    def to_xml(
        self,
        data: dict[str, Any],
    ) -> ET.Element:

        run = ET.Element(
            qn("w:r")
        )

        properties = (
            self._collect_flat_properties(
                data
            )
        )

        if properties:
            self._build_run_properties(
                run,
                properties,
            )

        # Symbols.
        self._append_symbols(
            run,
            data.get("symbols"),
        )

        # Tab.
        if data.get("hasTab"):
            ET.SubElement(
                run,
                qn("w:tab"),
            )

        # Carriage return.
        if data.get(
            "hasCarriageReturn"
        ):
            ET.SubElement(
                run,
                qn("w:cr"),
            )

        # Text.
        text = data.get(
            "text",
            "",
        )

        if text:

            text_element = ET.SubElement(
                run,
                qn("w:t"),
            )

            text_element.text = str(
                text
            )

            # Preserve leading/trailing whitespace.
            if (
                text_element.text.startswith(
                    " "
                )
                or text_element.text.endswith(
                    " "
                )
                or "\t" in text_element.text
            ):

                text_element.set(
                    qn("xml:space"),
                    "preserve",
                )

        # Breaks.
        self._append_breaks(
            run,
            data.get("breaks"),
        )

        # Drawings.
        drawings = data.get(
            "drawings",
            [],
        )

        if isinstance(
            drawings,
            list,
        ):

            for drawing_data in drawings:

                from handlers.media import MediaHandler

                run.append(
                    MediaHandler().to_xml(
                        drawing_data
                    )
                )

        # VML pictures / shapes.
        shapes = data.get(
            "shapes",
            data.get(
                "pictures",
                [],
            ),
        )

        self._append_shapes(
            run,
            shapes,
        )

        return run