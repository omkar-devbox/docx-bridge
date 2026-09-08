"""
JSON to DOCX Converter Script
------------------------------
This script converts structured JSON back into a .docx file.
Specify the input file path below in `FILE_PATH`.
Output DOCX will be generated in the SAME folder.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # Test/ -> project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import json_to_docx

# ==============================================================================
# FILE PATH CONFIGURATION (फाईलचा पाथ इथे बदला)
# ==============================================================================
FILE_PATH = PROJECT_ROOT / "Test" / "files" / "Apurva Jhunjhunwala.json"
# ==============================================================================


def run():
    # If user provided a path via CLI argument, use it; otherwise use FILE_PATH
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(FILE_PATH)

    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    # If user passed a .docx file instead of .json, check if corresponding .json exists
    if input_path.suffix.lower() == ".docx":
        corresponding_json = input_path.with_suffix(".json")
        if corresponding_json.exists():
            print(f"⚠️ Notice: DOCX file path was provided. Automatically switching to corresponding JSON:")
            print(f"   {corresponding_json}")
            input_path = corresponding_json
        else:
            print(f"❌ Error: Expected a .json file, but got a .docx file: {input_path.name}")
            print(f"Corresponding JSON not found at: {corresponding_json}")
            print(f"Please run docxToJson.py first to generate the JSON.")
            sys.exit(1)

    if not input_path.exists():
        print(f"❌ Error: JSON file not found at: {input_path}")
        print(f"Please check the path in jsonToDocx.py (FILE_PATH = '{FILE_PATH}') or run docxToJson.py first.")
        sys.exit(1)

    # Output file in the SAME folder
    if (input_path.parent / f"{input_path.stem}.docx").exists():
        output_path = input_path.parent / f"{input_path.stem}_converted.docx"
    else:
        output_path = input_path.with_suffix(".docx")

    print(f"⏳ Converting JSON to DOCX...")
    print(f"📁 Input JSON : {input_path}")
    print(f"📁 Output DOCX: {output_path}")

    json_to_docx(input_path, output_path)

    print(f"✅ Successfully converted! DOCX saved in same folder:")
    print(f"👉 {output_path}")


if __name__ == "__main__":
    run()
