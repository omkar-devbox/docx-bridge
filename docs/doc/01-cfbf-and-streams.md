# Compound File Binary Format (CFBF) & Stream Architecture

## 1. The CFBF Container Architecture

A legacy `.doc` file is packaged as a **Compound File Binary Format** (CFBF, also known as Microsoft OLE Structured Storage, specified in `[MS-CFB]`). It functions as an in-file virtual filesystem containing sectors, directory trees, and named byte streams.

```text
CFBF Container Layout (.doc)
┌────────────────────────────────────────────────────────┐
│ Header (512 bytes): Magic 0xD0CF11E0A1B11AE1          │
│ Sector size: 512 bytes (or 4096 for v4)                │
├────────────────────────────────────────────────────────┤
│ DIFAT (Double-Indirect FAT) Sectors                   │
├────────────────────────────────────────────────────────┤
│ FAT / SAT (Sector Allocation Table) Sectors            │
├────────────────────────────────────────────────────────┤
│ Mini-FAT Sectors (For streams < 4096 bytes)            │
├────────────────────────────────────────────────────────┤
│ Directory Stream (Directory Entries: Root, Streams)    │
├────────────────────────────────────────────────────────┤
│ Stream Data Sectors:                                   │
│   • WordDocument Stream                                │
│   • 0Table or 1Table Stream                            │
│   • Data Stream                                        │
│   • \x05SummaryInformation Stream                      │
│   • \x05DocumentSummaryInformation Stream              │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Streams in a `.doc` File

According to [`config/doc.json`](file:///home/omkar/Documents/docx-bridge/config/doc.json), a valid Word document CFBF container encapsulates the following streams:

| Stream Name | Identifier Key | Purpose & Contents |
| :--- | :--- | :--- |
| `WordDocument` | `wordDocumentStream` | Contains the File Information Block (FIB) and raw document text stream. |
| `0Table` / `1Table` | `tableStream0` / `1` | Stores formatting definitions: Piece Table (`Clx`), Style Sheet (`STSH`), Lists, Font Table, Bookmarks. |
| `Data` | `dataStream` | Binary payload for large objects, OLE controls, and drawing graphics. |
| `\x05SummaryInformation` | `summaryInformation` | Document metadata (Title, Subject, Author, Keywords, Comments, Revision). |
| `\x05DocumentSummaryInformation` | `documentSummaryInformation` | Company, Category, Manager, Line/Page counts. |
| `\x01CompObj` | `compoundObject` | COM / OLE Class ID (CLSID) and application binding identifiers. |
| `ObjectPool` | `objectPool` | Storage container for embedded OLE compound objects (Excel sheets, equations). |

---

## 3. Table Stream Selection Heuristic

A `.doc` file contains either a `0Table` stream or a `1Table` stream, never both concurrently active.

The active stream is determined by checking the `fWhichTblStm` bit within the FIB base flags at byte offset `10` (`flags`):

```python
def get_active_table_stream_name(fib_flags: int) -> str:
    # Bit 9 (0x0200) of FIB flags determines which table stream is active:
    # 0 = "0Table"
    # 1 = "1Table"
    f_which_tbl_stm = (fib_flags >> 9) & 0x01
    return "1Table" if f_which_tbl_stm else "0Table"
```

---

## 4. Sector Traversal & Reading Flow

1. **Verify Header**: Inspect first 8 bytes for magic `0xD0CF11E0A1B11AE1`.
2. **Build SAT/FAT**: Parse FAT sector chain to map logical sector indices to physical file offsets.
3. **Traverse Directory Entries**: Locate directory entry for `WordDocument` and `0Table`/`1Table`.
4. **Stream Assembly**: Concatenate sectors to yield the contiguous memory stream for parsing.
