"""DOC to JSON conversion pipeline (legacy Word 97-2003 binary format)."""

from pathlib import Path

from formats.doc.reader import DocReader
from parser.doc.binary_to_json import BinaryToJsonParser
from utils.common.json import dump_json


def doc_to_json(
    doc_path: Path | str,
    output_path: Path | str,
    mode: str = "simple",
) -> None:
    """Convert a legacy DOC (.doc) binary file to structured JSON format."""
    doc_path = Path(doc_path)
    output_path = Path(output_path)

    with DocReader(doc_path) as reader:
        parser = BinaryToJsonParser(reader)
        data = parser.parse_document()
        dump_json(data, output_path)

        print(
            f"Successfully converted "
            f"'{doc_path}' -> '{output_path}'"
        )


__all__ = ["doc_to_json"]
