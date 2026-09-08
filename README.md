# docx-engine

A modular Python engine for bi-directional conversion between DOCX (WordprocessingML) packages and structured JSON representations.

## Project Structure

```text
├── main.py
├── pyproject.toml
│
├── config/
│   ├── namespaces.json
│   └── master-tags.json
│
├── parser/
│   ├── xml_to_json.py
│   └── json_to_xml.py
│
├── docx/
│   ├── reader.py
│   └── writer.py
│
├── handlers/
│   ├── __init__.py
│   ├── base.py
│   ├── document.py
│   ├── paragraph.py
│   ├── run.py
│   ├── table.py
│   ├── styles.py
│   ├── numbering.py
│   ├── sections.py
│   ├── media.py
│   └── relationships.py
│
├── utils/
│   ├── xml.py
│   └── json.py
│
├── tests/
│   └── test_roundtrip.py
│
└── Test/
    ├── docxToJson.py
    ├── jsonToDocx.py
    └── TestFiled/          ← place your .docx / .json files here
```

## Setup & Installation

Install dependencies defined in [pyproject.toml](file:///home/omkar/Documents/DocxToJson/pyproject.toml):

```bash
pip install .
```

Or install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Running the Scripts

All scripts are run from the **project root** (`DocxToJson/`).

### DOCX → JSON  (`Test/docxToJson.py`)

Converts a `.docx` file into structured JSON. Output is saved in the **same folder** as the input.

**Default (uses `FILE_PATH` set inside the script):**
```bash
python3 Test/docxToJson.py
```

**Pass a custom file path as a CLI argument:**
```bash
python3 Test/docxToJson.py path/to/your/file.docx
```

**Choose output mode:**
```bash
# Simple mode (clean, compact JSON) — default
python3 Test/docxToJson.py path/to/file.docx --simple

# Raw mode (full OpenXML mapping with all properties)
python3 Test/docxToJson.py path/to/file.docx --raw
```

---

### JSON → DOCX  (`Test/jsonToDocx.py`)

Converts a structured JSON file back into a `.docx`. Output is saved in the **same folder** as the input.

> Run `docxToJson.py` first to generate the JSON, then convert it back.

**Default (uses `FILE_PATH` set inside the script):**
```bash
python3 Test/jsonToDocx.py
```

**Pass a custom file path as a CLI argument:**
```bash
python3 Test/jsonToDocx.py path/to/your/file.json
```

> If a `.docx` with the same name already exists, the output is saved as `<name>_converted.docx` to avoid overwriting.

---

## Running Tests

```bash
python3 -m pytest tests/
```
