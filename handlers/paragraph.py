"""Handler for w:p (paragraph) elements."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name
from handlers.run import RunHandler


class ParagraphHandler(BaseHandler):
    """Handles w:p paragraph element conversion to/from JSON."""

    def __init__(self, run_handler: RunHandler | None = None):
        self.run_handler = run_handler or RunHandler()

    def to_json(self, element: ET.Element, simple: bool = False) -> dict[str, Any]:
        """Convert w:p element to JSON dictionary with master-tags values as keys."""
        paragraph_properties: dict[str, Any] = {}
        p_pr = element.find(qn("w:pPr"))

        if p_pr is not None:
            # Paragraph Style (w:pStyle -> style)
            p_style = p_pr.find(qn("w:pStyle"))
            if p_style is not None:
                paragraph_properties["style"] = p_style.attrib.get(qn("w:val"), "")

            # Alignment (w:jc -> alignment)
            jc = p_pr.find(qn("w:jc"))
            if jc is not None:
                paragraph_properties["alignment"] = jc.attrib.get(qn("w:val"), "")

            # Spacing (w:spacing -> spacing)
            spacing = p_pr.find(qn("w:spacing"))
            if spacing is not None:
                sp_dict: dict[str, Any] = {}
                for attr, key in [
                    ("w:before", "before"),
                    ("w:after", "after"),
                    ("w:line", "line"),
                    ("w:lineRule", "lineRule"),
                ]:
                    val = spacing.attrib.get(qn(attr))
                    if val is not None:
                        sp_dict[key] = int(val) if val.isdigit() else val
                if sp_dict:
                    paragraph_properties["spacing"] = sp_dict

            # Indentation (w:ind -> indentation)
            ind = p_pr.find(qn("w:ind"))
            if ind is not None:
                ind_dict: dict[str, Any] = {}
                for attr, key in [
                    ("w:left", "left"),
                    ("w:right", "right"),
                    ("w:firstLine", "firstLine"),
                    ("w:hanging", "hanging"),
                ]:
                    val = ind.attrib.get(qn(attr))
                    if val is not None:
                        ind_dict[key] = int(val) if val.isdigit() else val
                if ind_dict:
                    paragraph_properties["indentation"] = ind_dict

            # Tabs (w:tabs -> tabs)
            tabs_el = p_pr.find(qn("w:tabs"))
            if tabs_el is not None:
                tab_list: list[dict[str, Any]] = []
                for tb in tabs_el.findall(qn("w:tab")):
                    t_dict: dict[str, Any] = {}
                    for k, v in tb.attrib.items():
                        t_dict[local_name(k)] = int(v) if v.isdigit() or (v.startswith("-") and v[1:].isdigit()) else v
                    tab_list.append(t_dict)
                if tab_list:
                    paragraph_properties["tabs"] = tab_list

            # Numbering Properties (w:numPr -> numbering)
            num_pr = p_pr.find(qn("w:numPr"))
            if num_pr is not None:
                num_dict: dict[str, Any] = {}
                ilvl = num_pr.find(qn("w:ilvl"))
                if ilvl is not None:
                    val = ilvl.attrib.get(qn("w:val"))
                    lvl_val = int(val) if val and val.isdigit() else val
                    num_dict["level"] = lvl_val
                num_id = num_pr.find(qn("w:numId"))
                if num_id is not None:
                    val = num_id.attrib.get(qn("w:val"))
                    id_val = int(val) if val and val.isdigit() else val
                    num_dict["id"] = id_val
                if num_dict:
                    paragraph_properties["numbering"] = num_dict

            # Keep with next (w:keepNext -> keepWithNext)
            if p_pr.find(qn("w:keepNext")) is not None:
                paragraph_properties["keepWithNext"] = True

            # Page break before (w:pageBreakBefore -> pageBreakBefore)
            if p_pr.find(qn("w:pageBreakBefore")) is not None:
                paragraph_properties["pageBreakBefore"] = True

            # Paragraph Shading (w:shd -> shading)
            p_shd = p_pr.find(qn("w:shd"))
            if p_shd is not None:
                shd_dict: dict[str, Any] = {}
                for k, v in p_shd.attrib.items():
                    shd_dict[local_name(k)] = v
                paragraph_properties["shading"] = shd_dict

            # Typography and formatting flags
            for tag_name in (
                "autoSpaceDE",
                "autoSpaceDN",
                "adjustRightInd",
                "snapToGrid",
                "bidi",
                "contextualSpacing",
                "suppressLineNumbers",
                "suppressAutoHyphens",
            ):
                el = p_pr.find(qn(f"w:{tag_name}"))
                if el is not None:
                    val = el.attrib.get(qn("w:val"))
                    if val is not None:
                        paragraph_properties[tag_name] = val not in ("0", "false", "off")
                    else:
                        paragraph_properties[tag_name] = True

            # Paragraph Mark Run Properties (w:rPr inside w:pPr)
            p_rpr = p_pr.find(qn("w:rPr"))
            if p_rpr is not None:
                r_json = self.run_handler.to_json(p_rpr, simple=False)
                if r_json.get("properties"):
                    paragraph_properties["markProperties"] = r_json["properties"]

        runs: list[dict[str, Any]] = []
        for child in element:
            if child.tag == qn("w:r"):
                runs.append(self.run_handler.to_json(child, simple=simple))
            elif child.tag == qn("w:hyperlink"):
                hl_id = child.attrib.get(qn("r:id"), "")
                anchor = child.attrib.get(qn("w:anchor"), "")
                for r_child in child.findall(qn("w:r")):
                    r_json = self.run_handler.to_json(r_child, simple=simple)
                    hl_dict: dict[str, str] = {}
                    if hl_id:
                        hl_dict["relationshipId"] = hl_id
                    if anchor:
                        hl_dict["anchor"] = anchor
                    if hl_dict:
                        r_json["hyperlink"] = hl_dict
                    runs.append(r_json)

        if simple:
            # Filter completely empty runs (no text, breaks, drawings, pictures, or structural chars)
            non_empty_runs = [
                r for r in runs
                if r.get("text") or r.get("drawings") or r.get("breaks")
                or r.get("pictures") or r.get("hyperlink")
                or r.get("hasTab") or r.get("hasCarriageReturn")
            ]

            result: dict[str, Any] = {}

            # Map paragraph properties cleanly
            if "style" in paragraph_properties:
                result["style"] = paragraph_properties["style"]
            if "alignment" in paragraph_properties:
                result["align"] = paragraph_properties["alignment"]
            if "indentation" in paragraph_properties:
                result["indent"] = paragraph_properties["indentation"]
            if "spacing" in paragraph_properties:
                result["spacing"] = paragraph_properties["spacing"]
            if "numbering" in paragraph_properties:
                result["numbering"] = paragraph_properties["numbering"]
                if "level" in paragraph_properties["numbering"]:
                    result["level"] = paragraph_properties["numbering"]["level"]
            if paragraph_properties.get("pageBreakBefore"):
                result["pageBreakBefore"] = True
            if paragraph_properties.get("shading"):
                result["shading"] = paragraph_properties["shading"]
            if "tabs" in paragraph_properties:
                result["tabs"] = paragraph_properties["tabs"]
            if "markProperties" in paragraph_properties:
                result["markProperties"] = paragraph_properties["markProperties"]

            for k in (
                "autoSpaceDE",
                "autoSpaceDN",
                "adjustRightInd",
                "snapToGrid",
                "bidi",
                "contextualSpacing",
                "suppressLineNumbers",
                "suppressAutoHyphens",
                "keepWithNext",
            ):
                if k in paragraph_properties:
                    result[k] = paragraph_properties[k]

            # If single run with text and no complex media/hyperlinks, inline it directly
            if len(non_empty_runs) == 1 and not non_empty_runs[0].get("hyperlink") and not non_empty_runs[0].get("drawings") and not non_empty_runs[0].get("pictures"):
                r0 = non_empty_runs[0]
                for k, v in r0.items():
                    if k != "type":
                        result[k] = v
            elif non_empty_runs:
                result["runs"] = non_empty_runs
            elif not non_empty_runs and not paragraph_properties:
                result["text"] = ""
        else:
            result: dict[str, Any] = {
                "type": self.tag_to_name("w:p"),
                "properties": paragraph_properties,
                "runs": runs,
            }

        # Check for paragraph-level section properties (w:sectPr -> sectionProperties)
        sect_pr = element.find(qn("w:pPr/") + qn("w:sectPr")) or element.find(qn("w:sectPr"))
        if sect_pr is not None:
            from handlers.sections import SectionsHandler
            result[self.tag_to_name("w:sectPr")] = SectionsHandler().to_json(sect_pr)

        return result

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Convert JSON paragraph representation to w:p XML element."""
        p = ET.Element(qn("w:p"))
        props = dict(data.get("paragraphProperties") or data.get("properties") or {})

        # If item type is bullet/list_item, default bullet to True
        item_type = data.get("type", "")
        if item_type in ("bullet", "list_item", "listItem"):
            if "bullet" not in props:
                props["bullet"] = True

        # Collect flat properties on data directly
        for k in (
            "alignment", "align", "indentation", "indent", "spacing",
            "style", "pStyle", "heading", "bullet", "pageBreakBefore",
            "pageBreak", "keepNext", "keepWithNext", "shading",
            "tabs", "markProperties", "numbering", "level", "ilvl",
            "list", "numbered", "number",
            "autoSpaceDE", "autoSpaceDN", "adjustRightInd", "snapToGrid",
            "bidi", "contextualSpacing", "suppressLineNumbers", "suppressAutoHyphens",
        ):
            if k in data and k not in props:
                props[k] = data[k]

        if props:
            p_pr = ET.SubElement(p, qn("w:pPr"))

            # Heading shorthand (heading: 1 -> Heading1)
            h_val = props.get("heading")
            if h_val is not None:
                ET.SubElement(p_pr, qn("w:pStyle"), {qn("w:val"): f"Heading{h_val}"})
            else:
                style_val = props.get("style") or props.get("pStyle")
                if style_val:
                    ET.SubElement(p_pr, qn("w:pStyle"), {qn("w:val"): str(style_val)})

            # Alignment (alignment or align)
            align_val = props.get("alignment") or props.get("align")
            if align_val:
                if align_val == "justify":
                    align_val = "both"
                ET.SubElement(p_pr, qn("w:jc"), {qn("w:val"): str(align_val)})

            # Spacing
            sp = props.get("spacing")
            if sp:
                if isinstance(sp, (int, str)) and str(sp).isdigit():
                    sp = {"after": int(sp)}
                if isinstance(sp, dict):
                    sp_attrs = {}
                    if "before" in sp:
                        sp_attrs[qn("w:before")] = str(sp["before"])
                    if "after" in sp:
                        sp_attrs[qn("w:after")] = str(sp["after"])
                    if "line" in sp:
                        sp_attrs[qn("w:line")] = str(sp["line"])
                    if "lineRule" in sp:
                        sp_attrs[qn("w:lineRule")] = str(sp["lineRule"])
                    if sp_attrs:
                        ET.SubElement(p_pr, qn("w:spacing"), sp_attrs)

            # Indentation
            ind = props.get("indentation") or props.get("indent")
            if ind is not None:
                if isinstance(ind, (int, str)) and str(ind).isdigit():
                    ind = {"left": int(ind)}
                if isinstance(ind, dict):
                    ind_attrs = {}
                    if "left" in ind:
                        ind_attrs[qn("w:left")] = str(ind["left"])
                    if "right" in ind:
                        ind_attrs[qn("w:right")] = str(ind["right"])
                    if "firstLine" in ind:
                        ind_attrs[qn("w:firstLine")] = str(ind["firstLine"])
                    if "hanging" in ind:
                        ind_attrs[qn("w:hanging")] = str(ind["hanging"])
                    if ind_attrs:
                        ET.SubElement(p_pr, qn("w:ind"), ind_attrs)

            # Tabs
            if props.get("tabs"):
                tabs_el = ET.SubElement(p_pr, qn("w:tabs"))
                for t_data in props["tabs"]:
                    t_attrs = {qn(f"w:{k}"): str(v) for k, v in t_data.items()}
                    ET.SubElement(tabs_el, qn("w:tab"), t_attrs)

            # Numbering properties, bullet shorthand, or list shorthand
            num_data = props.get("numberingProperties") or props.get("numbering")
            list_data = props.get("list")
            bullet_data = props.get("bullet")

            if num_data and isinstance(num_data, dict):
                ilvl_val = num_data.get("indentationLevel") if num_data.get("indentationLevel") is not None else num_data.get("level", props.get("level", props.get("ilvl", 0)))
                num_id_val = num_data.get("numberingId") if num_data.get("numberingId") is not None else num_data.get("id")
                if num_id_val is None:
                    fmt = str(num_data.get("format") or num_data.get("type") or "").strip().lower()
                    if fmt in (">", "arrow", "chevron"):
                        num_id_val = 2
                    elif fmt in ("decimal", "number", "numeric"):
                        num_id_val = 3
                    elif fmt in (".", "dot"):
                        num_id_val = 4
                    elif fmt in ("-", "dash", "hyphen"):
                        num_id_val = 5
                    else:
                        num_id_val = 1
                num_pr = ET.SubElement(p_pr, qn("w:numPr"))
                ET.SubElement(num_pr, qn("w:ilvl"), {qn("w:val"): str(ilvl_val)})
                ET.SubElement(num_pr, qn("w:numId"), {qn("w:val"): str(num_id_val)})
            elif list_data:
                if isinstance(list_data, dict):
                    ilvl_val = list_data.get("level", props.get("level", props.get("ilvl", 0)))
                    l_type = str(list_data.get("type") or list_data.get("format") or list_data.get("bullet") or "").strip().lower()
                else:
                    ilvl_val = props.get("level", props.get("ilvl", 0))
                    l_type = str(list_data).strip().lower() if not isinstance(list_data, bool) else ""

                if l_type in (">", "arrow", "chevron", ">>", "›", "»", "➢", "➔", "→"):
                    num_id_val = 2
                elif l_type in ("decimal", "number", "numeric", "1."):
                    num_id_val = 3
                elif l_type in (".", "dot"):
                    num_id_val = 4
                elif l_type in ("-", "dash", "hyphen", "–", "—"):
                    num_id_val = 5
                else:
                    num_id_val = 1

                num_pr = ET.SubElement(p_pr, qn("w:numPr"))
                ET.SubElement(num_pr, qn("w:ilvl"), {qn("w:val"): str(ilvl_val)})
                ET.SubElement(num_pr, qn("w:numId"), {qn("w:val"): str(num_id_val)})
            elif bullet_data is not None and bullet_data is not False:
                if isinstance(bullet_data, dict):
                    ilvl_val = bullet_data.get("level", props.get("level", props.get("ilvl", 0)))
                    b_type = str(bullet_data.get("type") or bullet_data.get("format") or bullet_data.get("style") or "").strip().lower()
                else:
                    ilvl_val = props.get("level", props.get("ilvl", 0))
                    b_type = str(bullet_data).strip().lower() if not isinstance(bullet_data, bool) else ""

                if b_type in (">", "arrow", "chevron", ">>", "›", "»", "➢", "➔", "→"):
                    num_id_val = 2
                elif b_type in ("decimal", "number", "numeric", "1."):
                    num_id_val = 3
                elif b_type in (".", "dot"):
                    num_id_val = 4
                elif b_type in ("-", "dash", "hyphen", "–", "—"):
                    num_id_val = 5
                else:
                    num_id_val = 1

                num_pr = ET.SubElement(p_pr, qn("w:numPr"))
                ET.SubElement(num_pr, qn("w:ilvl"), {qn("w:val"): str(ilvl_val)})
                ET.SubElement(num_pr, qn("w:numId"), {qn("w:val"): str(num_id_val)})
            elif props.get("numbered") or props.get("number"):
                ilvl_val = props.get("level", props.get("ilvl", 0))
                num_id_val = 3
                num_pr = ET.SubElement(p_pr, qn("w:numPr"))
                ET.SubElement(num_pr, qn("w:ilvl"), {qn("w:val"): str(ilvl_val)})
                ET.SubElement(num_pr, qn("w:numId"), {qn("w:val"): str(num_id_val)})

            if props.get("keepWithNext") or props.get("keepNext"):
                ET.SubElement(p_pr, qn("w:keepNext"))

            if props.get("pageBreakBefore") or props.get("pageBreak"):
                ET.SubElement(p_pr, qn("w:pageBreakBefore"))

            # Typography and formatting flags
            for tag_name in (
                "autoSpaceDE",
                "autoSpaceDN",
                "adjustRightInd",
                "snapToGrid",
                "bidi",
                "contextualSpacing",
            ):
                if tag_name in props:
                    val = props[tag_name]
                    if isinstance(val, bool):
                        ET.SubElement(p_pr, qn(f"w:{tag_name}"), {qn("w:val"): "1" if val else "0"})
                    elif val is not None:
                        ET.SubElement(p_pr, qn(f"w:{tag_name}"), {qn("w:val"): str(val)})

            if props.get("suppressLineNumbers"):
                ET.SubElement(p_pr, qn("w:suppressLineNumbers"))

            if props.get("suppressAutoHyphens"):
                ET.SubElement(p_pr, qn("w:suppressAutoHyphens"))

            # Shading
            if props.get("shading"):
                shd = props["shading"]
                if isinstance(shd, str):
                    shd_attrs = {qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): shd.lstrip("#")}
                else:
                    shd_attrs = {qn(f"w:{k}"): str(v) for k, v in shd.items()}
                ET.SubElement(p_pr, qn("w:shd"), shd_attrs)

            # Paragraph Mark Run Properties (w:rPr)
            if props.get("markProperties"):
                dummy_run = {"runProperties": props["markProperties"]}
                r_elem = self.run_handler.to_xml(dummy_run)
                r_pr_elem = r_elem.find(qn("w:rPr"))
                if r_pr_elem is not None:
                    p_pr.append(r_pr_elem)

            # Paragraph-level Section Properties (w:sectPr)
            sect_data = data.get("sectionProperties") or data.get(self.tag_to_name("w:sectPr"))
            if sect_data:
                from handlers.sections import SectionsHandler
                p_pr.append(SectionsHandler().to_xml(sect_data))

            # Apply schema ordering
            self.sort_children_by_schema(p_pr, "pPr")
        else:
            sect_data = data.get("sectionProperties") or data.get(self.tag_to_name("w:sectPr"))
            if sect_data:
                from handlers.sections import SectionsHandler
                p_pr = ET.SubElement(p, qn("w:pPr"))
                p_pr.append(SectionsHandler().to_xml(sect_data))

        # Runs handling (synthesize run from text if runs array is not provided)
        raw_runs = data.get("runs")
        if raw_runs is None and "text" in data:
            text_val = data["text"]
            # Check if there are any run-level style properties
            run_style_keys = (
                "bold", "b", "italic", "i", "underline", "u", "strike", "strikethrough",
                "color", "fontSize", "size", "sz", "fontFamily", "font", "rFonts",
                "highlight", "shading", "subscript", "superscript"
            )
            run_content_keys = ("breaks", "hasTab", "hasCarriageReturn", "drawings", "pictures")
            has_style = any(k in data for k in run_style_keys)
            has_content = any(k in data for k in run_content_keys)
            if text_val or has_style or has_content:
                # Only synthesize a run when there's actual text, explicit styling, or run content
                run_item = {"text": text_val}
                for k in run_style_keys:
                    if k in data:
                        run_item[k] = data[k]
                for k in run_content_keys:
                    if k in data:
                        run_item[k] = data[k]
                raw_runs = [run_item]
            else:
                raw_runs = []
        elif raw_runs is None:
            raw_runs = []

        # Add child runs (grouping runs sharing a hyperlink)
        current_hl_key = None
        current_hl_elem = None

        for run_data in raw_runs:
            if isinstance(run_data, str):
                run_data = {"text": run_data}

            hl = run_data.get("hyperlink")
            if hl:
                hl_id = hl.get("relationshipId", "")
                anchor = hl.get("anchor", "")
                hl_key = (hl_id, anchor)
                if current_hl_key != hl_key or current_hl_elem is None:
                    current_hl_key = hl_key
                    attrs = {}
                    if hl_id:
                        attrs[qn("r:id")] = hl_id
                    if anchor:
                        attrs[qn("w:anchor")] = anchor
                    current_hl_elem = ET.SubElement(p, qn("w:hyperlink"), attrs)
                current_hl_elem.append(self.run_handler.to_xml(run_data))
            else:
                current_hl_key = None
                current_hl_elem = None
                p.append(self.run_handler.to_xml(run_data))

        return p
