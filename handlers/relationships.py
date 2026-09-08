"""Handler for package and part relationship definitions (.rels)."""

from typing import Any
import xml.etree.ElementTree as ET
from handlers.base import BaseHandler, qn, NAMESPACES


class RelationshipsHandler(BaseHandler):
    """Handles package and document relationship definitions."""

    REL_NS = NAMESPACES.get("rel", "")

    def to_json(self, element: ET.Element) -> list[dict[str, Any]]:  # type: ignore[override]
        """Convert relationship XML root element into a list of relationship dictionaries."""
        relationships: list[dict[str, Any]] = []
        rel_tag = qn("rel:Relationship")
        for rel in element.findall(rel_tag):
            entry: dict[str, Any] = {
                "id": rel.attrib.get("Id", ""),
                "type": rel.attrib.get("Type", ""),
                "target": rel.attrib.get("Target", ""),
            }
            if "TargetMode" in rel.attrib:
                entry["targetMode"] = rel.attrib["TargetMode"]
            relationships.append(entry)
        return relationships

    def to_xml(self, data: list[dict[str, Any]] | dict[str, Any]) -> ET.Element:  # type: ignore[override]
        """Convert relationship dictionaries into a Relationships XML element."""
        root = ET.Element(qn("rel:Relationships"))
        rel_list = data if isinstance(data, list) else data.get("relationships", [])

        for rel in rel_list:
            attrs = {
                "Id": rel.get("id", ""),
                "Type": rel.get("type", ""),
                "Target": rel.get("target", ""),
            }
            if rel.get("targetMode"):
                attrs["TargetMode"] = rel["targetMode"]
            ET.SubElement(root, qn("rel:Relationship"), attrs)

        return root
