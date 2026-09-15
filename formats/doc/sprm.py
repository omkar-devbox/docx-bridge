"""Word Single Property Modifier (SPRM) and GRPPRL engine in pure Python.

Implements the [MS-DOC] 2.2.5 SPRM architecture:
- Opcode parsing with standard spra length determination
- Encoding & decoding of character, paragraph, section, and table properties
- Bidirectional translation to unified JSON AST format
"""

from __future__ import annotations

import struct
from typing import Any, Dict, List, Optional, Tuple


def _bgr_to_hex(bgr: int) -> str:
    r = bgr & 0xFF
    g = (bgr >> 8) & 0xFF
    b = (bgr >> 16) & 0xFF
    return f"{r:02X}{g:02X}{b:02X}"


def _hex_to_bgr(hex_str: str) -> int:
    clean = str(hex_str).lstrip("#").strip()
    if len(clean) == 6:
        try:
            r = int(clean[0:2], 16)
            g = int(clean[2:4], 16)
            b = int(clean[4:6], 16)
            return r | (g << 8) | (b << 16)
        except ValueError:
            return 0
    return 0


def _half_points_to_pt(hp: int) -> float:
    return hp / 2.0


def _pt_to_half_points(pt: float | int) -> int:
    return int(round(float(pt) * 2))


def _normalize_alignment(align: Any) -> str:
    s = str(align).lower().strip()
    return "both" if s in ("justify", "both") else s

# --------------------------------
# SPRM Opcode Constants
# --------------------------------

# Character formatting SPRMs
SPRM_C_BOLD = 0x0835         # sprmCFBold (1 byte)
SPRM_C_ITALIC = 0x0836       # sprmCFItalic (1 byte)
SPRM_C_STRIKE = 0x0837       # sprmCFStrike (1 byte)
SPRM_C_OUTLINE = 0x0838      # sprmCFOutline (1 byte)
SPRM_C_SHADOW = 0x0839       # sprmCFShadow (1 byte)
SPRM_C_SMALLCAPS = 0x083A    # sprmCFSmallCaps (1 byte)
SPRM_C_CAPS = 0x083B         # sprmCFCaps (1 byte)
SPRM_C_VANISH = 0x083C       # sprmCFVanish (1 byte)
SPRM_C_KUL = 0x2A3E          # sprmCKul (underline, 1 byte)
SPRM_C_COLOR_IDX = 0x2A42    # sprmCIco (color index, 1 byte)
SPRM_C_HPS = 0x4A43          # sprmCHps (font size in half points, 2 bytes)
SPRM_C_ISTD = 0x4A30         # sprmCIstd (character style index, 2 bytes)
SPRM_C_FTC0 = 0x4A4F         # sprmCRgFtc0 (font index ASCII, 2 bytes)
SPRM_C_FTC1 = 0x4A50         # sprmCRgFtc1 (font index East Asian, 2 bytes)
SPRM_C_FTC2 = 0x4A51         # sprmCRgFtc2 (font index Non-FE, 2 bytes)
SPRM_C_COLOR_CV = 0x6A61     # sprmCCv (32-bit COLORREF / BGR, 4 bytes)
SPRM_C_COLOR = 0x4A60        # sprmCColor (2 bytes or 4 bytes)
SPRM_C_HIGHLIGHT = 0x2A0C    # sprmCHighlight (1 byte)

# Paragraph formatting SPRMs
SPRM_P_ISTD = 0x4600         # sprmPIstd (style index, 2 bytes)
SPRM_P_JC = 0x2403           # sprmPJc (alignment, 1 byte: 0=L, 1=C, 2=R, 3=Both)
SPRM_P_KEEP = 0x2405         # sprmPFKeep (1 byte)
SPRM_P_KEEPNEXT = 0x2406     # sprmPFKeepFollow (1 byte)
SPRM_P_PAGEBREAK = 0x2407    # sprmPFPageBreakBefore (1 byte)
SPRM_P_ILVL = 0x260A         # sprmPIlvl (outline level, 1 byte)
SPRM_P_ILFO = 0x460B         # sprmPIlfo (list format override ID, 2 bytes)
SPRM_P_DXA_RIGHT = 0x840E    # sprmPDxaRight (indent right, 2 bytes)
SPRM_P_DXA_LEFT = 0x840F     # sprmPDxaLeft (indent left, 2 bytes)
SPRM_P_DXA_FIRST = 0x8411    # sprmPDxaLeft1 (first line / hanging indent, 2 bytes)
SPRM_P_DYA_LINE = 0x6412     # sprmPDyaLine (line spacing, 4 bytes)
SPRM_P_DYA_BEFORE = 0xA413   # sprmPDyaBefore (space before, 2 bytes)
SPRM_P_DYA_AFTER = 0x8414    # sprmPDyaAfter (space after, 2 bytes)
SPRM_P_IN_TABLE = 0x2416     # sprmPFInTable (1 byte)

# Section formatting SPRMs
SPRM_S_DXA_PAGE = 0xB01F     # sprmSDxaPage (page width, 2 bytes)
SPRM_S_DYA_PAGE = 0xB020     # sprmSDyaPage (page height, 2 bytes)
SPRM_S_DXA_LEFT = 0xB021     # sprmSDxaLeft (margin left, 2 bytes)
SPRM_S_DXA_RIGHT = 0xB022    # sprmSDxaRight (margin right, 2 bytes)
SPRM_S_DYA_TOP = 0x9023      # sprmSDyaTop (margin top, 2 bytes)
SPRM_S_DYA_BOTTOM = 0x9024   # sprmSDyaBottom (margin bottom, 2 bytes)
SPRM_S_DYA_HDRTOP = 0x9027   # sprmSDyaHdrTop (header margin, 2 bytes)
SPRM_S_DYA_HDRBOTTOM = 0x9028# sprmSDyaHdrBottom (footer margin, 2 bytes)
SPRM_S_ORIENT = 0x302A       # sprmSDmOrientPage (orientation, 1 byte: 1=P, 2=L)
SPRM_S_COLUMNS = 0x500B      # sprmSCcolumns (column count, 2 bytes)

# Table formatting SPRMs
SPRM_T_DXA_LEFT = 0x9601     # sprmTDxaLeft (table indent, 2 bytes)
SPRM_T_JC = 0x546A           # sprmTJc (table alignment, 2 bytes)
SPRM_T_DEF_TABLE = 0xD608    # sprmTDefTable (variable length table definition)
SPRM_T_WIDTH_CELL = 0xF614   # sprmTWidthCell (cell widths)
SPRM_T_BORDERS = 0xD605      # sprmTTableBorders


def get_sprm_operand_size(sprm: int, data: bytes, offset: int) -> int:
    """Calculate the operand length in bytes according to [MS-DOC] 2.2.5."""
    spra = (sprm >> 13) & 0x07

    if spra in (0, 1):
        return 1
    elif spra in (2, 4, 5):
        return 2
    elif spra == 3:
        return 4
    elif spra == 7:
        return 3
    elif spra == 6:
        # Variable length operand
        # Special case: sprmTDefTable (0xD608) has a 2-byte size
        if sprm == SPRM_T_DEF_TABLE:
            if offset + 2 <= len(data):
                return struct.unpack_from("<H", data, offset)[0] + 2
            return 0
        else:
            # 1-byte size field
            if offset < len(data):
                cb = data[offset]
                return cb + 1
            return 0

    return 0


# --------------------------------
# SPRM Decoder
# --------------------------------

def decode_grpprl(grpprl_bytes: bytes) -> List[Tuple[int, bytes]]:
    """Parse raw GRPPRL bytes into a list of (sprm_opcode, operand_bytes)."""
    results: List[Tuple[int, bytes]] = []
    offset = 0
    total = len(grpprl_bytes)

    while offset + 2 <= total:
        sprm = struct.unpack_from("<H", grpprl_bytes, offset)[0]
        offset += 2

        op_size = get_sprm_operand_size(sprm, grpprl_bytes, offset)
        if offset + op_size > total:
            # Truncated operand, consume remaining
            operand = grpprl_bytes[offset:]
            results.append((sprm, operand))
            break

        operand = grpprl_bytes[offset : offset + op_size]
        offset += op_size
        results.append((sprm, operand))

    return results


def decode_character_formatting(grpprl_bytes: bytes) -> Dict[str, Any]:
    """Decode character formatting GRPPRL into AST run properties."""
    props: Dict[str, Any] = {}
    tokens = decode_grpprl(grpprl_bytes)

    for sprm, operand in tokens:
        if sprm == SPRM_C_BOLD and operand:
            props["bold"] = bool(operand[0])
        elif sprm == SPRM_C_ITALIC and operand:
            props["italic"] = bool(operand[0])
        elif sprm == SPRM_C_STRIKE and operand:
            props["strike"] = bool(operand[0])
        elif sprm == SPRM_C_KUL and operand:
            val = operand[0]
            if val == 1:
                props["underline"] = "single"
            elif val == 3:
                props["underline"] = "double"
            elif val == 4:
                props["underline"] = "dotted"
            elif val == 0:
                props["underline"] = "none"
            else:
                props["underline"] = str(val)
        elif sprm == SPRM_C_HPS and len(operand) >= 2:
            half_pts = struct.unpack_from("<H", operand)[0]
            props["size"] = _half_points_to_pt(half_pts)
        elif sprm == SPRM_C_COLOR_CV and len(operand) >= 4:
            bgr = struct.unpack_from("<I", operand)[0]
            props["color"] = _bgr_to_hex(bgr)
        elif sprm == SPRM_C_COLOR and len(operand) >= 2:
            # Sometimes 16-bit or 32-bit
            if len(operand) >= 4:
                bgr = struct.unpack_from("<I", operand)[0]
                props["color"] = _bgr_to_hex(bgr)
        elif sprm == SPRM_C_ISTD and len(operand) >= 2:
            props["styleIndex"] = struct.unpack_from("<H", operand)[0]
        elif sprm in (SPRM_C_FTC0, SPRM_C_FTC1, SPRM_C_FTC2) and len(operand) >= 2:
            font_idx = struct.unpack_from("<H", operand)[0]
            props["fontIndex"] = font_idx
        elif sprm == SPRM_C_HIGHLIGHT and operand:
            props["highlight"] = operand[0]

    return props


def decode_paragraph_formatting(grpprl_bytes: bytes) -> Dict[str, Any]:
    """Decode paragraph formatting GRPPRL into AST paragraph properties."""
    props: Dict[str, Any] = {}
    tokens = decode_grpprl(grpprl_bytes)

    for sprm, operand in tokens:
        if sprm == SPRM_P_JC and operand:
            jc = operand[0]
            align_map = {0: "left", 1: "center", 2: "right", 3: "both"}
            props["align"] = align_map.get(jc, "left")
        elif sprm == SPRM_P_ISTD and len(operand) >= 2:
            props["styleIndex"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_P_DYA_BEFORE and len(operand) >= 2:
            props.setdefault("spacing", {})["before"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_P_DYA_AFTER and len(operand) >= 2:
            props.setdefault("spacing", {})["after"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_P_DYA_LINE and len(operand) >= 4:
            props.setdefault("spacing", {})["line"] = struct.unpack_from("<i", operand)[0]
        elif sprm == SPRM_P_DXA_LEFT and len(operand) >= 2:
            props.setdefault("indent", {})["left"] = struct.unpack_from("<h", operand)[0]
        elif sprm == SPRM_P_DXA_RIGHT and len(operand) >= 2:
            props.setdefault("indent", {})["right"] = struct.unpack_from("<h", operand)[0]
        elif sprm == SPRM_P_DXA_FIRST and len(operand) >= 2:
            val = struct.unpack_from("<h", operand)[0]
            if val >= 0:
                props.setdefault("indent", {})["firstLine"] = val
            else:
                props.setdefault("indent", {})["hanging"] = abs(val)
        elif sprm == SPRM_P_ILFO and len(operand) >= 2:
            props.setdefault("numbering", {})["id"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_P_ILVL and operand:
            props.setdefault("numbering", {})["level"] = operand[0]
        elif sprm == SPRM_P_IN_TABLE and operand:
            props["inTable"] = bool(operand[0])
        elif sprm == SPRM_P_KEEP and operand:
            props["keepLines"] = bool(operand[0])
        elif sprm == SPRM_P_KEEPNEXT and operand:
            props["keepWithNext"] = bool(operand[0])
        elif sprm == SPRM_P_PAGEBREAK and operand:
            props["pageBreakBefore"] = bool(operand[0])

    return props


def decode_section_formatting(grpprl_bytes: bytes) -> Dict[str, Any]:
    """Decode section formatting GRPPRL into AST section properties."""
    sec: Dict[str, Any] = {
        "page": {
            "margins": {}
        }
    }
    margins = sec["page"]["margins"]
    tokens = decode_grpprl(grpprl_bytes)

    for sprm, operand in tokens:
        if sprm == SPRM_S_DXA_LEFT and len(operand) >= 2:
            margins["left"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_DXA_RIGHT and len(operand) >= 2:
            margins["right"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_DYA_TOP and len(operand) >= 2:
            margins["top"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_DYA_BOTTOM and len(operand) >= 2:
            margins["bottom"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_DYA_HDRTOP and len(operand) >= 2:
            margins["header"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_DYA_HDRBOTTOM and len(operand) >= 2:
            margins["footer"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_DXA_PAGE and len(operand) >= 2:
            sec["page"]["width"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_DYA_PAGE and len(operand) >= 2:
            sec["page"]["height"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_S_ORIENT and operand:
            sec["page"]["orientation"] = "landscape" if operand[0] == 2 else "portrait"
        elif sprm == SPRM_S_COLUMNS and len(operand) >= 2:
            sec["page"]["columns"] = struct.unpack_from("<H", operand)[0]

    return sec


# --------------------------------
# SPRM Encoder
# --------------------------------

def encode_character_formatting(
    props: Dict[str, Any],
    font_table: Optional[Dict[str, int]] = None,
    style_table: Optional[Dict[str, int]] = None,
) -> bytes:
    """Encode run formatting AST into character GRPPRL bytes."""
    out = bytearray()

    # Character style
    if "style" in props and style_table:
        s_name = str(props["style"])
        if s_name in style_table:
            out.extend(struct.pack("<HH", SPRM_C_ISTD, style_table[s_name]))
    elif "styleIndex" in props:
        out.extend(struct.pack("<HH", SPRM_C_ISTD, int(props["styleIndex"])))

    if "bold" in props:
        out.extend(struct.pack("<HB", SPRM_C_BOLD, 1 if props["bold"] else 0))

    if "italic" in props:
        out.extend(struct.pack("<HB", SPRM_C_ITALIC, 1 if props["italic"] else 0))

    if "strike" in props:
        out.extend(struct.pack("<HB", SPRM_C_STRIKE, 1 if props["strike"] else 0))

    if "underline" in props:
        u_val = props["underline"]
        kul = 1 if u_val in ("single", True) else (3 if u_val == "double" else 0)
        out.extend(struct.pack("<HB", SPRM_C_KUL, kul))

    if "size" in props:
        pts = float(props["size"])
        half_pts = _pt_to_half_points(pts)
        out.extend(struct.pack("<HH", SPRM_C_HPS, half_pts))

    if "color" in props:
        color_str = str(props["color"]).strip()
        bgr = _hex_to_bgr(color_str)
        out.extend(struct.pack("<HI", SPRM_C_COLOR_CV, bgr))

    if "fontIndex" in props and props["fontIndex"] is not None:
        try:
            out.extend(struct.pack("<HH", SPRM_C_FTC0, int(props["fontIndex"])))
        except (ValueError, TypeError):
            pass
    elif "font" in props and font_table:
        font_name = str(props["font"])
        if font_name in font_table:
            idx = font_table[font_name]
            out.extend(struct.pack("<HH", SPRM_C_FTC0, idx))

    return bytes(out)


def encode_paragraph_formatting(props: Dict[str, Any], style_table: Optional[Dict[str, int]] = None) -> bytes:
    """Encode paragraph formatting AST into paragraph GRPPRL bytes."""
    out = bytearray()

    # Style
    if "style" in props and style_table:
        s_name = str(props["style"])
        if s_name in style_table:
            out.extend(struct.pack("<HH", SPRM_P_ISTD, style_table[s_name]))
    elif "styleIndex" in props:
        out.extend(struct.pack("<HH", SPRM_P_ISTD, int(props["styleIndex"])))

    # Alignment
    if "align" in props:
        al = _normalize_alignment(props["align"])
        jc_map = {"left": 0, "center": 1, "right": 2, "both": 3}
        out.extend(struct.pack("<HB", SPRM_P_JC, jc_map.get(al, 0)))

    # Spacing
    spacing = props.get("spacing")
    if isinstance(spacing, dict):
        if "before" in spacing:
            out.extend(struct.pack("<HH", SPRM_P_DYA_BEFORE, int(spacing["before"])))
        if "after" in spacing:
            out.extend(struct.pack("<HH", SPRM_P_DYA_AFTER, int(spacing["after"])))
        if "line" in spacing:
            out.extend(struct.pack("<Hi", SPRM_P_DYA_LINE, int(spacing["line"])))

    # Indentation
    indent = props.get("indent")
    if isinstance(indent, dict):
        if "left" in indent:
            out.extend(struct.pack("<Hh", SPRM_P_DXA_LEFT, int(indent["left"])))
        if "right" in indent:
            out.extend(struct.pack("<Hh", SPRM_P_DXA_RIGHT, int(indent["right"])))
        if "firstLine" in indent:
            out.extend(struct.pack("<Hh", SPRM_P_DXA_FIRST, int(indent["firstLine"])))
        elif "hanging" in indent:
            out.extend(struct.pack("<Hh", SPRM_P_DXA_FIRST, -int(indent["hanging"])))
    elif isinstance(indent, (int, float)):
        out.extend(struct.pack("<Hh", SPRM_P_DXA_LEFT, int(indent)))

    # Numbering
    numbering = props.get("numbering")
    if isinstance(numbering, dict):
        if "id" in numbering:
            out.extend(struct.pack("<HH", SPRM_P_ILFO, int(numbering["id"])))
        if "level" in numbering:
            out.extend(struct.pack("<HB", SPRM_P_ILVL, int(numbering["level"])))

    # Pagination / Keep
    if "keepWithNext" in props:
        out.extend(struct.pack("<HB", SPRM_P_KEEPNEXT, 1 if props["keepWithNext"] else 0))
    if "keepLines" in props:
        out.extend(struct.pack("<HB", SPRM_P_KEEP, 1 if props["keepLines"] else 0))

    # In Table
    if props.get("inTable"):
        out.extend(struct.pack("<HB", SPRM_P_IN_TABLE, 1))

    return bytes(out)


def encode_section_formatting(props: Dict[str, Any]) -> bytes:
    """Encode section formatting AST into section GRPPRL bytes."""
    out = bytearray()
    page = props.get("page", {})
    margins = page.get("margins", {})

    if "left" in margins:
        out.extend(struct.pack("<HH", SPRM_S_DXA_LEFT, int(margins["left"])))
    if "right" in margins:
        out.extend(struct.pack("<HH", SPRM_S_DXA_RIGHT, int(margins["right"])))
    if "top" in margins:
        out.extend(struct.pack("<HH", SPRM_S_DYA_TOP, int(margins["top"])))
    if "bottom" in margins:
        out.extend(struct.pack("<HH", SPRM_S_DYA_BOTTOM, int(margins["bottom"])))
    if "header" in margins:
        out.extend(struct.pack("<HH", SPRM_S_DYA_HDRTOP, int(margins["header"])))
    if "footer" in margins:
        out.extend(struct.pack("<HH", SPRM_S_DYA_HDRBOTTOM, int(margins["footer"])))

    if "width" in page:
        out.extend(struct.pack("<HH", SPRM_S_DXA_PAGE, int(page["width"])))
    if "height" in page:
        out.extend(struct.pack("<HH", SPRM_S_DYA_PAGE, int(page["height"])))

    if "orientation" in page:
        orient = 2 if page["orientation"] == "landscape" else 1
        out.extend(struct.pack("<HB", SPRM_S_ORIENT, orient))

    return bytes(out)


__all__ = [
    "decode_grpprl",
    "decode_character_formatting",
    "decode_paragraph_formatting",
    "decode_section_formatting",
    "encode_character_formatting",
    "encode_paragraph_formatting",
    "encode_section_formatting",
    "get_sprm_operand_size",
]
