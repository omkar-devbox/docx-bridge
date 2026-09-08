"""
DOCX to JSON Converter Script
------------------------------
This script converts a .docx file into structured JSON.
Specify the input file path below in `FILE_PATH`.
Output JSON will be generated in the SAME folder.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # Test/ -> project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import docx_to_json

# ==============================================================================
# FILE PATH & MODE CONFIGURATION (फाईलचा पाथ आणि मोड इथे बदला)
# ==============================================================================
# MODE: 'simple' = Clean, compact, developer-friendly JSON (default)
#       'raw'    = Full OpenXML mapping with all properties nested
MODE = "simple"
FILE_PATH = PROJECT_ROOT / "Test" / "files" / "Apurva Jhunjhunwala.docx"
# ==============================================================================


def run():
    mode = MODE
    # Parse CLI arguments if provided
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if "--raw" in flags:
        mode = "raw"
    elif "--simple" in flags:
        mode = "simple"

    input_path = Path(args[0]) if args else Path(FILE_PATH)

    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    if input_path.suffix.lower() == ".json":
        print(f"❌ Error: Expected a .docx file, but got a .json file: {input_path.name}")
        print(f"Did you mean to run Test/jsonToDocx.py instead?")
        sys.exit(1)

    if not input_path.exists():
        print(f"❌ Error: File not found at: {input_path}")
        print(f"Please check the path in docxToJson.py (FILE_PATH = '{FILE_PATH}')")
        sys.exit(1)

    # Output file in the SAME folder with .json extension
    output_path = input_path.with_suffix(".json")

    print(f"⏳ Converting DOCX to JSON (Mode: {mode})...")
    print(f"📁 Input DOCX : {input_path}")
    print(f"📁 Output JSON: {output_path}")

    docx_to_json(input_path, output_path, mode=mode)

    print(f"✅ Successfully converted! JSON saved in same folder:")
    print(f"👉 {output_path}")


if __name__ == "__main__":
    run()
