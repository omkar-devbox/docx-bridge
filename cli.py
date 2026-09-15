"""Command-line interface for docx-engine."""

import argparse
import sys
import tempfile
from pathlib import Path

from converter import doc_to_json, docx_to_json, json_to_doc, json_to_docx


def create_parser() -> argparse.ArgumentParser:
    """Build and return argument parser for CLI commands."""
    parser = argparse.ArgumentParser(
        prog="docx-engine",
        description="Convert Word documents (DOCX / legacy DOC) to structured JSON and back.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Sub-commands",
    )

    # --------------------------------
    # DOCX -> JSON Command
    # --------------------------------

    docx_to_json_cmd = subparsers.add_parser(
        "docx-to-json",
        help="Convert .docx to .json",
    )

    docx_to_json_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .docx file",
    )

    docx_to_json_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .json file",
    )

    docx_to_json_cmd.add_argument(
        "-m",
        "--mode",
        choices=["simple", "raw"],
        default="simple",
        help=(
            "Output mode: 'simple' for concise AI-friendly JSON, "
            "'raw' for detailed OpenXML mapping "
            "(default: simple)"
        ),
    )

    # --------------------------------
    # JSON -> DOCX Command
    # --------------------------------

    to_docx_cmd = subparsers.add_parser(
        "json-to-docx",
        help="Convert .json to .docx",
    )

    to_docx_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .json file",
    )

    to_docx_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .docx file",
    )

    to_docx_cmd.add_argument(
        "-t",
        "--template",
        type=Path,
        default=None,
        help="Optional template .docx file",
    )

    # --------------------------------
    # DOC -> JSON Command
    # --------------------------------

    doc_to_json_cmd = subparsers.add_parser(
        "doc-to-json",
        help="Convert legacy Word .doc to .json",
    )

    doc_to_json_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .doc file",
    )

    doc_to_json_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .json file",
    )

    # --------------------------------
    # JSON -> DOC Command
    # --------------------------------

    to_doc_cmd = subparsers.add_parser(
        "json-to-doc",
        help="Convert .json to legacy Word .doc",
    )

    to_doc_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .json file",
    )

    to_doc_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .doc file",
    )

    # --------------------------------
    # DOC -> DOCX Cross Conversion
    # --------------------------------

    doc_to_docx_cmd = subparsers.add_parser(
        "doc-to-docx",
        help="Convert legacy Word .doc to .docx",
    )

    doc_to_docx_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .doc file",
    )

    doc_to_docx_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .docx file",
    )

    # --------------------------------
    # DOCX -> DOC Cross Conversion
    # --------------------------------

    docx_to_doc_cmd = subparsers.add_parser(
        "docx-to-doc",
        help="Convert .docx to legacy Word .doc",
    )

    docx_to_doc_cmd.add_argument(
        "input",
        type=Path,
        help="Path to source .docx file",
    )

    docx_to_doc_cmd.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to output .doc file",
    )

    return parser


def main(args: list[str] | None = None) -> None:
    """CLI entry point dispatching to appropriate conversion pipelines."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.command == "docx-to-json":
        docx_to_json(
            parsed_args.input,
            parsed_args.output,
            mode=parsed_args.mode,
        )

    elif parsed_args.command == "json-to-docx":
        json_to_docx(
            parsed_args.input,
            parsed_args.output,
            parsed_args.template,
        )

    elif parsed_args.command == "doc-to-json":
        doc_to_json(
            parsed_args.input,
            parsed_args.output,
        )

    elif parsed_args.command == "json-to-doc":
        json_to_doc(
            parsed_args.input,
            parsed_args.output,
        )

    elif parsed_args.command == "doc-to-docx":
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_json = Path(tmp.name)
        try:
            doc_to_json(parsed_args.input, tmp_json)
            json_to_docx(tmp_json, parsed_args.output)
            print(f"Successfully converted '{parsed_args.input}' -> '{parsed_args.output}'")
        finally:
            if tmp_json.exists():
                tmp_json.unlink()

    elif parsed_args.command == "docx-to-doc":
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_json = Path(tmp.name)
        try:
            docx_to_json(parsed_args.input, tmp_json)
            json_to_doc(tmp_json, parsed_args.output)
            print(f"Successfully converted '{parsed_args.input}' -> '{parsed_args.output}'")
        finally:
            if tmp_json.exists():
                tmp_json.unlink()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
