from typing import Any
import xml.etree.ElementTree as ET

from handlers.base import BaseHandler, qn, local_name
from handlers.run import RunHandler


# --------------------------------
# Numbering Handler
# --------------------------------

class NumberingHandler(BaseHandler):

    # --------------------------------
    # Conversion Helpers
    # --------------------------------

    @staticmethod
    def _to_int_if_possible(
        value: Any,
        default: Any = "",
    ) -> Any:

        if value is None:
            return default

        value_str = str(value)

        if (
            value_str.isdigit()
            or (
                value_str.startswith("-")
                and value_str[1:].isdigit()
            )
        ):
            return int(value_str)

        return value


    @staticmethod
    def _to_bool(
        value: Any,
    ) -> bool:

        return value in (
            True,
            1,
            "1",
            "true",
            "True",
        )


    # --------------------------------
    # Indentation Parsing
    # --------------------------------

    def _parse_indent(
        self,
        p_pr: ET.Element,
    ) -> dict[str, Any] | None:

        indent_element = p_pr.find(
            qn("w:ind")
        )

        if indent_element is None:
            return None

        indent: dict[str, Any] = {}

        attributes = (
            ("left", "left"),
            ("right", "right"),
            ("start", "start"),
            ("end", "end"),
            ("hanging", "hanging"),
            ("firstLine", "firstLine"),
        )

        for xml_name, json_name in attributes:

            value = indent_element.attrib.get(
                qn(f"w:{xml_name}")
            )

            if value is not None:
                indent[json_name] = (
                    self._to_int_if_possible(
                        value
                    )
                )

        return indent or None


    # --------------------------------
    # Tabs Parsing
    # --------------------------------

    def _parse_tabs(
        self,
        p_pr: ET.Element,
    ) -> list[dict[str, Any]] | None:

        tabs_element = p_pr.find(
            qn("w:tabs")
        )

        if tabs_element is None:
            return None

        tabs: list[dict[str, Any]] = []

        for tab in tabs_element.findall(
            qn("w:tab")
        ):

            tab_data: dict[str, Any] = {}

            for key, value in tab.attrib.items():

                tab_data[
                    local_name(key)
                ] = self._to_int_if_possible(
                    value
                )

            if tab_data:
                tabs.append(
                    tab_data
                )

        return tabs or None


    # --------------------------------
    # Run Properties Parsing
    # --------------------------------

    def _parse_run_properties(
        self,
        r_pr: ET.Element,
    ) -> dict[str, Any] | None:

        run_handler = RunHandler()

        run_data = run_handler.to_json(
            r_pr,
            simple=True,
        )

        if not run_data:
            return None

        clean_data = {
            key: value
            for key, value in run_data.items()
            if key not in (
                "text",
                "type",
            )
        }

        return clean_data or None


    # --------------------------------
    # Abstract Number Parsing
    # --------------------------------

    def _parse_abstract_number(
        self,
        abstract_element: ET.Element,
    ) -> dict[str, Any]:

        abstract_id = abstract_element.attrib.get(
            qn("w:abstractNumId"),
            "",
        )

        result: dict[str, Any] = {
            "id": abstract_id,
        }

        # Basic abstract numbering properties.
        property_map = (
            ("nsid", "nsid"),
            ("multiLevelType", "multiLevelType"),
            ("tmpl", "tmpl"),
            ("name", "name"),
            ("styleLink", "styleLink"),
            ("numStyleLink", "numStyleLink"),
        )

        for xml_name, json_name in property_map:

            element = abstract_element.find(
                qn(f"w:{xml_name}")
            )

            if element is None:
                continue

            result[json_name] = element.attrib.get(
                qn("w:val"),
                "",
            )

        # Numbering levels.
        levels: list[dict[str, Any]] = []

        for level_element in abstract_element.findall(
            qn("w:lvl")
        ):
            levels.append(
                self._parse_level(
                    level_element
                )
            )

        result["levels"] = levels

        return result


    # --------------------------------
    # Numbering Level Parsing
    # --------------------------------

    def _parse_level(
        self,
        level_element: ET.Element,
    ) -> dict[str, Any]:

        level_value = level_element.attrib.get(
            qn("w:ilvl"),
            "0",
        )

        level: dict[str, Any] = {
            "level": self._to_int_if_possible(
                level_value,
                0,
            ),
        }

        # Level attributes.
        tplc = level_element.attrib.get(
            qn("w:tplc")
        )

        if tplc is not None:
            level["tplc"] = tplc

        tentative = level_element.attrib.get(
            qn("w:tentative")
        )

        if tentative is not None:
            level["tentative"] = self._to_bool(
                tentative
            )

        # Level child properties.
        self._parse_level_basic_properties(
            level_element,
            level,
        )

        self._parse_level_paragraph_properties(
            level_element,
            level,
        )

        self._parse_level_run_properties(
            level_element,
            level,
        )

        return level


    # --------------------------------
    # Level Basic Properties
    # --------------------------------

    def _parse_level_basic_properties(
        self,
        level_element: ET.Element,
        level: dict[str, Any],
    ) -> None:

        property_map = (
            ("start", "start", True),
            ("numFmt", "format", False),
            ("lvlRestart", "restart", True),
            ("pStyle", "style", False),
            ("suff", "suffix", False),
            ("lvlText", "text", False),
            ("lvlPicBulletId", "lvlPicBulletId", True),
            ("lvlJc", "alignment", False),
        )

        for xml_name, json_name, numeric in property_map:

            element = level_element.find(
                qn(f"w:{xml_name}")
            )

            if element is None:
                continue

            value = element.attrib.get(
                qn("w:val"),
                "",
            )

            level[json_name] = (
                self._to_int_if_possible(value)
                if numeric
                else value
            )


    # --------------------------------
    # Level Paragraph Properties
    # --------------------------------

    def _parse_level_paragraph_properties(
        self,
        level_element: ET.Element,
        level: dict[str, Any],
    ) -> None:

        paragraph_properties = level_element.find(
            qn("w:pPr")
        )

        if paragraph_properties is None:
            return

        indent = self._parse_indent(
            paragraph_properties
        )

        if indent:
            level["indent"] = indent

        tabs = self._parse_tabs(
            paragraph_properties
        )

        if tabs:
            level["tabs"] = tabs


    # --------------------------------
    # Level Run Properties
    # --------------------------------

    def _parse_level_run_properties(
        self,
        level_element: ET.Element,
        level: dict[str, Any],
    ) -> None:

        run_properties = level_element.find(
            qn("w:rPr")
        )

        if run_properties is None:
            return

        run_data = self._parse_run_properties(
            run_properties
        )

        if not run_data:
            return

        level["runProperties"] = run_data

        # Keep convenient font shortcut.
        if "fonts" in run_data:
            level["fonts"] = run_data["fonts"]

        elif "font" in run_data:
            level["fonts"] = {
                "ascii": run_data["font"],
                "hAnsi": run_data["font"],
            }


    # --------------------------------
    # Number Instance Parsing
    # --------------------------------

    @staticmethod
    def _parse_number_instance(
        num_element: ET.Element,
    ) -> dict[str, Any]:

        num_id = num_element.attrib.get(
            qn("w:numId"),
            "",
        )

        abstract_element = num_element.find(
            qn("w:abstractNumId")
        )

        abstract_id = ""

        if abstract_element is not None:
            abstract_id = abstract_element.attrib.get(
                qn("w:val"),
                "",
            )

        return {
            "numId": num_id,
            "abstractNumId": abstract_id,
        }


    # --------------------------------
    # XML → JSON
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
    ) -> dict[str, Any]:

        abstract_numbering: list[dict[str, Any]] = []

        for abstract_element in element.findall(
            qn("w:abstractNum")
        ):
            abstract_numbering.append(
                self._parse_abstract_number(
                    abstract_element
                )
            )

        numbering: list[dict[str, Any]] = []

        for num_element in element.findall(
            qn("w:num")
        ):
            numbering.append(
                self._parse_number_instance(
                    num_element
                )
            )

        return {
            "abstractNumbering": abstract_numbering,
            "numbering": numbering,
        }


    # --------------------------------
    # Indentation XML Building
    # --------------------------------

    @staticmethod
    def _build_indent(
        parent: ET.Element,
        indent_data: Any,
    ) -> None:

        if not isinstance(
            indent_data,
            dict,
        ):
            return

        attributes = {
            qn(f"w:{key}"): str(value)
            for key, value
            in indent_data.items()
        }

        if attributes:
            ET.SubElement(
                parent,
                qn("w:ind"),
                attributes,
            )


    # --------------------------------
    # Tabs XML Building
    # --------------------------------

    @staticmethod
    def _build_tabs(
        parent: ET.Element,
        tabs_data: Any,
    ) -> None:

        if not isinstance(
            tabs_data,
            list,
        ):
            return

        tabs_element = ET.SubElement(
            parent,
            qn("w:tabs"),
        )

        for tab_data in tabs_data:

            if not isinstance(
                tab_data,
                dict,
            ):
                continue

            attributes = {
                qn(f"w:{key}"): str(value)
                for key, value
                in tab_data.items()
            }

            ET.SubElement(
                tabs_element,
                qn("w:tab"),
                attributes,
            )


    # --------------------------------
    # Level Paragraph XML
    # --------------------------------

    def _build_level_paragraph_properties(
        self,
        level_element: ET.Element,
        level_data: dict[str, Any],
    ) -> None:

        indent_data = level_data.get(
            "indent"
        )

        tabs_data = level_data.get(
            "tabs"
        )

        if not indent_data and not tabs_data:
            return

        paragraph_properties = ET.SubElement(
            level_element,
            qn("w:pPr"),
        )

        # Schema order: tabs before ind.
        if tabs_data:
            self._build_tabs(
                paragraph_properties,
                tabs_data,
            )

        if indent_data:
            self._build_indent(
                paragraph_properties,
                indent_data,
            )


    # --------------------------------
    # Level Run XML
    # --------------------------------

    def _build_level_run_properties(
        self,
        level_element: ET.Element,
        level_data: dict[str, Any],
    ) -> None:

        run_properties_data = (
            level_data.get(
                "runProperties"
            )
            or level_data.get(
                "rPr"
            )
        )

        fonts_data = level_data.get(
            "fonts"
        )

        if (
            isinstance(
                run_properties_data,
                dict,
            )
            and run_properties_data
        ):

            dummy_run = {
                "runProperties":
                    run_properties_data,
            }

            run_element = RunHandler().to_xml(
                dummy_run
            )

            run_properties = run_element.find(
                qn("w:rPr")
            )

            if run_properties is not None:
                level_element.append(
                    run_properties
                )

            return

        if not fonts_data:
            return

        if not isinstance(
            fonts_data,
            dict,
        ):
            return

        run_properties = ET.SubElement(
            level_element,
            qn("w:rPr"),
        )

        font_attributes = {
            qn(f"w:{key}"): str(value)
            for key, value
            in fonts_data.items()
        }

        ET.SubElement(
            run_properties,
            qn("w:rFonts"),
            font_attributes,
        )


    # --------------------------------
    # Level XML Building
    # --------------------------------

    def _build_level(
        self,
        level_data: dict[str, Any],
    ) -> ET.Element:

        level_attributes = {
            qn("w:ilvl"): str(
                level_data.get(
                    "level",
                    "0",
                )
            )
        }

        if "tplc" in level_data:
            level_attributes[
                qn("w:tplc")
            ] = str(
                level_data["tplc"]
            )

        if level_data.get(
            "tentative"
        ):
            level_attributes[
                qn("w:tentative")
            ] = "1"

        level_element = ET.Element(
            qn("w:lvl"),
            level_attributes,
        )

        # Strict OpenXML schema order.
        self._build_level_basic_properties(
            level_element,
            level_data,
        )

        self._build_level_paragraph_properties(
            level_element,
            level_data,
        )

        self._build_level_run_properties(
            level_element,
            level_data,
        )

        return level_element


    # --------------------------------
    # Level Basic XML
    # --------------------------------

    @staticmethod
    def _build_level_basic_properties(
        level_element: ET.Element,
        level_data: dict[str, Any],
    ) -> None:

        property_map = (
            ("start", "start"),
            ("format", "numFmt"),
            ("restart", "lvlRestart"),
            ("style", "pStyle"),
            ("suffix", "suff"),
            ("text", "lvlText"),
            ("lvlPicBulletId", "lvlPicBulletId"),
            ("alignment", "lvlJc"),
        )

        for json_name, xml_name in property_map:

            if json_name not in level_data:
                continue

            ET.SubElement(
                level_element,
                qn(f"w:{xml_name}"),
                {
                    qn("w:val"): str(
                        level_data[json_name]
                    )
                },
            )


    # --------------------------------
    # Abstract Number XML
    # --------------------------------

    def _build_abstract_number(
        self,
        abstract_data: dict[str, Any],
    ) -> ET.Element:

        abstract_element = ET.Element(
            qn("w:abstractNum"),
            {
                qn("w:abstractNumId"): str(
                    abstract_data.get(
                        "id",
                        "0",
                    )
                )
            },
        )

        # Schema order.
        property_map = (
            ("nsid", "nsid"),
            ("multiLevelType", "multiLevelType"),
            ("tmpl", "tmpl"),
            ("name", "name"),
            ("styleLink", "styleLink"),
            ("numStyleLink", "numStyleLink"),
        )

        for json_name, xml_name in property_map:

            if json_name not in abstract_data:
                continue

            ET.SubElement(
                abstract_element,
                qn(f"w:{xml_name}"),
                {
                    qn("w:val"): str(
                        abstract_data[json_name]
                    )
                },
            )

        levels = abstract_data.get(
            "levels",
            [],
        )

        if isinstance(
            levels,
            list,
        ):

            for level_data in levels:

                if isinstance(
                    level_data,
                    dict,
                ):
                    abstract_element.append(
                        self._build_level(
                            level_data
                        )
                    )

        return abstract_element


    # --------------------------------
    # Number Instance XML
    # --------------------------------

    @staticmethod
    def _build_number_instance(
        item: dict[str, Any],
    ) -> ET.Element:

        num = ET.Element(
            qn("w:num"),
            {
                qn("w:numId"): str(
                    item.get(
                        "numId",
                        "",
                    )
                )
            },
        )

        ET.SubElement(
            num,
            qn("w:abstractNumId"),
            {
                qn("w:val"): str(
                    item.get(
                        "abstractNumId",
                        "",
                    )
                )
            },
        )

        return num


    # --------------------------------
    # JSON → XML
    # --------------------------------

    def to_xml(
        self,
        data: dict[str, Any],
    ) -> ET.Element:

        root = ET.Element(
            qn("w:numbering")
        )

        abstract_numbering = data.get(
            "abstractNumbering",
            [],
        )

        if isinstance(
            abstract_numbering,
            list,
        ):

            for abstract_data in abstract_numbering:

                if not isinstance(
                    abstract_data,
                    dict,
                ):
                    continue

                root.append(
                    self._build_abstract_number(
                        abstract_data
                    )
                )

        numbering = data.get(
            "numbering",
            [],
        )

        if isinstance(
            numbering,
            list,
        ):

            for item in numbering:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                root.append(
                    self._build_number_instance(
                        item
                    )
                )

        return root


    # --------------------------------
    # Preset Numbering IDs
    # --------------------------------

    @staticmethod
    def get_known_preset_id(
        name_or_symbol: str,
    ) -> int | None:

        raw = str(
            name_or_symbol
        ).strip()

        value = raw.lower()

        if not value:
            return 1

        # Upper Alphabet.
        if (
            raw in (
                "A.",
                "A)",
                "A",
                "B.",
                "B)",
            )
            or value in (
                "upper_alpha",
                "upper_letter",
                "abc_upper",
                "capitals",
            )
        ):
            return 14

        # Lower Alphabet.
        if (
            raw in (
                "a.",
                "a)",
                "a",
                "b.",
                "b)",
            )
            or value in (
                "alpha",
                "lower_alpha",
                "lower_letter",
                "letter",
                "abc",
                "alphabet",
            )
        ):
            return 13

        # Upper Roman.
        if (
            raw in (
                "I.",
                "I)",
                "I",
                "II.",
                "IV.",
                "VI.",
            )
            or value in (
                "upper_roman",
                "roman_upper",
            )
        ):
            return 16

        # Lower Roman.
        if (
            raw in (
                "i.",
                "i)",
                "i",
                "ii.",
                "iv.",
                "vi.",
            )
            or value in (
                "roman",
                "lower_roman",
                "roman_lower",
            )
        ):
            return 15

        # Standard Bullet.
        if value in (
            "true",
            "bullet",
            "bullets",
            "disc",
            "circle_filled",
            "default",
            "•",
            "bull",
        ):
            return 1

        # Arrow / Chevron.
        if value in (
            ">",
            ">>",
            "arrow",
            "chevron",
            "right",
            "›",
            "»",
            "➢",
            "➔",
            "→",
            "pointer",
            "caret",
        ):
            return 2

        # Decimal / Numbered.
        if value in (
            "1.",
            "1)",
            "decimal",
            "number",
            "numbered",
            "numeric",
            "digits",
            "count",
            "num",
        ):
            return 3

        # Dot.
        if value in (
            ".",
            "..",
            "dot",
            "dots",
            "period",
        ):
            return 4

        # Dash / Hyphen.
        if value in (
            "-",
            "--",
            "dash",
            "hyphen",
            "minus",
            "–",
            "—",
            "en_dash",
            "em_dash",
        ):
            return 5

        # Checkmark / Done.
        if value in (
            "check",
            "checkmark",
            "tick",
            "✓",
            "✔",
            "☑",
            "done",
            "correct",
            "success",
        ):
            return 6

        # Star.
        if value in (
            "star",
            "stars",
            "★",
            "☆",
            "⭐",
            "✦",
            "✧",
            "asterisk",
            "*",
        ):
            return 7

        # Square.
        if value in (
            "square",
            "box",
            "▪",
            "▫",
            "■",
            "□",
            "rect",
            "block",
        ):
            return 8

        # Diamond.
        if value in (
            "diamond",
            "rhombus",
            "◆",
            "◇",
            "❖",
            "🔹",
            "🔸",
            "gem",
        ):
            return 9

        # Circle / Hollow.
        if value in (
            "circle",
            "hollow_circle",
            "ring",
            "○",
            "◯",
            "⭕",
            "o",
        ):
            return 10

        # Triangle / Play.
        if value in (
            "triangle",
            "play",
            "▲",
            "▶",
            "►",
            "▸",
            "tri",
        ):
            return 11

        # Hand / Pointing.
        if value in (
            "hand",
            "point",
            "finger",
            "👉",
            "☞",
            "☛",
            "hand_point",
        ):
            return 12

        return None


    # --------------------------------
    # Bullet Level Generator
    # --------------------------------

    @staticmethod
    def _make_bullet_levels(
        symbols_fonts: list[
            tuple[str, dict[str, str]] | str
        ],
        default_font: str = "",
    ) -> list[dict[str, Any]]:

        levels: list[dict[str, Any]] = []

        if not symbols_fonts:
            return levels

        for index in range(9):

            item = symbols_fonts[
                index % len(symbols_fonts)
            ]

            if isinstance(
                item,
                tuple,
            ):

                text = item[0]
                fonts = item[1]

            else:

                text = str(item)

                fonts = (
                    {
                        "ascii": default_font,
                        "hAnsi": default_font,
                        "cs": default_font,
                    }
                    if default_font
                    else {}
                )

            level: dict[str, Any] = {
                "level": index,
                "start": 1,
                "format": "bullet",
                "text": text,
                "alignment": "left",
                "indent": {
                    "left": 720 * (index + 1),
                    "hanging": 360,
                },
            }

            if fonts:
                level["fonts"] = fonts

            levels.append(
                level
            )

        return levels


    # --------------------------------
    # Formatted Level Generator
    # --------------------------------

    @staticmethod
    def _make_formatted_levels(
        number_format: str,
        pattern: str = "%1.",
    ) -> list[dict[str, Any]]:

        levels: list[dict[str, Any]] = []

        for index in range(9):

            if pattern == "nested":

                format_text = ".".join(
                    f"%{level + 1}"
                    for level in range(index + 1)
                ) + "."

            else:

                format_text = (
                    f"%{index + 1}."
                )

            levels.append(
                {
                    "level": index,
                    "start": 1,
                    "format": number_format,
                    "text": format_text,
                    "alignment": "left",
                    "indent": {
                        "left": 720 * (index + 1),
                        "hanging": 360,
                    },
                }
            )

        return levels


    # --------------------------------
    # Default Numbering Presets
    # --------------------------------

    @staticmethod
    def build_default_numbering() -> dict[str, Any]:

        bullet_levels = [
            (
                "•",
                {
                    "ascii": "Symbol",
                    "hAnsi": "Symbol",
                },
            ),
            (
                "◦",
                {
                    "ascii": "Courier New",
                    "hAnsi": "Courier New",
                },
            ),
            (
                "▪",
                {
                    "ascii": "Wingdings",
                    "hAnsi": "Wingdings",
                },
            ),
            "–",
            (
                "•",
                {
                    "ascii": "Symbol",
                    "hAnsi": "Symbol",
                },
            ),
            (
                "◦",
                {
                    "ascii": "Courier New",
                    "hAnsi": "Courier New",
                },
            ),
            (
                "▪",
                {
                    "ascii": "Wingdings",
                    "hAnsi": "Wingdings",
                },
            ),
            "–",
            (
                "•",
                {
                    "ascii": "Symbol",
                    "hAnsi": "Symbol",
                },
            ),
        ]

        abstract_numbering = [
            # 1. Standard Bullet
            {
                "id": "1",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        bullet_levels
                    ),
            },

            # 2. Arrow / Chevron
            {
                "id": "2",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            ">",
                            "»",
                            "›",
                            "➢",
                            "➔",
                            "→",
                        ],
                        "Segoe UI Symbol",
                    ),
            },

            # 3. Decimal Multi-Level
            {
                "id": "3",
                "levels":
                    NumberingHandler._make_formatted_levels(
                        "decimal",
                        "nested",
                    ),
            },

            # 4. Dot Bullet
            {
                "id": "4",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            ".",
                            "..",
                            "...",
                            "....",
                        ]
                    ),
            },

            # 5. Dash / Hyphen
            {
                "id": "5",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            "–",
                            "—",
                        ]
                    ),
            },

            # 6. Checkmark / Done
            {
                "id": "6",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            (
                                "ü",
                                {
                                    "ascii": "Wingdings",
                                    "hAnsi": "Wingdings",
                                },
                            ),
                            (
                                "✓",
                                {
                                    "ascii":
                                        "Segoe UI Symbol",
                                    "hAnsi":
                                        "Segoe UI Symbol",
                                },
                            ),
                            (
                                "☑",
                                {
                                    "ascii":
                                        "Segoe UI Symbol",
                                    "hAnsi":
                                        "Segoe UI Symbol",
                                },
                            ),
                        ]
                    ),
            },

            # 7. Star
            {
                "id": "7",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            "★",
                            "☆",
                            "⭐",
                            "✦",
                            "✧",
                        ],
                        "Segoe UI Symbol",
                    ),
            },

            # 8. Square
            {
                "id": "8",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            (
                                "▪",
                                {
                                    "ascii": "Wingdings",
                                    "hAnsi": "Wingdings",
                                },
                            ),
                            (
                                "▫",
                                {
                                    "ascii": "Wingdings",
                                    "hAnsi": "Wingdings",
                                },
                            ),
                            (
                                "■",
                                {
                                    "ascii":
                                        "Segoe UI Symbol",
                                    "hAnsi":
                                        "Segoe UI Symbol",
                                },
                            ),
                            (
                                "□",
                                {
                                    "ascii":
                                        "Segoe UI Symbol",
                                    "hAnsi":
                                        "Segoe UI Symbol",
                                },
                            ),
                        ]
                    ),
            },

            # 9. Diamond
            {
                "id": "9",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            "◆",
                            "◇",
                            "❖",
                            "🔹",
                            "🔸",
                        ],
                        "Segoe UI Symbol",
                    ),
            },

            # 10. Circle / Hollow
            {
                "id": "10",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            "○",
                            "◯",
                            "⭕",
                        ],
                        "Segoe UI Symbol",
                    ),
            },

            # 11. Triangle / Play
            {
                "id": "11",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            "▲",
                            "▶",
                            "►",
                            "▸",
                        ],
                        "Segoe UI Symbol",
                    ),
            },

            # 12. Hand / Pointing
            {
                "id": "12",
                "levels":
                    NumberingHandler._make_bullet_levels(
                        [
                            "👉",
                            "☞",
                            "☛",
                        ],
                        "Segoe UI Emoji",
                    ),
            },

            # 13. Lower Alphabet
            {
                "id": "13",
                "levels":
                    NumberingHandler._make_formatted_levels(
                        "lowerLetter"
                    ),
            },

            # 14. Upper Alphabet
            {
                "id": "14",
                "levels":
                    NumberingHandler._make_formatted_levels(
                        "upperLetter"
                    ),
            },

            # 15. Lower Roman
            {
                "id": "15",
                "levels":
                    NumberingHandler._make_formatted_levels(
                        "lowerRoman"
                    ),
            },

            # 16. Upper Roman
            {
                "id": "16",
                "levels":
                    NumberingHandler._make_formatted_levels(
                        "upperRoman"
                    ),
            },
        ]

        numbering_instances = [
            {
                "numId": str(index),
                "abstractNumId": str(index),
            }
            for index in range(1, 17)
        ]

        return {
            "abstractNumbering": abstract_numbering,
            "numbering": numbering_instances,
        }


    # --------------------------------
    # Custom Bullet Generator
    # --------------------------------

    @staticmethod
    def build_custom_bullet_abstract_num(
        symbol: str,
        abs_id: int | str,
    ) -> dict[str, Any]:

        font_name = "Segoe UI Emoji"

        fonts = {
            "ascii": font_name,
            "hAnsi": font_name,
            "cs": font_name,
        }

        levels: list[dict[str, Any]] = []

        for index in range(9):

            levels.append(
                {
                    "level": index,
                    "start": 1,
                    "format": "bullet",
                    "text": str(symbol),
                    "alignment": "left",
                    "indent": {
                        "left": 720 * (index + 1),
                        "hanging": 360,
                    },
                    "fonts": fonts,
                }
            )

        return {
            "id": str(abs_id),
            "levels": levels,
        }