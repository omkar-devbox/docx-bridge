"""Handler for word/settings.xml and word/webSettings.xml."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


class SettingsHandler(BaseHandler):
    """Handles parsing and generating settings and webSettings for DOCX packages."""

    def to_json(
        self,
        element: ET.Element,
        **kwargs,
    ) -> dict[str, Any]:
        """Convert settings XML to JSON dictionary."""
        settings: dict[str, Any] = {}

        if element is None:
            return settings

        default_tab = element.find(qn("w:defaultTabStop"))
        if default_tab is not None:
            val = default_tab.attrib.get(qn("w:val"), "")
            settings["defaultTabStop"] = int(val) if val.isdigit() else val

        zoom = element.find(qn("w:zoom"))
        if zoom is not None:
            val = zoom.attrib.get(qn("w:percent"), "")
            settings["zoom"] = int(val) if val.isdigit() else val

        track_rev = element.find(qn("w:trackRevisions"))
        if track_rev is not None:
            settings["trackRevisions"] = True

        proof_state = element.find(qn("w:proofState"))
        if proof_state is not None:
            ps: dict[str, str] = {}
            if qn("w:spelling") in proof_state.attrib:
                ps["spelling"] = proof_state.attrib[qn("w:spelling")]
            if qn("w:grammar") in proof_state.attrib:
                ps["grammar"] = proof_state.attrib[qn("w:grammar")]
            if ps:
                settings["proofState"] = ps

        char_spacing = element.find(qn("w:characterSpacingControl"))
        if char_spacing is not None:
            settings["characterSpacingControl"] = char_spacing.attrib.get(
                qn("w:val"), "doNotCompress"
            )

        compat = element.find(qn("w:compat"))
        if compat is not None:
            for child in compat:
                if child.tag == qn("w:compatSetting"):
                    name = child.attrib.get(qn("w:name"), "")
                    val = child.attrib.get(qn("w:val"), "")
                    if name:
                        settings[name] = int(val) if val.isdigit() else val
                else:
                    tag = local_name(child.tag)
                    val = child.attrib.get(qn("w:val"))
                    if val is not None:
                        settings[tag] = val not in ("0", "false", "off")
                    else:
                        settings[tag] = True

        return settings

    def to_xml(
        self,
        settings_data: dict[str, Any] | None = None,
    ) -> ET.Element:
        """Construct a compliant w:settings XML element."""
        root = ET.Element(qn("w:settings"))
        data = settings_data or {}

        # Default tab stop (standard 720 dxa = 0.5 in)
        tab_val = data.get("defaultTabStop", 720)
        ET.SubElement(root, qn("w:defaultTabStop"), {qn("w:val"): str(tab_val)})

        # Zoom percentage
        zoom_val = data.get("zoom")
        if zoom_val is not None:
            ET.SubElement(root, qn("w:zoom"), {qn("w:percent"): str(zoom_val)})

        # Track Revisions
        if data.get("trackRevisions"):
            ET.SubElement(root, qn("w:trackRevisions"))

        # Proof state
        proof_state = data.get("proofState")
        if isinstance(proof_state, dict):
            ps_attrs: dict[str, str] = {}
            if "spelling" in proof_state:
                ps_attrs[qn("w:spelling")] = str(proof_state["spelling"])
            if "grammar" in proof_state:
                ps_attrs[qn("w:grammar")] = str(proof_state["grammar"])
            if ps_attrs:
                ET.SubElement(root, qn("w:proofState"), ps_attrs)

        # Character spacing control
        if "characterSpacingControl" in data:
            ET.SubElement(
                root,
                qn("w:characterSpacingControl"),
                {qn("w:val"): str(data["characterSpacingControl"])},
            )
        elif not data:
            ET.SubElement(
                root,
                qn("w:characterSpacingControl"),
                {qn("w:val"): "doNotCompress"},
            )

        # Compatibility settings
        known_top_level = {
            "defaultTabStop",
            "zoom",
            "trackRevisions",
            "proofState",
            "characterSpacingControl",
        }
        compat_keys = [k for k in data if k not in known_top_level]
        if compat_keys:
            compat = ET.SubElement(root, qn("w:compat"))
            for k in compat_keys:
                val = data[k]
                if isinstance(val, bool):
                    if val:
                        ET.SubElement(compat, qn(f"w:{k}"))
                    else:
                        ET.SubElement(compat, qn(f"w:{k}"), {qn("w:val"): "0"})
                else:
                    ET.SubElement(
                        compat,
                        qn("w:compatSetting"),
                        {
                            qn("w:name"): k,
                            qn("w:uri"): "http://schemas.microsoft.com/office/word",
                            qn("w:val"): str(val),
                        },
                    )
        elif not data:
            compat = ET.SubElement(root, qn("w:compat"))
            ET.SubElement(
                compat,
                qn("w:compatSetting"),
                {
                    qn("w:name"): "compatibilityMode",
                    qn("w:uri"): "http://schemas.microsoft.com/office/word",
                    qn("w:val"): "15",
                },
            )

        return root

    def to_web_settings_xml(self) -> bytes:
        """Construct standard word/webSettings.xml bytes."""
        root = ET.Element(qn("w:webSettings"))
        ET.SubElement(root, qn("w:optimizeForBrowser"))
        ET.SubElement(root, qn("w:allowPNG"))
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)


__all__ = ["SettingsHandler"]
