"""Handler for media and drawing relationship bindings (r:embed, r:link)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn


class MediaRelationshipsHandler(BaseHandler):
    """Handles mapping media elements to package relationships and resolving relationship targets."""

    def __init__(self, relationships: dict[str, Any] | None = None):
        self.relationships = relationships or {}

    def extract_relationship_id(self, element: ET.Element) -> str | None:
        """Extract r:embed or r:link attribute value from an element."""
        embed_id = element.attrib.get(qn("r:embed"))
        if embed_id:
            return embed_id
        link_id = element.attrib.get(qn("r:link"))
        if link_id:
            return link_id
        return None

    def set_relationship_id(
        self,
        element: ET.Element,
        rel_id: str,
        is_link: bool = False,
    ) -> None:
        """Set r:embed or r:link attribute on an element."""
        attr = qn("r:link") if is_link else qn("r:embed")
        element.set(attr, str(rel_id))

    def resolve_target(self, rel_id: str) -> str | None:
        """Resolve relationship ID to its target part URI."""
        rel_info = self.relationships.get(rel_id)
        if isinstance(rel_info, dict):
            return rel_info.get("target") or rel_info.get("Target")
        return None

    def to_json(self, element: ET.Element) -> dict[str, Any]:
        """Extract relationship ID from element into a JSON AST dictionary."""
        rel_id = self.extract_relationship_id(element)
        return {"relationshipId": rel_id} if rel_id else {}

    def to_xml(self, data: dict[str, Any]) -> ET.Element:
        """Create a placeholder element with the relationship ID bound."""
        el = ET.Element(qn("a:blip"))
        rel_id = data.get("relationshipId", "")
        if rel_id:
            self.set_relationship_id(el, rel_id)
        return el


__all__ = ["MediaRelationshipsHandler"]
