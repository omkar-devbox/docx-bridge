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
│   ├── docx/
│   │   ├── __init__.py
│   │   ├── docx_to_json.py
│   │   ├── json_to_docx.py
│   │   ├── numbering.py
│   │   └── packaging.py
│   └── doc/
│       ├── __init__.py
│       ├── doc_to_json.py
│       └── json_to_doc.py
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
│   ├── xml_to_json.py
│   └── json_to_xml.py
│
├── formats/
│   ├── __init__.py
│   ├── docx/
│   │   ├── reader.py
│   │   └── writer.py
│   └── doc/
│       ├── reader.py
│       └── writer.py
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
├── docs/
│   ├── README.md                       # Master Documentation Hub & AI Index
│   ├── docx/                           # Modern DOCX (ECMA-376 / OpenXML) docs
│   │   ├── README.md
│   │   ├── 01-architecture-and-pipeline.md
│   │   ├── 02-schema-and-ast.md
│   │   ├── 03-handlers-and-openxml.md
│   │   └── 04-ai-generation-guide.md
│   └── doc/                            # Legacy DOC (MS-DOC / CFBF) docs
│       ├── README.md
│       ├── 01-cfbf-and-streams.md
│       ├── 02-fib-and-data-structures.md
│       ├── 03-doc-to-json-bridge.md
│       └── 04-ai-integration-guide.md
│
├── tests/
│   └── test_roundtrip.py
│
└── Test/
    ├── docxToJson.py
    ├── jsonToDocx.py
    └── files/                          ← place your .docx / .json files here
```

## 📖 Documentation Suite

Comprehensive, section-wise, and AI-compatible documentation is organized under [`docs/`](docs/README.md):

- **[Master Documentation Hub](docs/README.md)**: Architectural diagrams, format comparison matrices, and AI ingestion protocols.
- **[DOCX Format Documentation (`docs/docx/`)](docs/docx/README.md)**:
  - [Architecture & Packaging Pipeline](docs/docx/01-architecture-and-pipeline.md): OPC ZIP packaging, relationship trees, readers and writers.
  - [Unified JSON AST Specification](docs/docx/02-schema-and-ast.md): Complete typed schema (Simple vs Raw mode), sections, runs, tables, lists.
  - [OpenXML Handlers & Tag Mappings](docs/docx/03-handlers-and-openxml.md): ISO/IEC 29500 schema enforcement, unit conversions, and numbering engines.
  - [AI / LLM Document Generation Guide](docs/docx/04-ai-generation-guide.md): Prompting templates, golden examples, and anti-hallucination rules.
- **[Legacy DOC Binary Documentation (`docs/doc/`)](docs/doc/README.md)**:
  - [CFBF & Stream Architecture](docs/doc/01-cfbf-and-streams.md): Compound File Binary Format, OLE structured storage, and FAT/SAT sectors.
  - [FIB & Memory Structures](docs/doc/02-fib-and-data-structures.md): File Information Block offsets, Clx piece tables, and SPRM opcodes.
  - [DOC to JSON Bridge & Parity Mapping](docs/doc/03-doc-to-json-bridge.md): Normalization into the canonical AST.
  - [AI Binary Analysis & Diagnostic Guide](docs/doc/04-ai-integration-guide.md): Automated verification scripts and troubleshooting.

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
