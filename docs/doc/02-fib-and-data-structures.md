# FIB (File Information Block) & Data Structures

## 1. File Information Block (FIB) Overview

The File Information Block (FIB) resides at offset `0x00` of the `WordDocument` stream. It defines document layout, character offsets, and byte pointers to all metadata in the Table stream.

### 1.1 Base FIB Header (32 Bytes)

| Offset | Field Name | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0` | `wIdent` | `uint16` | 2 | Magic number: `0xA5EC` (`42617` decimal) |
| `2` | `nFib` | `uint16` | 2 | Word binary format version (e.g. `0x00C3` = Word 97) |
| `4` | `nProduct` | `uint16` | 2 | Product ID |
| `6` | `lid` | `uint16` | 2 | Primary Language ID (e.g. `0x0409` = en-US) |
| `8` | `pnNext` | `int16` | 2 | Next sector offset |
| `10` | `flags` | `uint16` | 2 | Status flags (Bit 9: `fWhichTblStm`, Bit 0: `fDot`) |
| `12` | `nFibBack` | `uint16` | 2 | Backward compatibility version |
| `14` | `lKey` | `int32` | 4 | Encryption key (0 if unencrypted) |
| `18` | `envr` | `uint8` | 1 | Operating environment flag |
| `19` | `flags2` | `uint8` | 1 | Secondary flags |
| `24` | `fcMin` | `uint32` | 4 | Byte offset of start of text in `WordDocument` stream |
| `28` | `fcMac` | `uint32` | 4 | Byte offset of end of text in `WordDocument` stream |

---

## 2. Extended FIB Table Pointers (`config/doc.json`)

The extended FIB holds pairs of `(fc, lcb)` where:
- `fc` = File Character / Byte Offset into the active Table Stream (`0Table` or `1Table`).
- `lcb` = Length of Count of Bytes.

| Field Name | `fc` Offset | `lcb` Offset | Target Structure & Purpose |
| :--- | :--- | :--- | :--- |
| `Stshf` | `104` | `108` | Style Sheet (`STSH`) containing character & paragraph styles |
| `PlcfBteChpx` | `192` | `196` | Bin Table for Character Property Exceptions (CHPX) |
| `PlcfBtePapx` | `200` | `204` | Bin Table for Paragraph Property Exceptions (PAPX) |
| `PlcfSea` | `208` | `212` | Section Descriptor Table (SED) |
| `SttbfBkmk` | `264` | `268` | Bookmark string names |
| `PlcfBkf` / `Bkl`| `272` / `280` | `276` / `284` | Bookmark start and end position tables |
| `Dop` | `344` | `348` | Document Properties (margins, compatibility) |
| `Clx` | `416` | `420` | Complex file structure & **Piece Table** |
| `DggInfo` | `400` | `404` | OfficeArt / Escher drawing group info |
| `PlfLfo` | `706` | `710` | List Format Override (`LFO`) for numbering |

---

## 3. Piece Table & Text Stream Assembly (`Clx`)

Modern and fast-saved Word documents store text fragmented across a **Piece Table** within the `Clx` structure.

```text
Clx Record
├── Optional Grpprls (Array of Sprm property modifiers)
└── PlcPcd (Piece Descriptor Table)
    ├── CP Array: [cp0, cp1, ..., cpN] (Character Positions)
    └── PCD Array: [pcd0, pcd1, ..., pcdN-1] (Piece Descriptors)
```

### 3.1 Piece Descriptor (`Pcd`) & Compressed Text
Each `Pcd` contains an 8-byte descriptor:
- `fcValue` (uint32): File character pointer.
- The `fcCompressed` bit (`Bit 30`, mask `0x40000000`, value `1073741824`):

```python
def decode_text_piece(word_document_stream: bytes, fc_value: int, char_count: int) -> str:
    is_compressed = bool(fc_value & 0x40000000)
    actual_offset = (fc_value & ~0x40000000)

    if is_compressed:
        # Compressed: 8-bit ANSI characters (divide byte offset by 2)
        byte_offset = actual_offset // 2
        raw_bytes = word_document_stream[byte_offset : byte_offset + char_count]
        return raw_bytes.decode("cp1252", errors="replace")
    else:
        # Uncompressed: 16-bit UTF-16LE Unicode characters
        raw_bytes = word_document_stream[actual_offset : actual_offset + (char_count * 2)]
        return raw_bytes.decode("utf-16le", errors="replace")
```

---

## 4. Single Property Modifiers (SPRM)

Formatting in `.doc` files is represented by binary opcodes called **SPRMs**. Each SPRM modifies a specific style property:

### Character SPRMs
- `sprmCFBold` (`0x0835`): Toggle bold flag.
- `sprmCFItalic` (`0x0836`): Toggle italic flag.
- `sprmCKul` (`0x2A3E`): Underline style enum.
- `sprmCHps` (`0x4A43`): Font size in half-points.
- `sprmCRgFtc0` (`0x4A51`): Primary font ID in Font Table.
- `sprmCColor` (`0x6870`): 24-bit RGB color.

### Paragraph SPRMs
- `sprmPIstd` (`0x4600`): Paragraph style ID.
- `sprmPJc` (`0x2403`): Alignment (`0=left`, `1=center`, `2=right`, `3=both`).
- `sprmPDxaLeft` (`0x840F`): Left indentation in dxa.
- `sprmPDyaLine` (`0x6412`): Line spacing.
- `sprmPDyaBefore` (`0xA413`): Space before in dxa.
- `sprmPDyaAfter` (`0x8414`): Space after in dxa.
