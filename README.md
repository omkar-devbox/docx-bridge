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
└── tests/
    └── test_roundtrip.py
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

## Running Tests

```bash
python3 -m pytest tests/
```
# docx-bridge
