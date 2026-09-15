# DOCX Format Specification & Engine Documentation

## 1. Overview

The `docx-bridge` DOCX engine is a high-fidelity bi-directional translation system between Microsoft Word OpenXML packages (`.docx`, adhering to ECMA-376 4th edition and ISO/IEC 29500:2008) and structured JSON Abstract Syntax Trees (AST).

```
.docx (ZIP / OPC Package)
   │
   ▼
[formats/docx/reader.py] ──> Unzips, parses XML streams & relationships
   │
   ▼
[parser/xml_to_json.py] + [handlers/*] ──> Parses OpenXML nodes to structured AST
   │
   ▼
[Canonical JSON AST] ──> Structured representation (Simple or Raw mode)
   │
   ▼
[converter/docx/json_to_docx.py] + [handlers/*] ──> Generates clean OpenXML
   │
   ▼
[converter/docx/packaging.py] ──> Packages XML, relations, media into valid .docx
```

---

## 2. Document Modules Index

| Document | Purpose | Key Concepts Covered |
| :--- | :--- | :--- |
| [01-architecture-and-pipeline.md](01-architecture-and-pipeline.md) | Pipeline & OPC Internals | ZIP container structure, `[Content_Types].xml`, `_rels`, `DocxReader`, `DocxWriter`, `packaging.py` |
| [02-schema-and-ast.md](02-schema-and-ast.md) | AST Schemas (Simple & Raw) | JSON Schema, section geometry, paragraphs, runs, tables, cells, lists, images, units (`dxa`, `emu`) |
| [03-handlers-and-openxml.md](03-handlers-and-openxml.md) | Handler Implementations | Mapping `w:pPr`, `w:rPr`, `w:tblPr`, `w:tcPr`, style cascading, list resolution, border types |
| [04-ai-generation-guide.md](04-ai-generation-guide.md) | LLM Generation Blueprint | Strict system prompts, token-efficient templates, error recovery, JSON validation checklists |

---

## 3. Key Specifications At-A-Glance

### 3.1 Units of Measurement
| Unit | Definition | Usage in `docx-bridge` | Conversion Factor |
| :--- | :--- | :--- | :--- |
| **dxa (Twip)** | 1/20th of a point | Page margins, widths, indentations, paragraph spacing | $1\text{ in} = 1440\text{ dxa}$, $1\text{ cm} \approx 567\text{ dxa}$ |
| **Half-Points** | 1/2 of a point | Font sizes (`w:sz`, `w:szCs`) | $24\text{ half-points} = 12\text{ pt}$ |
| **Eighth-Points**| 1/8th of a point | Border line widths (`w:sz` in borders) | $8 = 1\text{ pt}$, $4 = 0.5\text{ pt}$ |
| **EMU** | English Metric Unit | Image dimensions (`w:extent` in DrawingML) | $1\text{ in} = 914,400\text{ EMU}$, $1\text{ dxa} = 635\text{ EMU}$ |
| **pct / 50th %**| 1/50th of a percent | Table cell percentage widths | $5000 = 100\%$ |

### 3.2 Standard Page Formats (`config/page-sizes.json`)
- **A4**: Width = `11906 dxa` ($210\text{ mm}$), Height = `16838 dxa` ($297\text{ mm}$), Paper Code = `9`
- **Letter**: Width = `12240 dxa` ($8.5\text{ in}$), Height = `15840 dxa` ($11\text{ in}$), Paper Code = `1`
- **Legal**: Width = `12240 dxa` ($8.5\text{ in}$), Height = `20160 dxa` ($14\text{ in}$), Paper Code = `5`

### 3.3 Core OpenXML Namespaces
- `w`: `http://schemas.openxmlformats.org/wordprocessingml/2006/main`
- `r`: `http://schemas.openxmlformats.org/officeDocument/2006/relationships`
- `a`: `http://schemas.openxmlformats.org/drawingml/2006/main`
- `wp`: `http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing`
- `pic`: `http://schemas.openxmlformats.org/drawingml/2006/picture`
