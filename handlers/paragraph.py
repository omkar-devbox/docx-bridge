"""Handler for w:p (paragraph) elements."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, local_name
from handlers.run import RunHandler


class ParagraphHandler(BaseHandler):
    """Handles w:p paragraph element conversion to/from JSON."""

    def __init__(self, run_handler: RunHandler | None = None):
        self.run_handler = run_handler or RunHandler()

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert w:p element to JSON dictionary with master-tags values as keys."""
        paragraph_properties: dict[str, Any] = {}
        p_pr = element.find(qn("w:pPr"))

        if p_pr is not None:
            # Paragraph Style (w:pStyle -> style)
            p_style = p_pr.find(qn("w:pStyle"))
            if p_style is not None:
                paragraph_properties[self.tag_to_name("w:pStyle")] = p_style.attrib.get(qn("w:val"), "")

            # Alignment (w:jc -> alignment)
            jc = p_pr.find(qn("w:jc"))
            if jc is not None:
                paragraph_properties[self.tag_to_name("w:jc")] = jc.attrib.get(qn("w:val"), "")

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
                    paragraph_properties[self.tag_to_name("w:spacing")] = sp_dict

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
                    paragraph_properties[self.tag_to_name("w:ind")] = ind_dict

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

            # Numbering Properties (w:numPr -> numberingProperties)
            num_pr = p_pr.find(qn("w:numPr"))
            if num_pr is not None:
                num_dict: dict[str, Any] = {}
                ilvl = num_pr.find(qn("w:ilvl"))
                if ilvl is not None:
                    val = ilvl.attrib.get(qn("w:val"))
                    lvl_val = int(val) if val and val.isdigit() else val
                    num_dict[self.tag_to_name("w:ilvl")] = lvl_val
                    num_dict["level"] = lvl_val
                num_id = num_pr.find(qn("w:numId"))
                if num_id is not None:
                    val = num_id.attrib.get(qn("w:val"))
                    id_val = int(val) if val and val.isdigit() else val
                    num_dict[self.tag_to_name("w:numId")] = id_val
                    num_dict["id"] = id_val
                if num_dict:
                    paragraph_properties[self.tag_to_name("w:numPr")] = num_dict
                    paragraph_properties["numbering"] = num_dict

            # Keep with next (w:keepNext -> keepWithNext)
            if p_pr.find(qn("w:keepNext")) is not None:
                paragraph_properties[self.tag_to_name("w:keepNext")] = True
                paragraph_properties["keepNext"] = True

            # Page break before (w:pageBreakBefore -> pageBreakBefore)
            if p_pr.find(qn("w:pageBreakBefore")) is not None:
                paragraph_properties[self.tag_to_name("w:pageBreakBefore")] = True
                paragraph_properties["pageBreakBefore"] = True

            # Paragraph Shading (w:shd -> shading)
            p_shd = p_pr.find(qn("w:shd"))
            if p_shd is not None:
                shd_dict: dict[str, Any] = {}
                for k, v in p_shd.attrib.items():
                    shd_dict[local_name(k)] = v
                paragraph_properties[self.tag_to_name("w:shd")] = shd_dict
                paragraph_properties["shading"] = shd_dict

            # Paragraph Mark Run Properties (w:rPr inside w:pPr)
            p_rpr = p_pr.find(qn("w:rPr"))
            if p_rpr is not None:
                r_json = self.run_handler.to_json(p_rpr)
                if r_json.get("properties"):
                    paragraph_properties["markProperties"] = r_json["properties"]

        runs: list[dict[str, Any]] = []
        for child in element:
            if child.tag == qn("w:r"):
                runs.append(self.run_handler.to_json(child))
            elif child.tag == qn("w:hyperlink"):
                hl_id = child.attrib.get(qn("r:id"), "")
                anchor = child.attrib.get(qn("w:anchor"), "")
                for r_child in child.findall(qn("w:r")):
                    r_json = self.run_handler.to_json(r_child)
                    hl_dict: dict[str, str] = {}
                    if hl_id:
                        hl_dict["relationshipId"] = hl_id
                    if anchor:
                        hl_dict["anchor"] = anchor
                    if hl_dict:
                        r_json["hyperlink"] = hl_dict
                    runs.append(r_json)

        result: dict[str, Any] = {
            "type": self.tag_to_name("w:p"),
            "paragraphProperties": paragraph_properties,
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
        props = data.get("paragraphProperties") or data.get("properties", {})

        if props:
            p_pr = ET.SubElement(p, qn("w:pPr"))

            # Style (style)
            style_val = props.get("style")
            if style_val:
                ET.SubElement(p_pr, qn("w:pStyle"), {qn("w:val"): str(style_val)})

            # Alignment (alignment)
            align_val = props.get("alignment")
            if align_val:
                ET.SubElement(p_pr, qn("w:jc"), {qn("w:val"): str(align_val)})

            # Spacing
            if props.get("spacing"):
                sp = props["spacing"]
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
            if props.get("indentation"):
                ind = props["indentation"]
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

            # Numbering properties
            num_data = props.get("numberingProperties") or props.get("numbering")
            if num_data:
                num_pr = ET.SubElement(p_pr, qn("w:numPr"))
                ilvl_val = num_data.get("indentationLevel") or num_data.get("level")
                if ilvl_val is not None:
                    ET.SubElement(num_pr, qn("w:ilvl"), {qn("w:val"): str(ilvl_val)})
                num_id_val = num_data.get("numberingId") or num_data.get("id")
                if num_id_val is not None:
                    ET.SubElement(num_pr, qn("w:numId"), {qn("w:val"): str(num_id_val)})

            if props.get("keepWithNext") or props.get("keepNext"):
                ET.SubElement(p_pr, qn("w:keepNext"))

            if props.get("pageBreakBefore"):
                ET.SubElement(p_pr, qn("w:pageBreakBefore"))

            # Shading
            if props.get("shading"):
                shd_attrs = {qn(f"w:{k}"): str(v) for k, v in props["shading"].items()}
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
        else:
            sect_data = data.get("sectionProperties") or data.get(self.tag_to_name("w:sectPr"))
            if sect_data:
                from handlers.sections import SectionsHandler
                p_pr = ET.SubElement(p, qn("w:pPr"))
                p_pr.append(SectionsHandler().to_xml(sect_data))

        # Add child runs (grouping runs sharing a hyperlink)
        current_hl_key = None
        current_hl_elem = None

        for run_data in data.get("runs", []):
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
