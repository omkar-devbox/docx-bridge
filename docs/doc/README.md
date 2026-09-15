# Legacy DOC Binary Format Specification & Bridge Documentation

## 1. Overview

This documentation suite details the internal architecture, binary structures, and bridge strategies for Microsoft Word Binary File Format (`.doc`, Word 97-2003 / [MS-DOC]) in `docx-bridge`.

Unlike modern XML-based `.docx` packages, `.doc` files are complex binary files stored within an OLE Compound File Binary Format (CFBF) structured storage container.

```
.doc File (CFBF / OLE Container)
   │
   ├── Sector Allocation Table (SAT / FAT)
   ├── Directory Stream (Directory Entries)
   │
   ├── [WordDocument Stream] ──> Contains FIB (File Information Block) & Body Text
   ├── [0Table / 1Table Stream] ──> Contains Styles (STSH), Piece Table (Clx), Formatting (Sprms)
   ├── [Data Stream] ──> Embedded Objects, Complex Drawings
   └── [\x05SummaryInformation] ──> Document Properties & Author Metadata
```

---

## 2. Document Modules Index

| Document | Purpose | Key Concepts Covered |
| :--- | :--- | :--- |
| [01-cfbf-and-streams.md](01-cfbf-and-streams.md) | CFBF Container & Storage | OLE Structured Storage, 512-byte sectors, FAT/SAT, Mini-FAT, Directory Entries, Stream hierarchy |
| [02-fib-and-data-structures.md](02-fib-and-data-structures.md) | FIB & Memory Structures | Magic `0xA5EC`, FIB offsets, `fcMin`/`fcMac`, Piece Table (`Clx`), `PlcPcd`, STSH, SPRMs |
| [03-doc-to-json-bridge.md](03-doc-to-json-bridge.md) | Bridge & Normalization | Binary extraction pipeline, AST normalization, SPRM to JSON attribute translation |
| [04-ai-integration-guide.md](04-ai-integration-guide.md) | AI Analysis & Extraction | Hex inspection patterns, diagnostic heuristics, debugging legacy Word structures |

---

## 3. Key Specifications At-A-Glance

### 3.1 Binary Identifiers
- **CFBF Container Magic**: `0xD0CF11E0A1B11AE1` (Bytes `0x00 - 0x07`)
- **Word Document FIB Magic (`wIdent`)**: `0xA5EC` (`42617` decimal) at offset `0x00` of `WordDocument` stream
- **Default Sector Size**: `512` bytes (Sector shift = `9`)
- **Mini-Sector Size**: `64` bytes (Mini-sector cutoff = `4096` bytes)

### 3.2 Supported Word Versions (`config/doc.json`)
| Version Code (`nFib`) | Product Release |
| :--- | :--- |
| `0x00C1` | Word 6.0 / Word 95 |
| `0x00C3` | Word 97 |
| `0x00D9` | Word 2000 |
| `0x0101` | Word 2002 (XP) |
| `0x010C` | Word 2003 |
| `0x0112` | Word 2003 SP3 |

### 3.3 Target Parity with DOCX AST
The `docx-bridge` engine maps legacy binary structures into the exact same canonical JSON AST used by the DOCX engine:
- Section margins and paper codes $\longleftrightarrow$ `sections[].page`
- Paragraph Sprms $\longleftrightarrow$ `sections[].content[].style`, `align`, `spacing`
- Character Sprms $\longleftrightarrow$ `runs[].bold`, `size`, `color`, `font`
- Table descriptors $\longleftrightarrow$ `table.rows[].cells[]`
