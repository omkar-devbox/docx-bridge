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
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import docx_to_json

# ==============================================================================
# FILE PATH CONFIGURATION (फाईलचा पाथ इथे बदला)
# ==============================================================================
FILE_PATH = PROJECT_ROOT / "Test" / "TestFiled" / "sample.docx"
# ==============================================================================


def run():
    # If user provided a path via CLI argument, use it; otherwise use FILE_PATH
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(FILE_PATH)

    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    if not input_path.exists():
        print(f"❌ Error: File not found at: {input_path}")
        print(f"Please check the path in docxToJson.py (FILE_PATH = '{FILE_PATH}')")
        sys.exit(1)

    # Output file in the SAME folder with .json extension
    output_path = input_path.with_suffix(".json")

    print(f"⏳ Converting DOCX to JSON...")
    print(f"📁 Input DOCX : {input_path}")
    print(f"📁 Output JSON: {output_path}")

    docx_to_json(input_path, output_path)

    print(f"✅ Successfully converted! JSON saved in same folder:")
    print(f"👉 {output_path}")


if __name__ == "__main__":
    run()
