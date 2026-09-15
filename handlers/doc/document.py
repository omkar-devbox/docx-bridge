"""Legacy Word (.doc) document and stream assembly handler."""

import io
from pathlib import Path
from typing import Any, BinaryIO, Union

from handlers.doc.base import DocBaseHandler
from handlers.doc.media import DocMediaHandler
from handlers.doc.numbering import DocNumberingHandler
from handlers.doc.paragraph import DocParagraphHandler
from handlers.doc.sections import DocSectionsHandler
from handlers.doc.styles import DocStylesHandler
from handlers.doc.table import DocTableHandler


class DocDocumentHandler(DocBaseHandler):
    """Handler for Word 97-2003 main document stream and structure."""

    def __init__(
        self,
        paragraph_handler: DocParagraphHandler | None = None,
        table_handler: DocTableHandler | None = None,
        sections_handler: DocSectionsHandler | None = None,
        media_handler: DocMediaHandler | None = None,
        styles_handler: DocStylesHandler | None = None,
        numbering_handler: DocNumberingHandler | None = None,
    ):
        super().__init__()
        self.paragraph_handler = paragraph_handler or DocParagraphHandler()
        self.table_handler = table_handler or DocTableHandler(paragraph_handler=self.paragraph_handler)
        self.sections_handler = sections_handler or DocSectionsHandler()
        self.media_handler = media_handler or DocMediaHandler()
        self.styles_handler = styles_handler or DocStylesHandler()
        self.numbering_handler = numbering_handler or DocNumberingHandler()

    def to_json(self, source: Union[str, Path, BinaryIO, bytes, dict], **kwargs) -> dict[str, Any]:
        """Convert document stream structure or file to JSON AST."""
        if isinstance(source, dict):
            return source

        from formats.doc.reader import DocReader

        with DocReader(source) as reader:
            return reader.parse_document()

    def to_binary(self, data: dict[str, Any], **kwargs) -> bytes:
        """Serialize document AST to complete binary Word .doc bytes."""
        from formats.doc.writer import DocWriter

        buf = io.BytesIO()
        writer = DocWriter(buf)
        writer.build_document(data)
        return writer._cfb.build()


__all__ = ["DocDocumentHandler"]
