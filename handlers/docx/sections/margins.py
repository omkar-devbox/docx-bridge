"""Handler for section margins (w:pgMar)."""

from typing import Any
import xml.etree.ElementTree as ET

from handlers.docx.base import BaseHandler, qn
from config import DEFAULT_MARGINS


class MarginsHandler(BaseHandler):
    """Handles parsing and reconstructing w:pgMar section margin elements."""

    def to_json(self, pg_mar: ET.Element) -> dict[str, Any]:
        """Convert w:pgMar element to JSON margins dictionary."""
        margins: dict[str, Any] = {}
        if pg_mar is None:
            return margins

        for attr, key in [
            ("w:top", "top"),
            ("w:bottom", "bottom"),
            ("w:left", "left"),
            ("w:right", "right"),
            ("w:header", "header"),
            ("w:footer", "footer"),
            ("w:gutter", "gutter"),
        ]:
            val = pg_mar.attrib.get(qn(attr))
            if val is not None:
                margins[key] = int(val) if val.isdigit() else val

        return margins

    def to_xml(self, margins: dict[str, Any]) -> ET.Element:
        """Construct w:pgMar element from margins dictionary."""
        pg_mar = ET.Element(qn("w:pgMar"))
        merged = {**DEFAULT_MARGINS, **margins}

        for key, attr in [
            ("top", "w:top"),
            ("bottom", "w:bottom"),
            ("left", "w:left"),
            ("right", "w:right"),
            ("header", "w:header"),
            ("footer", "w:footer"),
            ("gutter", "w:gutter"),
        ]:
            if key in merged and merged[key] is not None:
                pg_mar.set(qn(attr), str(merged[key]))

        return pg_mar


__all__ = ["MarginsHandler"]
