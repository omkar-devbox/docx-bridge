"""Tables domain handlers: table, row, cell, properties."""

from handlers.docx.tables.table import TableHandler
from handlers.docx.tables.row import TableRowHandler
from handlers.docx.tables.cell import TableCellHandler
from handlers.docx.tables.properties import TablePropertiesHandler

__all__ = [
    "TableHandler",
    "TableRowHandler",
    "TableCellHandler",
    "TablePropertiesHandler",
]
