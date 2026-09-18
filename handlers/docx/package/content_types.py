"""Handler for Open Packaging Conventions [Content_Types].xml."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn, local_name


CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

DEFAULT_EXTENSIONS: dict[str, str] = {
    "rels": "application/vnd.openxmlformats-package.relationships+xml",
    "xml": "application/xml",
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "gif": "image/gif",
    "emf": "image/x-emf",
    "wmf": "image/x-wmf",
    "tiff": "image/tiff",
    "tif": "image/tiff",
    "bmp": "image/bmp",
    "svg": "image/svg+xml",
}

DEFAULT_OVERRIDES: dict[str, str] = {
    "/word/document.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    "/word/styles.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
    "/word/numbering.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml",
    "/word/settings.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml",
    "/word/webSettings.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.webSettings+xml",
    "/word/fontTable.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml",
    "/word/theme/theme1.xml": "application/vnd.openxmlformats-officedocument.theme+xml",
    "/docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
    "/docProps/app.xml": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
}


class ContentTypesHandler(BaseHandler):
    """Handles parsing and generating [Content_Types].xml."""

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Convert [Content_Types].xml element to JSON defaults and overrides."""
        defaults: dict[str, str] = {}
        overrides: dict[str, str] = {}

        for child in element:
            tag = local_name(child.tag)
            if tag == "Default":
                ext = child.attrib.get("Extension", "").lower()
                ct = child.attrib.get("ContentType", "")
                if ext and ct:
                    defaults[ext] = ct
            elif tag == "Override":
                part = child.attrib.get("PartName", "")
                ct = child.attrib.get("ContentType", "")
                if part and ct:
                    overrides[part] = ct

        return {
            "defaults": defaults,
            "overrides": overrides,
        }

    def to_xml(self, data: dict[str, Any] | None = None) -> ET.Element:
        """Construct [Content_Types].xml root element."""
        root = ET.Element(f"{{{CONTENT_TYPES_NS}}}Types")

        defaults = dict(DEFAULT_EXTENSIONS)
        overrides = dict(DEFAULT_OVERRIDES)

        if data:
            if "defaults" in data:
                defaults.update(data["defaults"])
            if "overrides" in data:
                overrides.update(data["overrides"])

        for ext, ct in sorted(defaults.items()):
            ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Default", {"Extension": ext, "ContentType": ct})

        for part, ct in sorted(overrides.items()):
            ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Override", {"PartName": part, "ContentType": ct})

        return root


__all__ = [
    "ContentTypesHandler",
    "CONTENT_TYPES_NS",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_OVERRIDES",
]
