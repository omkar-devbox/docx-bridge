# docx-engine

A modular Python engine for bi-directional conversion between DOCX (WordprocessingML) packages and structured JSON representations.

## Project Structure

```text
├── main.py
├── cli.py
├── pyproject.toml
│
├── converter/
│   ├── __init__.py
│   └── docx/
│       ├── __init__.py
│       ├── docx_to_json.py
│       ├── json_to_docx.py
│       ├── numbering.py
│       └── packaging.py
│
├── config/
│   ├── __init__.py
│   ├── docx.json
│   ├── page-sizes.json
│   ├── namespaces.json
│   ├── master-tags.json
│   ├── relationships.json
│   └── content-types.json
│
├── parser/
│   ├── __init__.py
│   └── docx/
│       ├── xml_to_json.py
│       └── json_to_xml.py
│
├── formats/
│   ├── __init__.py
│   └── docx/
│       ├── reader.py
│       └── writer.py
│
├── handlers/
│   ├── __init__.py
│   ├── common/
│   │   ├── base.py
│   │   ├── color.py
│   │   ├── helpers.py
│   │   ├── registry.py
│   │   └── units.py
│   └── docx/
│       ├── base.py
│       ├── comments.py
│       ├── document.py
│       ├── header_footer.py
│       ├── media.py
│       ├── notes.py
│       ├── numbering.py
│       ├── paragraph.py
│       ├── properties.py
│       ├── relationships.py
│       ├── run.py
│       ├── sections.py
│       ├── settings.py
│       ├── styles.py
│       └── table.py
│
├── utils/
│   ├── common/
│   │   └── json.py
│   └── docx/
│       └── xml.py
│
├── tests/
│   └── docx/
│       ├── test_audit.py
│       ├── test_handlers.py
│       ├── test_new_docx_features.py
│       ├── test_property_fidelity.py
│       ├── test_roundtrip.py
│       ├── test_section_styles.py
│       ├── test_simple_format.py
│       └── test_standalone_roundtrip.py
│
└── Test/
    ├── docx/
    │   ├── docxToJson.py
    │   └── jsonToDocx.py
    └── files/                          ← place your .docx / .json files here
```

## Setup & Installation

Install dependencies defined in [pyproject.toml](pyproject.toml):

```bash
pip install .
```

Or install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Running the Scripts

All scripts are run from the **project root** (`docx-bridge/`).

### DOCX → JSON  (`Test/docx/docxToJson.py`)

Converts a `.docx` file into structured JSON. Output is saved in the **same folder** as the input.

**Default (uses `FILE_PATH` set inside the script):**
```bash
python3 Test/docx/docxToJson.py
```

**Pass a custom file path as a CLI argument:**
```bash
python3 Test/docx/docxToJson.py path/to/your/file.docx
```

**Choose output mode:**
```bash
# Simple mode (clean, compact JSON) — default
python3 Test/docx/docxToJson.py path/to/file.docx --simple

# Raw mode (full OpenXML mapping with all properties)
python3 Test/docx/docxToJson.py path/to/file.docx --raw
```

---

### JSON → DOCX  (`Test/docx/jsonToDocx.py`)

Converts a structured JSON file back into a `.docx`. Output is saved in the **same folder** as the input.

> Run `docxToJson.py` first to generate the JSON, then convert it back.

**Default (uses `FILE_PATH` set inside the script):**
```bash
python3 Test/docx/jsonToDocx.py
```

**Pass a custom file path as a CLI argument:**
```bash
python3 Test/docx/jsonToDocx.py path/to/your/file.json
```

> If a `.docx` with the same name already exists, the output is saved as `<name>_converted.docx` to avoid overwriting.

---

## CLI Usage

```bash
# Convert DOCX to JSON
python3 cli.py docx-to-json input.docx -o output.json --mode simple

# Convert JSON to DOCX
python3 cli.py json-to-docx input.json -o output.docx
```

---

## Running Tests

```bash
python3 -m unittest discover -s tests/docx
```

