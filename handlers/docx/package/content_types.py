"""Handler for Open Packaging Conventions [Content_Types].xml."""

from typing import Any
import xml.etree.ElementTree as ET

from config import (
    CONTENT_TYPES_DEFAULTS,
    CONTENT_TYPES_NAMESPACE,
    CONTENT_TYPES_OVERRIDES,
)
from handlers.docx.base import BaseHandler, qn, local_name


CONTENT_TYPES_NS = CONTENT_TYPES_NAMESPACE

DEFAULT_EXTENSIONS: dict[str, str] = dict(CONTENT_TYPES_DEFAULTS)

DEFAULT_OVERRIDES: dict[str, str] = dict(CONTENT_TYPES_OVERRIDES)


class ContentTypesHandler(BaseHandler):
    """Handles parsing and generating [Content_Types].xml."""

    def __init__(self, content_types_config: dict[str, Any] | None = None):
        self.content_types_config = content_types_config or {}
        self.ns = (
            self.content_types_config.get("namespace")
            or CONTENT_TYPES_NS
        )
        self.default_extensions = dict(
            self.content_types_config.get("defaults")
            or DEFAULT_EXTENSIONS
        )
        self.default_overrides = dict(
            self.content_types_config.get("overrides")
            or DEFAULT_OVERRIDES
        )

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
        ns = getattr(self, "ns", CONTENT_TYPES_NS)
        root = ET.Element(f"{{{ns}}}Types")

        defaults = dict(getattr(self, "default_extensions", DEFAULT_EXTENSIONS))
        overrides = dict(getattr(self, "default_overrides", DEFAULT_OVERRIDES))

        if data:
            if "defaults" in data:
                defaults.update(data["defaults"])
            if "overrides" in data:
                overrides.update(data["overrides"])

        for ext, ct in sorted(defaults.items()):
            ET.SubElement(root, f"{{{ns}}}Default", {"Extension": ext, "ContentType": ct})

        for part, ct in sorted(overrides.items()):
            ET.SubElement(root, f"{{{ns}}}Override", {"PartName": part, "ContentType": ct})

        return root


__all__ = [
    "ContentTypesHandler",
    "CONTENT_TYPES_NS",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_OVERRIDES",
]
