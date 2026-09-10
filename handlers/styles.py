from typing import Any
import xml.etree.ElementTree as ET

from handlers.base import BaseHandler, qn, local_name


# --------------------------------
# Styles Handler
# --------------------------------

class StylesHandler(BaseHandler):

    # --------------------------------
    # JSON Conversion
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> dict[str, Any]:

        from handlers.run import RunHandler
        from handlers.paragraph import ParagraphHandler

        run_handler = RunHandler()
        paragraph_handler = ParagraphHandler()

        styles_map: dict[str, Any] = {}
        styles_list: list[dict[str, Any]] = []
        defaults: dict[str, Any] = {}
        latent_styles_data: dict[str, Any] = {}

        # --------------------------------
        # Document Defaults
        # --------------------------------

        doc_defaults = element.find(qn("w:docDefaults"))

        if doc_defaults is not None:
            run_default = doc_defaults.find(
                qn("w:rPrDefault/") + qn("w:rPr")
            )

            if run_default is None:
                run_default = doc_defaults.find(
                    qn("w:rPrDefault")
                )

            if run_default is not None:
                run_json = run_handler.to_json(
                    run_default,
                    simple=True,
                )

                for key, value in run_json.items():
                    if (
                        key not in ("text", "type")
                        and value not in (None, "", {})
                    ):
                        defaults[key] = value

            paragraph_default = doc_defaults.find(
                qn("w:pPrDefault/") + qn("w:pPr")
            )

            if paragraph_default is None:
                paragraph_default = doc_defaults.find(
                    qn("w:pPrDefault")
                )

            if paragraph_default is not None:
                paragraph_json = paragraph_handler.to_json(
                    paragraph_default,
                    simple=True,
                )

                for key, value in paragraph_json.items():
                    if (
                        key not in (
                            "text",
                            "type",
                            "runs",
                            "style",
                        )
                        and value not in (None, "", {})
                    ):
                        defaults[key] = value

            if doc_defaults.find(qn("w:pPrDefault")) is not None:
                defaults["hasPPrDefault"] = True

            if doc_defaults.find(qn("w:rPrDefault")) is not None:
                defaults["hasRPrDefault"] = True

        # --------------------------------
        # Latent Styles
        # --------------------------------

        latent_styles = element.find(
            qn("w:latentStyles")
        )

        if latent_styles is not None:
            latent_data = {
                local_name(key): value
                for key, value in latent_styles.attrib.items()
            }

            exceptions: list[dict[str, Any]] = []

            for exception in latent_styles.findall(
                qn("w:lsdException")
            ):
                exceptions.append(
                    {
                        local_name(key): value
                        for key, value in exception.attrib.items()
                    }
                )

            if exceptions:
                latent_data["exceptions"] = exceptions

            latent_styles_data = latent_data

        # --------------------------------
        # Style Elements
        # --------------------------------

        for style_element in element.findall(qn("w:style")):
            style_id = style_element.attrib.get(
                qn("w:styleId"),
                "",
            )

            style_type = style_element.attrib.get(
                qn("w:type"),
                "paragraph",
            )

            default_value = style_element.attrib.get(
                qn("w:default")
            )

            custom_value = style_element.attrib.get(
                qn("w:customStyle")
            )

            entry: dict[str, Any] = {
                "id": style_id,
            }

            # --------------------------------
            # Basic Style Attributes
            # --------------------------------

            if style_type != "paragraph" or not simple:
                entry["type"] = style_type

            if default_value in ("1", "true"):
                entry["default"] = True

            if custom_value in ("1", "true"):
                entry["customStyle"] = True

            # --------------------------------
            # Style Name
            # --------------------------------

            name_element = style_element.find(
                qn("w:name")
            )

            if name_element is not None:
                entry["name"] = name_element.attrib.get(
                    qn("w:val"),
                    "",
                )

            # --------------------------------
            # Style Aliases
            # --------------------------------

            aliases_element = style_element.find(
                qn("w:aliases")
            )

            if aliases_element is not None:
                entry["aliases"] = aliases_element.attrib.get(
                    qn("w:val"),
                    "",
                )

            # --------------------------------
            # Based On
            # --------------------------------

            based_on = style_element.find(
                qn("w:basedOn")
            )

            if based_on is not None:
                entry["basedOn"] = based_on.attrib.get(
                    qn("w:val"),
                    "",
                )

            # --------------------------------
            # Next Style
            # --------------------------------

            next_style = style_element.find(
                qn("w:next")
            )

            if next_style is not None:
                entry["next"] = next_style.attrib.get(
                    qn("w:val"),
                    "",
                )

            # --------------------------------
            # Linked Style
            # --------------------------------

            linked_style = style_element.find(
                qn("w:link")
            )

            if linked_style is not None:
                entry["link"] = linked_style.attrib.get(
                    qn("w:val"),
                    "",
                )

            # --------------------------------
            # Style Flags
            # --------------------------------

            if style_element.find(
                qn("w:autoRedefine")
            ) is not None:
                entry["autoRedefine"] = True

            if style_element.find(
                qn("w:hidden")
            ) is not None:
                entry["hidden"] = True

            # --------------------------------
            # UI Priority
            # --------------------------------

            ui_priority = style_element.find(
                qn("w:uiPriority")
            )

            if ui_priority is not None:
                value = ui_priority.attrib.get(
                    qn("w:val"),
                    "",
                )

                entry["uiPriority"] = (
                    int(value)
                    if value.isdigit()
                    else value
                )

            # --------------------------------
            # Additional Style Flags
            # --------------------------------

            if style_element.find(
                qn("w:semiHidden")
            ) is not None:
                entry["semiHidden"] = True

            if style_element.find(
                qn("w:unhideWhenUsed")
            ) is not None:
                entry["unhideWhenUsed"] = True

            if style_element.find(
                qn("w:locked")
            ) is not None:
                entry["locked"] = True

            if style_element.find(
                qn("w:personal")
            ) is not None:
                entry["personal"] = True

            if style_element.find(
                qn("w:personalCompose")
            ) is not None:
                entry["personalCompose"] = True

            if style_element.find(
                qn("w:personalReply")
            ) is not None:
                entry["personalReply"] = True

            # --------------------------------
            # Run Properties
            # --------------------------------

            run_properties = style_element.find(
                qn("w:rPr")
            )

            if run_properties is not None:
                entry["hasRunProperties"] = True

                run_json = run_handler.to_json(
                    run_properties,
                    simple=True,
                )

                for key, value in run_json.items():
                    if (
                        key not in ("text", "type")
                        and value not in (None, "", {})
                    ):
                        entry[key] = value

            # --------------------------------
            # Paragraph Properties
            # --------------------------------

            paragraph_properties = style_element.find(
                qn("w:pPr")
            )

            if paragraph_properties is not None:
                entry["hasParagraphProperties"] = True

                paragraph_json = paragraph_handler.to_json(
                    paragraph_properties,
                    simple=True,
                )

                for key, value in paragraph_json.items():
                    if (
                        key not in (
                            "text",
                            "type",
                            "runs",
                            "style",
                        )
                        and value not in (None, "", {})
                    ):
                        entry[key] = value

            # --------------------------------
            # Table Properties
            # --------------------------------

            table_properties = style_element.find(
                qn("w:tblPr")
            )

            if table_properties is not None:
                table_data: dict[str, Any] = {}

                for child in table_properties:
                    tag_name = local_name(child.tag)

                    if len(child) > 0:
                        table_data[tag_name] = {
                            local_name(grandchild.tag): {
                                local_name(key): value
                                for key, value
                                in grandchild.attrib.items()
                            }
                            for grandchild in child
                        }
                    else:
                        table_data[tag_name] = {
                            local_name(key): value
                            for key, value
                            in child.attrib.items()
                        }

                if table_data:
                    entry["tableProperties"] = table_data

            # --------------------------------
            # Row Properties
            # --------------------------------

            row_properties = style_element.find(
                qn("w:trPr")
            )

            if row_properties is not None:
                row_data: dict[str, Any] = {}

                for child in row_properties:
                    tag_name = local_name(child.tag)

                    if len(child) > 0:
                        row_data[tag_name] = {
                            local_name(grandchild.tag): {
                                local_name(key): value
                                for key, value
                                in grandchild.attrib.items()
                            }
                            for grandchild in child
                        }
                    else:
                        row_data[tag_name] = {
                            local_name(key): value
                            for key, value
                            in child.attrib.items()
                        }

                if row_data:
                    entry["rowProperties"] = row_data

            # --------------------------------
            # Cell Properties
            # --------------------------------

            cell_properties = style_element.find(
                qn("w:tcPr")
            )

            if cell_properties is not None:
                cell_data: dict[str, Any] = {}

                for child in cell_properties:
                    tag_name = local_name(child.tag)

                    if len(child) > 0:
                        cell_data[tag_name] = {
                            local_name(grandchild.tag): {
                                local_name(key): value
                                for key, value
                                in grandchild.attrib.items()
                            }
                            for grandchild in child
                        }
                    else:
                        cell_data[tag_name] = {
                            local_name(key): value
                            for key, value
                            in child.attrib.items()
                        }

                if cell_data:
                    entry["cellProperties"] = cell_data

            # --------------------------------
            # Table Style Properties
            # --------------------------------

            table_style_properties: list[
                dict[str, Any]
            ] = []

            for table_style_property in style_element.findall(
                qn("w:tblStylePr")
            ):
                property_type = table_style_property.attrib.get(
                    qn("w:type"),
                    "",
                )

                property_entry: dict[str, Any] = {
                    "type": property_type,
                }

                # Run properties
                run_properties = table_style_property.find(
                    qn("w:rPr")
                )

                if run_properties is not None:
                    run_json = run_handler.to_json(
                        run_properties,
                        simple=True,
                    )

                    property_entry["runProperties"] = {
                        key: value
                        for key, value in run_json.items()
                        if (
                            key not in ("text", "type")
                            and value not in (None, "", {})
                        )
                    }

                # Paragraph properties
                paragraph_properties = table_style_property.find(
                    qn("w:pPr")
                )

                if paragraph_properties is not None:
                    paragraph_json = paragraph_handler.to_json(
                        paragraph_properties,
                        simple=True,
                    )

                    property_entry["paragraphProperties"] = {
                        key: value
                        for key, value in paragraph_json.items()
                        if (
                            key not in (
                                "text",
                                "type",
                                "runs",
                                "style",
                            )
                            and value not in (None, "", {})
                        )
                    }

                # Table properties
                table_properties = table_style_property.find(
                    qn("w:tblPr")
                )

                if table_properties is not None:
                    property_entry["tableProperties"] = {
                        local_name(child.tag): {
                            local_name(key): value
                            for key, value
                            in child.attrib.items()
                        }
                        for child in table_properties
                    }

                # Row properties
                row_properties = table_style_property.find(
                    qn("w:trPr")
                )

                if row_properties is not None:
                    property_entry["rowProperties"] = {
                        local_name(child.tag): {
                            local_name(key): value
                            for key, value
                            in child.attrib.items()
                        }
                        for child in row_properties
                    }

                # Cell properties
                cell_properties = table_style_property.find(
                    qn("w:tcPr")
                )

                if cell_properties is not None:
                    property_entry["cellProperties"] = {
                        local_name(child.tag): {
                            local_name(key): value
                            for key, value
                            in child.attrib.items()
                        }
                        for child in cell_properties
                    }

                table_style_properties.append(
                    property_entry
                )

            if table_style_properties:
                entry["tableStyleProperties"] = (
                    table_style_properties
                )

            # --------------------------------
            # Primary Style
            # --------------------------------

            if style_element.find(
                qn("w:qFormat")
            ) is not None:
                entry["primaryStyle"] = True

            # --------------------------------
            # Store Style
            # --------------------------------

            styles_map[style_id] = entry
            styles_list.append(entry)

        # --------------------------------
        # Build Result
        # --------------------------------

        result: dict[str, Any] = {}

        if defaults:
            result["defaults"] = defaults

        if latent_styles_data:
            result["latentStyles"] = latent_styles_data

        result["styles"] = (
            styles_map
            if simple
            else styles_list
        )

        return result

    # --------------------------------
    # XML Conversion
    # --------------------------------

    def to_xml(
        self,
        data: dict[str, Any],
    ) -> ET.Element:

        from handlers.run import RunHandler
        from handlers.paragraph import ParagraphHandler

        run_handler = RunHandler()
        paragraph_handler = ParagraphHandler()

        root = ET.Element(qn("w:styles"))

        # --------------------------------
        # Document Defaults
        # --------------------------------

        defaults_data = (
            data.get("defaults")
            or data.get("docDefaults")
            if isinstance(data, dict)
            else None
        )

        if (
            defaults_data
            and isinstance(defaults_data, dict)
        ):
            doc_defaults = ET.SubElement(
                root,
                qn("w:docDefaults"),
            )

            # Run defaults
            run_dummy = run_handler.to_xml(
                defaults_data
            )

            run_properties = run_dummy.find(
                qn("w:rPr")
            )

            has_run_properties = (
                run_properties is not None
                and len(run_properties) > 0
            )

            if (
                has_run_properties
                or defaults_data.get("hasRPrDefault")
                or "font" in defaults_data
                or "size" in defaults_data
                or "rFonts" in defaults_data
            ):
                run_default = ET.SubElement(
                    doc_defaults,
                    qn("w:rPrDefault"),
                )

                if has_run_properties:
                    run_default.append(
                        run_properties
                    )

            # Paragraph defaults
            paragraph_dummy = paragraph_handler.to_xml(
                defaults_data
            )

            paragraph_properties = paragraph_dummy.find(
                qn("w:pPr")
            )

            has_paragraph_properties = (
                paragraph_properties is not None
                and len(paragraph_properties) > 0
            )

            if (
                has_paragraph_properties
                or defaults_data.get("hasPPrDefault")
                or any(
                    key in defaults_data
                    for key in (
                        "spacing",
                        "indent",
                        "align",
                        "alignment",
                        "widowControl",
                        "suppressAutoHyphens",
                    )
                )
            ):
                paragraph_default = ET.SubElement(
                    doc_defaults,
                    qn("w:pPrDefault"),
                )

                if has_paragraph_properties:
                    paragraph_default.append(
                        paragraph_properties
                    )

        # --------------------------------
        # Latent Styles
        # --------------------------------

        latent_data = (
            data.get("latentStyles")
            if isinstance(data, dict)
            else None
        )

        if (
            latent_data
            and isinstance(latent_data, dict)
        ):
            latent_attributes = {
                qn(f"w:{key}"): str(value)
                for key, value in latent_data.items()
                if key != "exceptions"
            }

            latent_element = ET.SubElement(
                root,
                qn("w:latentStyles"),
                latent_attributes,
            )

            for exception in latent_data.get(
                "exceptions",
                [],
            ):
                exception_attributes = {
                    qn(f"w:{key}"): str(value)
                    for key, value in exception.items()
                }

                ET.SubElement(
                    latent_element,
                    qn("w:lsdException"),
                    exception_attributes,
                )

        # --------------------------------
        # Extract Styles
        # --------------------------------

        raw_styles = (
            data.get("styles", data)
            if isinstance(data, dict)
            else data
        )

        styles_list: list[
            tuple[str, dict[str, Any]]
        ] = []

        if isinstance(raw_styles, dict):
            for style_id, style_value in raw_styles.items():

                if style_id in (
                    "defaults",
                    "docDefaults",
                    "latentStyles",
                    "latentStylesXml",
                    "docDefaultsXml",
                ):
                    continue

                if isinstance(style_value, dict):
                    styles_list.append(
                        (
                            style_id,
                            style_value,
                        )
                    )

        elif isinstance(raw_styles, list):
            for item in raw_styles:
                if isinstance(item, dict):
                    style_id = item.get(
                        "id",
                        item.get(
                            "name",
                            "CustomStyle",
                        ),
                    )

                    styles_list.append(
                        (
                            style_id,
                            item,
                        )
                    )

        # --------------------------------
        # Build Styles
        # --------------------------------

        for style_id, style_data in styles_list:

            style_type = str(
                style_data.get(
                    "type",
                    "paragraph",
                )
            )

            style_attributes = {
                qn("w:type"): style_type,
                qn("w:styleId"): str(
                    style_data.get(
                        "id",
                        style_id,
                    )
                ),
            }

            if style_data.get("default"):
                style_attributes[
                    qn("w:default")
                ] = "1"

            if style_data.get("customStyle"):
                style_attributes[
                    qn("w:customStyle")
                ] = "1"

            style_element = ET.SubElement(
                root,
                qn("w:style"),
                style_attributes,
            )

            # --------------------------------
            # Style Name
            # --------------------------------

            name_value = style_data.get(
                "name",
                style_id,
            )

            if name_value:
                ET.SubElement(
                    style_element,
                    qn("w:name"),
                    {
                        qn("w:val"): str(name_value),
                    },
                )

            # --------------------------------
            # Aliases
            # --------------------------------

            if style_data.get("aliases"):
                ET.SubElement(
                    style_element,
                    qn("w:aliases"),
                    {
                        qn("w:val"): str(
                            style_data["aliases"]
                        ),
                    },
                )

            # --------------------------------
            # Based On
            # --------------------------------

            if style_data.get("basedOn"):
                ET.SubElement(
                    style_element,
                    qn("w:basedOn"),
                    {
                        qn("w:val"): str(
                            style_data["basedOn"]
                        ),
                    },
                )

            # --------------------------------
            # Next Style
            # --------------------------------

            if style_data.get("next"):
                ET.SubElement(
                    style_element,
                    qn("w:next"),
                    {
                        qn("w:val"): str(
                            style_data["next"]
                        ),
                    },
                )

            # --------------------------------
            # Linked Style
            # --------------------------------

            if style_data.get("link"):
                ET.SubElement(
                    style_element,
                    qn("w:link"),
                    {
                        qn("w:val"): str(
                            style_data["link"]
                        ),
                    },
                )

            # --------------------------------
            # Auto Redefine
            # --------------------------------

            if style_data.get("autoRedefine"):
                ET.SubElement(
                    style_element,
                    qn("w:autoRedefine"),
                )

            # --------------------------------
            # Hidden
            # --------------------------------

            if style_data.get("hidden"):
                ET.SubElement(
                    style_element,
                    qn("w:hidden"),
                )

            # --------------------------------
            # UI Priority
            # --------------------------------

            if "uiPriority" in style_data:
                ET.SubElement(
                    style_element,
                    qn("w:uiPriority"),
                    {
                        qn("w:val"): str(
                            style_data["uiPriority"]
                        ),
                    },
                )

            # --------------------------------
            # Semi Hidden
            # --------------------------------

            if style_data.get("semiHidden"):
                ET.SubElement(
                    style_element,
                    qn("w:semiHidden"),
                )

            # --------------------------------
            # Unhide When Used
            # --------------------------------

            if style_data.get("unhideWhenUsed"):
                ET.SubElement(
                    style_element,
                    qn("w:unhideWhenUsed"),
                )

            # --------------------------------
            # Primary Style
            # --------------------------------

            if (
                style_data.get("primaryStyle")
                or style_data.get("qFormat")
            ):
                ET.SubElement(
                    style_element,
                    qn("w:qFormat"),
                )

            # --------------------------------
            # Locked
            # --------------------------------

            if style_data.get("locked"):
                ET.SubElement(
                    style_element,
                    qn("w:locked"),
                )

            # --------------------------------
            # Personal
            # --------------------------------

            if style_data.get("personal"):
                ET.SubElement(
                    style_element,
                    qn("w:personal"),
                )

            # --------------------------------
            # Personal Compose
            # --------------------------------

            if style_data.get("personalCompose"):
                ET.SubElement(
                    style_element,
                    qn("w:personalCompose"),
                )

            # --------------------------------
            # Personal Reply
            # --------------------------------

            if style_data.get("personalReply"):
                ET.SubElement(
                    style_element,
                    qn("w:personalReply"),
                )

            # --------------------------------
            # Paragraph Properties
            # --------------------------------

            if style_type != "character":
                paragraph_dummy = paragraph_handler.to_xml(
                    style_data
                )

                paragraph_properties = (
                    paragraph_dummy.find(
                        qn("w:pPr")
                    )
                )

                if paragraph_properties is not None:
                    paragraph_style = (
                        paragraph_properties.find(
                            qn("w:pStyle")
                        )
                    )

                    if paragraph_style is not None:
                        paragraph_properties.remove(
                            paragraph_style
                        )

                    if (
                        len(paragraph_properties) > 0
                        or style_data.get(
                            "hasParagraphProperties"
                        )
                    ):
                        style_element.append(
                            paragraph_properties
                        )

                elif style_data.get(
                    "hasParagraphProperties"
                ):
                    ET.SubElement(
                        style_element,
                        qn("w:pPr"),
                    )

            # --------------------------------
            # Run Properties
            # --------------------------------

            run_dummy = run_handler.to_xml(
                style_data
            )

            run_properties = run_dummy.find(
                qn("w:rPr")
            )

            if run_properties is not None:
                run_style = run_properties.find(
                    qn("w:rStyle")
                )

                if run_style is not None:
                    run_properties.remove(
                        run_style
                    )

                if (
                    len(run_properties) > 0
                    or style_data.get(
                        "hasRunProperties"
                    )
                ):
                    style_element.append(
                        run_properties
                    )

            elif style_data.get(
                "hasRunProperties"
            ):
                ET.SubElement(
                    style_element,
                    qn("w:rPr"),
                )

            # --------------------------------
            # Table Properties
            # --------------------------------

            if (
                "tableProperties" in style_data
                and isinstance(
                    style_data["tableProperties"],
                    dict,
                )
            ):
                table_properties = ET.SubElement(
                    style_element,
                    qn("w:tblPr"),
                )

                for tag_name, attributes in (
                    style_data[
                        "tableProperties"
                    ].items()
                ):
                    child = ET.SubElement(
                        table_properties,
                        qn(f"w:{tag_name}"),
                    )

                    if isinstance(attributes, dict):
                        for key, value in attributes.items():

                            if isinstance(value, dict):
                                nested = ET.SubElement(
                                    child,
                                    qn(f"w:{key}"),
                                )

                                for nested_key, nested_value in (
                                    value.items()
                                ):
                                    nested.attrib[
                                        qn(
                                            f"w:{nested_key}"
                                        )
                                    ] = str(nested_value)

                            else:
                                child.attrib[
                                    qn(f"w:{key}")
                                ] = str(value)

            # --------------------------------
            # Row Properties
            # --------------------------------

            if (
                "rowProperties" in style_data
                and isinstance(
                    style_data["rowProperties"],
                    dict,
                )
            ):
                row_properties = ET.SubElement(
                    style_element,
                    qn("w:trPr"),
                )

                for tag_name, attributes in (
                    style_data[
                        "rowProperties"
                    ].items()
                ):
                    child = ET.SubElement(
                        row_properties,
                        qn(f"w:{tag_name}"),
                    )

                    if isinstance(attributes, dict):
                        for key, value in attributes.items():

                            if isinstance(value, dict):
                                nested = ET.SubElement(
                                    child,
                                    qn(f"w:{key}"),
                                )

                                for nested_key, nested_value in (
                                    value.items()
                                ):
                                    nested.attrib[
                                        qn(
                                            f"w:{nested_key}"
                                        )
                                    ] = str(nested_value)

                            else:
                                child.attrib[
                                    qn(f"w:{key}")
                                ] = str(value)

            # --------------------------------
            # Cell Properties
            # --------------------------------

            if (
                "cellProperties" in style_data
                and isinstance(
                    style_data["cellProperties"],
                    dict,
                )
            ):
                cell_properties = ET.SubElement(
                    style_element,
                    qn("w:tcPr"),
                )

                for tag_name, attributes in (
                    style_data[
                        "cellProperties"
                    ].items()
                ):
                    child = ET.SubElement(
                        cell_properties,
                        qn(f"w:{tag_name}"),
                    )

                    if isinstance(attributes, dict):
                        for key, value in attributes.items():

                            if isinstance(value, dict):
                                nested = ET.SubElement(
                                    child,
                                    qn(f"w:{key}"),
                                )

                                for nested_key, nested_value in (
                                    value.items()
                                ):
                                    nested.attrib[
                                        qn(
                                            f"w:{nested_key}"
                                        )
                                    ] = str(nested_value)

                            else:
                                child.attrib[
                                    qn(f"w:{key}")
                                ] = str(value)

            # --------------------------------
            # Table Style Properties
            # --------------------------------

            table_style_properties = style_data.get(
                "tableStyleProperties"
            )

            if isinstance(
                table_style_properties,
                list,
            ):
                for table_style_data in table_style_properties:

                    if not isinstance(
                        table_style_data,
                        dict,
                    ):
                        continue

                    table_style_element = ET.SubElement(
                        style_element,
                        qn("w:tblStylePr"),
                        {
                            qn("w:type"): str(
                                table_style_data.get(
                                    "type",
                                    "",
                                )
                            )
                        },
                    )

                    # Paragraph properties
                    if "paragraphProperties" in table_style_data:
                        paragraph_dummy = paragraph_handler.to_xml(
                            table_style_data[
                                "paragraphProperties"
                            ]
                        )

                        paragraph_properties = (
                            paragraph_dummy.find(
                                qn("w:pPr")
                            )
                        )

                        if paragraph_properties is not None:
                            table_style_element.append(
                                paragraph_properties
                            )

                    # Run properties
                    if "runProperties" in table_style_data:
                        run_dummy = run_handler.to_xml(
                            table_style_data[
                                "runProperties"
                            ]
                        )

                        run_properties = run_dummy.find(
                            qn("w:rPr")
                        )

                        if run_properties is not None:
                            table_style_element.append(
                                run_properties
                            )

                    # Table properties
                    table_properties = (
                        table_style_data.get(
                            "tableProperties"
                        )
                    )

                    if isinstance(
                        table_properties,
                        dict,
                    ):
                        table_properties_element = ET.SubElement(
                            table_style_element,
                            qn("w:tblPr"),
                        )

                        for tag_name, attributes in (
                            table_properties.items()
                        ):
                            child = ET.SubElement(
                                table_properties_element,
                                qn(f"w:{tag_name}"),
                            )

                            if isinstance(
                                attributes,
                                dict,
                            ):
                                for key, value in (
                                    attributes.items()
                                ):
                                    child.attrib[
                                        qn(f"w:{key}")
                                    ] = str(value)

                    # Row properties
                    row_properties = (
                        table_style_data.get(
                            "rowProperties"
                        )
                    )

                    if isinstance(
                        row_properties,
                        dict,
                    ):
                        row_properties_element = ET.SubElement(
                            table_style_element,
                            qn("w:trPr"),
                        )

                        for tag_name, attributes in (
                            row_properties.items()
                        ):
                            child = ET.SubElement(
                                row_properties_element,
                                qn(f"w:{tag_name}"),
                            )

                            if isinstance(
                                attributes,
                                dict,
                            ):
                                for key, value in (
                                    attributes.items()
                                ):
                                    child.attrib[
                                        qn(f"w:{key}")
                                    ] = str(value)

                    # Cell properties
                    cell_properties = (
                        table_style_data.get(
                            "cellProperties"
                        )
                    )

                    if isinstance(
                        cell_properties,
                        dict,
                    ):
                        cell_properties_element = ET.SubElement(
                            table_style_element,
                            qn("w:tcPr"),
                        )

                        for tag_name, attributes in (
                            cell_properties.items()
                        ):
                            child = ET.SubElement(
                                cell_properties_element,
                                qn(f"w:{tag_name}"),
                            )

                            if isinstance(
                                attributes,
                                dict,
                            ):
                                for key, value in (
                                    attributes.items()
                                ):
                                    child.attrib[
                                        qn(f"w:{key}")
                                    ] = str(value)

        return root