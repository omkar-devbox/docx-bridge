import base64
from typing import Any
from handlers.doc.base import DocBaseHandler
from formats.doc.structures import EscherParser


class DocMediaHandler(DocBaseHandler):
    """Handler for Word 97-2003 OfficeArt (Escher) drawing containers and BLIPs."""

    def to_json(self, source: Any, **kwargs) -> dict[str, Any]:
        """Convert Escher drawing record to JSON AST media item."""
        if isinstance(source, (bytes, bytearray)):
            blips = EscherParser.extract_blips(bytes(source))
            media_dict = {}
            for b in blips:
                b_data = b["data"]
                b64_str = (
                    base64.b64encode(b_data).decode("ascii")
                    if isinstance(b_data, (bytes, bytearray))
                    else str(b_data)
                )
                media_dict[b["name"]] = {
                    "bytes": b64_str,
                    "contentType": f"image/{b['type']}",
                }
            return media_dict
        if isinstance(source, dict):
            return source
        return {"type": "image"}

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize media AST to Escher binary records."""
        if isinstance(data, dict):
            out = bytearray()
            for item in data.values():
                if isinstance(item, dict) and "bytes" in item:
                    b = item["bytes"]
                    if isinstance(b, str):
                        try:
                            b = base64.b64decode(b)
                        except Exception:
                            b = b.encode("latin1")
                    elif isinstance(b, (bytes, bytearray)):
                        pass
                    else:
                        continue
                    out.extend(b)
                elif isinstance(item, str):
                    try:
                        out.extend(base64.b64decode(item))
                    except Exception:
                        out.extend(item.encode("latin1"))
                elif isinstance(item, (bytes, bytearray)):
                    out.extend(item)
            return bytes(out)
        return b""


__all__ = ["DocMediaHandler"]
