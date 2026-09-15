"""Handler for OPC document metadata (docProps/core.xml and docProps/app.xml)."""

from datetime import datetime, timezone
from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, local_name


CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
APP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


# Register namespaces for proper serialization
ET.register_namespace("cp", CORE_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("dcterms", DCTERMS_NS)
ET.register_namespace("xsi", XSI_NS)
ET.register_namespace("ep", APP_NS)
ET.register_namespace("vt", "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes")


class PropertiesHandler(BaseHandler):
    """Handles parsing and generating core and extended document properties."""

    def to_json(
        self,
        element: ET.Element,
        app_element: ET.Element | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Parse core.xml and optional app.xml elements into a unified metadata dictionary."""
        metadata: dict[str, Any] = {}

        if element is not None:
            # Parse coreProperties
            for child in element:
                tag = local_name(child.tag)
                val = (child.text or "").strip()
                if not val:
                    continue

                if tag == "title":
                    metadata["title"] = val
                elif tag == "subject":
                    metadata["subject"] = val
                elif tag == "creator":
                    metadata["author"] = val
                    metadata["creator"] = val
                elif tag == "keywords":
                    metadata["keywords"] = val
                elif tag == "description":
                    metadata["description"] = val
                elif tag == "lastModifiedBy":
                    metadata["lastModifiedBy"] = val
                elif tag == "revision":
                    metadata["revision"] = int(val) if val.isdigit() else val
                elif tag == "created":
                    metadata["created"] = val
                elif tag == "modified":
                    metadata["modified"] = val

        if app_element is not None:
            # Parse extended properties
            for child in app_element:
                tag = local_name(child.tag)
                val = (child.text or "").strip()
                if not val:
                    continue

                if tag == "Application":
                    metadata["application"] = val
                elif tag == "AppVersion":
                    metadata["appVersion"] = val
                elif tag == "Pages":
                    metadata["pages"] = int(val) if val.isdigit() else val
                elif tag == "Words":
                    metadata["words"] = int(val) if val.isdigit() else val
                elif tag == "Characters":
                    metadata["characters"] = int(val) if val.isdigit() else val
                elif tag == "Lines":
                    metadata["lines"] = int(val) if val.isdigit() else val
                elif tag == "Paragraphs":
                    metadata["paragraphs"] = int(val) if val.isdigit() else val
                elif tag == "Company":
                    metadata["company"] = val

        return metadata

    def to_core_xml(self, metadata: dict[str, Any]) -> bytes:
        """Build docProps/core.xml content bytes."""
        root = ET.Element(f"{{{CORE_NS}}}coreProperties")

        title = metadata.get("title")
        if title:
            el = ET.SubElement(root, f"{{{DC_NS}}}title")
            el.text = str(title)

        subject = metadata.get("subject")
        if subject:
            el = ET.SubElement(root, f"{{{DC_NS}}}subject")
            el.text = str(subject)

        creator = metadata.get("creator") or metadata.get("author") or "docx-bridge"
        el = ET.SubElement(root, f"{{{DC_NS}}}creator")
        el.text = str(creator)

        keywords = metadata.get("keywords")
        if keywords:
            el = ET.SubElement(root, f"{{{CORE_NS}}}keywords")
            el.text = str(keywords)

        description = metadata.get("description")
        if description:
            el = ET.SubElement(root, f"{{{DC_NS}}}description")
            el.text = str(description)

        last_modified_by = metadata.get("lastModifiedBy") or creator
        el = ET.SubElement(root, f"{{{CORE_NS}}}lastModifiedBy")
        el.text = str(last_modified_by)

        revision = metadata.get("revision", 1)
        el = ET.SubElement(root, f"{{{CORE_NS}}}revision")
        el.text = str(revision)

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        created = metadata.get("created", now_iso)
        c_el = ET.SubElement(
            root,
            f"{{{DCTERMS_NS}}}created",
            {f"{{{XSI_NS}}}type": "dcterms:W3CDTF"},
        )
        c_el.text = str(created)

        modified = metadata.get("modified", now_iso)
        m_el = ET.SubElement(
            root,
            f"{{{DCTERMS_NS}}}modified",
            {f"{{{XSI_NS}}}type": "dcterms:W3CDTF"},
        )
        m_el.text = str(modified)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def to_app_xml(self, metadata: dict[str, Any]) -> bytes:
        """Build docProps/app.xml content bytes."""
        root = ET.Element(f"{{{APP_NS}}}Properties")

        app_name = metadata.get("application", "docx-bridge")
        app_el = ET.SubElement(root, f"{{{APP_NS}}}Application")
        app_el.text = str(app_name)

        for key, xml_name in [
            ("pages", "Pages"),
            ("words", "Words"),
            ("characters", "Characters"),
            ("lines", "Lines"),
            ("paragraphs", "Paragraphs"),
            ("company", "Company"),
            ("appVersion", "AppVersion"),
        ]:
            if key in metadata:
                el = ET.SubElement(root, f"{{{APP_NS}}}{xml_name}")
                el.text = str(metadata[key])

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Format-agnostic to_xml returning coreProperties element."""
        return ET.fromstring(self.to_core_xml(data))


__all__ = ["PropertiesHandler"]
