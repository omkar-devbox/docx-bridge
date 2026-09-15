"""JSON to DOC conversion pipeline (legacy Word 97-2003 binary format)."""

from pathlib import Path

from formats.doc.writer import DocWriter
from utils.json import load_json


def json_to_doc(
    json_path: Path | str,
    output_path: Path | str,
    template_doc: Path | str | None = None,
) -> None:
    """Convert structured JSON back to a legacy DOC (.doc) binary file."""
    json_path = Path(json_path)
    output_path = Path(output_path)

    data = load_json(json_path)

    with DocWriter(output_path) as writer:
        writer.build_document(data)

        print(
            f"Successfully converted "
            f"'{json_path}' -> '{output_path}'"
        )


__all__ = ["json_to_doc"]
