"""Command-line interface for docx-engine."""

import argparse
import sys
from pathlib import Path

from converter import docx_to_json, json_to_docx


def create_parser() -> argparse.ArgumentParser:
    """Build and return argument parser for CLI commands."""
    parser = argparse.ArgumentParser(
        prog="docx-engine",
        description="Convert Word documents (DOCX) to structured JSON and back.",
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

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

