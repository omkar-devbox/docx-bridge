"""Legacy Microsoft Word (.doc, Word 97-2003) binary handlers."""

from handlers.doc.base import DocBaseHandler
from handlers.doc.document import DocDocumentHandler
from handlers.doc.paragraph import DocParagraphHandler
from handlers.doc.run import DocRunHandler
from handlers.doc.table import DocTableHandler
from handlers.doc.styles import DocStylesHandler
from handlers.doc.numbering import DocNumberingHandler
from handlers.doc.sections import DocSectionsHandler
from handlers.doc.media import DocMediaHandler
from handlers.common.registry import BaseHandlerRegistry


class DocHandlerRegistry(BaseHandlerRegistry):
    """Registry coordinating legacy DOC binary handlers."""

    def __init__(self):
        super().__init__()
        self.run_handler = DocRunHandler()
        self.paragraph_handler = DocParagraphHandler(run_handler=self.run_handler)
        self.table_handler = DocTableHandler(paragraph_handler=self.paragraph_handler)
        self.sections_handler = DocSectionsHandler()
        self.media_handler = DocMediaHandler()
        self.document_handler = DocDocumentHandler(
            paragraph_handler=self.paragraph_handler,
            table_handler=self.table_handler,
            sections_handler=self.sections_handler,
            media_handler=self.media_handler,
        )
        self.styles_handler = DocStylesHandler()
        self.numbering_handler = DocNumberingHandler()

        # Register standard type handlers
        self.register("document", self.document_handler)
        self.register("paragraph", self.paragraph_handler)
        self.register("run", self.run_handler)
        self.register("table", self.table_handler)
        self.register("section", self.sections_handler)
        self.register("styles", self.styles_handler)
        self.register("numbering", self.numbering_handler)
        self.register("media", self.media_handler)

    def get_handler_for_native(self, stream_or_sprm_name: str) -> DocBaseHandler | None:
        """Find handler corresponding to a stream or SPRM category name."""
        stream_map = {
            "WordDocument": self.document_handler,
            "1Table": self.document_handler,
            "0Table": self.document_handler,
            "Data": self.media_handler,
            "character": self.run_handler,
            "paragraph": self.paragraph_handler,
            "table": self.table_handler,
            "section": self.sections_handler,
            "styles": self.styles_handler,
            "numbering": self.numbering_handler,
        }
        return stream_map.get(stream_or_sprm_name)


__all__ = [
    "DocBaseHandler",
    "DocDocumentHandler",
    "DocParagraphHandler",
    "DocRunHandler",
    "DocTableHandler",
    "DocStylesHandler",
    "DocNumberingHandler",
    "DocSectionsHandler",
    "DocMediaHandler",
    "DocHandlerRegistry",
]
