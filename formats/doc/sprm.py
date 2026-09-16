"""Word Single Property Modifier (SPRM) and GRPPRL engine in pure Python.

Implements the [MS-DOC] 2.2.5 SPRM architecture:
- Opcode parsing with standard spra length determination
- Encoding & decoding of character, paragraph, section, and table properties
- Bidirectional translation to unified JSON AST format
- Lossless round-trip: unknown SPRMs are preserved in 'unknownSprms' bucket
"""

from __future__ import annotations

import base64
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


def _bytes_to_hex(b: bytes) -> str:
    return b.hex()


def _hex_to_bytes(h: str) -> bytes:
    try:
        return bytes.fromhex(h)
    except Exception:
        return b""


# --------------------------------
# SPRM Opcode Constants
# --------------------------------

# Character formatting SPRMs
SPRM_C_BOLD       = 0x0835  # sprmCFBold (1 byte)
SPRM_C_ITALIC     = 0x0836  # sprmCFItalic (1 byte)
SPRM_C_STRIKE     = 0x0837  # sprmCFStrike (1 byte)
SPRM_C_OUTLINE    = 0x0838  # sprmCFOutline (1 byte)
SPRM_C_SHADOW     = 0x0839  # sprmCFShadow (1 byte)
SPRM_C_SMALLCAPS  = 0x083A  # sprmCFSmallCaps (1 byte)
SPRM_C_CAPS       = 0x083B  # sprmCFCaps (1 byte)
SPRM_C_VANISH     = 0x083C  # sprmCFVanish (1 byte)
SPRM_C_KUL        = 0x2A3E  # sprmCKul (underline, 1 byte)
SPRM_C_COLOR_IDX  = 0x2A42  # sprmCIco (color index, 1 byte)
SPRM_C_HIGHLIGHT  = 0x2A0C  # sprmCHighlight (1 byte)
SPRM_C_HPS        = 0x4A43  # sprmCHps (font size in half points, 2 bytes)
SPRM_C_ISTD       = 0x4A30  # sprmCIstd (character style index, 2 bytes)
SPRM_C_FTC0       = 0x4A4F  # sprmCRgFtc0 (font index ASCII, 2 bytes)
SPRM_C_FTC1       = 0x4A50  # sprmCRgFtc1 (font index East Asian, 2 bytes)
SPRM_C_FTC2       = 0x4A51  # sprmCRgFtc2 (font index Non-FE, 2 bytes)
SPRM_C_COLOR_CV   = 0x6A61  # sprmCCv (32-bit COLORREF / BGR, 4 bytes)
SPRM_C_COLOR      = 0x4A60  # sprmCColor (2 or 4 bytes)
SPRM_C_HPSOS      = 0x4A61  # sprmCHpsOs (1 byte — sometimes seen)
SPRM_C_LANGUAGE   = 0x486D  # sprmCLid (language ID, 2 bytes)
SPRM_C_KERNING    = 0x484B  # sprmCHpsKern (kerning, 2 bytes)
SPRM_C_CHARSET    = 0x4252  # sprmCRgFtc (charset, 2 bytes)

# Paragraph formatting SPRMs
SPRM_P_ISTD        = 0x4600  # sprmPIstd (style index, 2 bytes)
SPRM_P_JC          = 0x2403  # sprmPJc (alignment, 1 byte: 0=L, 1=C, 2=R, 3=Both)
SPRM_P_KEEP        = 0x2405  # sprmPFKeep (1 byte)
SPRM_P_KEEPNEXT    = 0x2406  # sprmPFKeepFollow (1 byte)
SPRM_P_PAGEBREAK   = 0x2407  # sprmPFPageBreakBefore (1 byte)
SPRM_P_ILVL        = 0x260A  # sprmPIlvl (outline level, 1 byte)
SPRM_P_ILFO        = 0x460B  # sprmPIlfo (list format override ID, 2 bytes)
SPRM_P_DXA_RIGHT   = 0x840E  # sprmPDxaRight (indent right, 2 bytes signed)
SPRM_P_DXA_LEFT    = 0x840F  # sprmPDxaLeft (indent left, 2 bytes signed)
SPRM_P_DXA_FIRST   = 0x8411  # sprmPDxaLeft1 (first line / hanging, 2 bytes signed)
SPRM_P_DYA_LINE    = 0x6412  # sprmPDyaLine (line spacing, 4 bytes LSPD)
SPRM_P_DYA_BEFORE  = 0xA413  # sprmPDyaBefore (space before, 2 bytes)
SPRM_P_DYA_AFTER   = 0x8414  # sprmPDyaAfter (space after, 2 bytes)
SPRM_P_IN_TABLE    = 0x2416  # sprmPFInTable (1 byte)
SPRM_P_TABLE_ROW   = 0x2417  # sprmPFTtp (table row terminator, 1 byte)
SPRM_P_SHD         = 0x442C  # sprmPShd (paragraph shading, 2 bytes)
SPRM_P_BRC_TOP     = 0xC64E  # sprmPBrcTop (paragraph border top, variable)
SPRM_P_BRC_LEFT    = 0xC64F  # sprmPBrcLeft (paragraph border left)
SPRM_P_BRC_BOTTOM  = 0xC650  # sprmPBrcBottom
SPRM_P_BRC_RIGHT   = 0xC651  # sprmPBrcRight
SPRM_P_BRC_BAR     = 0xC652  # sprmPBrcBar
SPRM_P_BETWEEN     = 0xC653  # sprmPBrcBetween
SPRM_P_CHGTTABS    = 0xC60D  # sprmPChgTabsPapx (tabs, variable)
SPRM_P_OUTLINE_LVL = 0x2640  # sprmPOutLvl (outline level, 1 byte)

# Section formatting SPRMs
SPRM_S_DXA_PAGE    = 0xB01F  # sprmSDxaPage (page width, 2 bytes)
SPRM_S_DYA_PAGE    = 0xB020  # sprmSDyaPage (page height, 2 bytes)
SPRM_S_DXA_LEFT    = 0xB021  # sprmSDxaLeft (margin left, 2 bytes)
SPRM_S_DXA_RIGHT   = 0xB022  # sprmSDxaRight (margin right, 2 bytes)
SPRM_S_DYA_TOP     = 0x9023  # sprmSDyaTop (margin top, 2 bytes)
SPRM_S_DYA_BOTTOM  = 0x9024  # sprmSDyaBottom (margin bottom, 2 bytes)
SPRM_S_DYA_HDRTOP  = 0x9027  # sprmSDyaHdrTop (header margin, 2 bytes)
SPRM_S_DYA_HDRBOTTOM = 0x9028  # sprmSDyaHdrBottom (footer margin, 2 bytes)
SPRM_S_ORIENT      = 0x302A  # sprmSDmOrientPage (orientation, 1 byte: 1=P, 2=L)
SPRM_S_COLUMNS     = 0x500B  # sprmSCcolumns (column count, 2 bytes)
SPRM_S_BREAK_TYPE  = 0x3009  # sprmSBkc (section break type, 1 byte)
SPRM_S_COLS_SPACE  = 0xB02A  # sprmSDxaColumns (column spacing, 2 bytes)

# Table formatting SPRMs
SPRM_T_DXA_LEFT    = 0x9601  # sprmTDxaLeft (table indent, 2 bytes)
SPRM_T_JC          = 0x546A  # sprmTJc (table alignment, 2 bytes)
SPRM_T_DEF_TABLE   = 0xD608  # sprmTDefTable (variable length table definition)
SPRM_T_WIDTH_CELL  = 0xF614  # sprmTWidthCell (cell widths)
SPRM_T_BORDERS     = 0xD605  # sprmTTableBorders

# Known SPRMs set for quick lookup
_KNOWN_CHAR_SPRMS = {
    SPRM_C_BOLD, SPRM_C_ITALIC, SPRM_C_STRIKE, SPRM_C_OUTLINE,
    SPRM_C_SHADOW, SPRM_C_SMALLCAPS, SPRM_C_CAPS, SPRM_C_VANISH,
    SPRM_C_KUL, SPRM_C_COLOR_IDX, SPRM_C_HIGHLIGHT,
    SPRM_C_HPS, SPRM_C_ISTD,
    SPRM_C_FTC0, SPRM_C_FTC1, SPRM_C_FTC2,
    SPRM_C_COLOR_CV, SPRM_C_COLOR,
    SPRM_C_LANGUAGE, SPRM_C_KERNING, SPRM_C_CHARSET, SPRM_C_HPSOS,
}

_KNOWN_PARA_SPRMS = {
    SPRM_P_ISTD, SPRM_P_JC, SPRM_P_KEEP, SPRM_P_KEEPNEXT, SPRM_P_PAGEBREAK,
    SPRM_P_ILVL, SPRM_P_ILFO,
    SPRM_P_DXA_RIGHT, SPRM_P_DXA_LEFT, SPRM_P_DXA_FIRST,
    SPRM_P_DYA_LINE, SPRM_P_DYA_BEFORE, SPRM_P_DYA_AFTER,
    SPRM_P_IN_TABLE, SPRM_P_TABLE_ROW,
    SPRM_P_SHD,
    SPRM_P_BRC_TOP, SPRM_P_BRC_LEFT, SPRM_P_BRC_BOTTOM, SPRM_P_BRC_RIGHT,
    SPRM_P_BRC_BAR, SPRM_P_BETWEEN, SPRM_P_CHGTTABS, SPRM_P_OUTLINE_LVL,
}

_KNOWN_SEC_SPRMS = {
    SPRM_S_DXA_PAGE, SPRM_S_DYA_PAGE,
    SPRM_S_DXA_LEFT, SPRM_S_DXA_RIGHT,
    SPRM_S_DYA_TOP, SPRM_S_DYA_BOTTOM,
    SPRM_S_DYA_HDRTOP, SPRM_S_DYA_HDRBOTTOM,
    SPRM_S_ORIENT, SPRM_S_COLUMNS,
    SPRM_S_BREAK_TYPE, SPRM_S_COLS_SPACE,
}


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
        if sprm == SPRM_T_DEF_TABLE:
            if offset + 2 <= len(data):
                return struct.unpack_from("<H", data, offset)[0] + 2
            return 0
        else:
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
            operand = grpprl_bytes[offset:]
            results.append((sprm, operand))
            break

        operand = grpprl_bytes[offset : offset + op_size]
        offset += op_size
        results.append((sprm, operand))

    return results


def _encode_unknown_sprm(opcode: int, operand_hex: str) -> bytes:
    """Re-encode a preserved unknown SPRM from its hex operand."""
    try:
        opcode_int = int(opcode, 16) if isinstance(opcode, str) else int(opcode)
        operand_bytes = bytes.fromhex(operand_hex) if operand_hex else b""
        return struct.pack("<H", opcode_int) + operand_bytes
    except Exception:
        return b""


def decode_character_formatting(grpprl_bytes: bytes) -> Dict[str, Any]:
    """Decode character formatting GRPPRL into AST run properties.

    Unknown SPRMs are preserved in props['unknownSprms'] for lossless round-trip.
    """
    props: Dict[str, Any] = {}
    unknown: List[Dict[str, Any]] = []
    tokens = decode_grpprl(grpprl_bytes)

    for sprm, operand in tokens:
        handled = True
        if sprm == SPRM_C_BOLD and operand:
            props["bold"] = bool(operand[0])
        elif sprm == SPRM_C_ITALIC and operand:
            props["italic"] = bool(operand[0])
        elif sprm == SPRM_C_STRIKE and operand:
            props["strike"] = bool(operand[0])
        elif sprm == SPRM_C_OUTLINE and operand:
            props["outline"] = bool(operand[0])
        elif sprm == SPRM_C_SHADOW and operand:
            props["shadow"] = bool(operand[0])
        elif sprm == SPRM_C_SMALLCAPS and operand:
            props["smallCaps"] = bool(operand[0])
        elif sprm == SPRM_C_CAPS and operand:
            props["caps"] = bool(operand[0])
        elif sprm == SPRM_C_VANISH and operand:
            props["vanish"] = bool(operand[0])
        elif sprm == SPRM_C_KUL and operand:
            val = operand[0]
            kul_map = {0: "none", 1: "single", 2: "byWord", 3: "double",
                       4: "dotted", 5: "hidden", 6: "thick", 7: "dash",
                       8: "dotDash", 9: "dotDotDash", 10: "wave"}
            props["underline"] = kul_map.get(val, str(val))
        elif sprm == SPRM_C_HPS and len(operand) >= 2:
            half_pts = struct.unpack_from("<H", operand)[0]
            props["size"] = _half_points_to_pt(half_pts)
        elif sprm == SPRM_C_COLOR_CV and len(operand) >= 4:
            bgr = struct.unpack_from("<I", operand)[0]
            props["color"] = _bgr_to_hex(bgr)
        elif sprm == SPRM_C_COLOR and len(operand) >= 2:
            if len(operand) >= 4:
                bgr = struct.unpack_from("<I", operand)[0]
                props["color"] = _bgr_to_hex(bgr)
        elif sprm == SPRM_C_ISTD and len(operand) >= 2:
            props["styleIndex"] = struct.unpack_from("<H", operand)[0]
        elif sprm in (SPRM_C_FTC0, SPRM_C_FTC1, SPRM_C_FTC2) and len(operand) >= 2:
            font_idx = struct.unpack_from("<H", operand)[0]
            if sprm == SPRM_C_FTC0:
                props["fontIndex"] = font_idx
            elif sprm == SPRM_C_FTC1:
                props["fontIndexEA"] = font_idx
            elif sprm == SPRM_C_FTC2:
                props["fontIndexNFE"] = font_idx
        elif sprm == SPRM_C_COLOR_IDX and operand:
            props["colorIndex"] = operand[0]
        elif sprm == SPRM_C_HIGHLIGHT and operand:
            props["highlight"] = operand[0]
        elif sprm == SPRM_C_LANGUAGE and len(operand) >= 2:
            props["language"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_C_KERNING and len(operand) >= 2:
            props["kerning"] = struct.unpack_from("<H", operand)[0]
        else:
            handled = False

        if not handled:
            unknown.append({
                "opcode": hex(sprm),
                "operand": operand.hex(),
                "raw": base64.b64encode(struct.pack("<H", sprm) + operand).decode("ascii"),
            })

    if unknown:
        props["unknownSprms"] = unknown

    return props


def decode_paragraph_formatting(grpprl_bytes: bytes) -> Dict[str, Any]:
    """Decode paragraph formatting GRPPRL into AST paragraph properties.

    Unknown SPRMs are preserved in props['unknownSprms'] for lossless round-trip.
    """
    props: Dict[str, Any] = {}
    unknown: List[Dict[str, Any]] = []
    tokens = decode_grpprl(grpprl_bytes)

    for sprm, operand in tokens:
        handled = True
        if sprm == SPRM_P_JC and operand:
            jc = operand[0]
            align_map = {0: "left", 1: "center", 2: "right", 3: "both", 4: "thai", 5: "lowKashida"}
            props["align"] = align_map.get(jc, "left")
        elif sprm == SPRM_P_ISTD and len(operand) >= 2:
            props["styleIndex"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_P_DYA_BEFORE and len(operand) >= 2:
            props.setdefault("spacing", {})["before"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_P_DYA_AFTER and len(operand) >= 2:
            props.setdefault("spacing", {})["after"] = struct.unpack_from("<H", operand)[0]
        elif sprm == SPRM_P_DYA_LINE and len(operand) >= 4:
            dya_line = struct.unpack_from("<h", operand, 0)[0]
            f_mult = struct.unpack_from("<H", operand, 2)[0]
            sp = props.setdefault("spacing", {})
            sp["line"] = dya_line
            sp["lineRule"] = "auto" if f_mult else "exact"
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
        elif sprm == SPRM_P_TABLE_ROW and operand:
            props["tableRowTerminator"] = bool(operand[0])
        elif sprm == SPRM_P_KEEP and operand:
            props["keepLines"] = bool(operand[0])
        elif sprm == SPRM_P_KEEPNEXT and operand:
            props["keepWithNext"] = bool(operand[0])
        elif sprm == SPRM_P_PAGEBREAK and operand:
            props["pageBreakBefore"] = bool(operand[0])
        elif sprm == SPRM_P_OUTLINE_LVL and operand:
            props["outlineLevel"] = operand[0]
        elif sprm == SPRM_P_SHD and len(operand) >= 2:
            # SHD: 2-byte packed value (ico/icoPattern)
            shd_val = struct.unpack_from("<H", operand)[0]
            props["shading"] = {"raw": shd_val}
        elif sprm in (SPRM_P_BRC_TOP, SPRM_P_BRC_LEFT, SPRM_P_BRC_BOTTOM, SPRM_P_BRC_RIGHT,
                      SPRM_P_BRC_BAR, SPRM_P_BETWEEN):
            # BRC: variable-length border definition
            border_map = {
                SPRM_P_BRC_TOP: "top", SPRM_P_BRC_LEFT: "left",
                SPRM_P_BRC_BOTTOM: "bottom", SPRM_P_BRC_RIGHT: "right",
                SPRM_P_BRC_BAR: "bar", SPRM_P_BETWEEN: "between",
            }
            border_side = border_map[sprm]
            props.setdefault("borders", {})[border_side] = {
                "raw": operand.hex()
            }
        elif sprm == SPRM_P_CHGTTABS and operand:
            # Tab definition — preserve raw for faithful round-trip
            props["tabs"] = {"raw": operand.hex()}
        else:
            handled = False

        if not handled:
            unknown.append({
                "opcode": hex(sprm),
                "operand": operand.hex(),
                "raw": base64.b64encode(struct.pack("<H", sprm) + operand).decode("ascii"),
            })

    if unknown:
        props["unknownSprms"] = unknown

    return props


def decode_section_formatting(grpprl_bytes: bytes) -> Dict[str, Any]:
    """Decode section formatting GRPPRL into AST section properties.

    Unknown SPRMs are preserved in props['unknownSprms'] for lossless round-trip.
    """
    sec: Dict[str, Any] = {"page": {"margins": {}}}
    margins = sec["page"]["margins"]
    unknown: List[Dict[str, Any]] = []
    tokens = decode_grpprl(grpprl_bytes)

    for sprm, operand in tokens:
        handled = True
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
        elif sprm == SPRM_S_BREAK_TYPE and operand:
            # 0=continuous, 1=new column, 2=new page, 3=even, 4=odd
            break_map = {0: "continuous", 1: "column", 2: "nextPage", 3: "evenPage", 4: "oddPage"}
            sec["breakType"] = break_map.get(operand[0], str(operand[0]))
        elif sprm == SPRM_S_COLS_SPACE and len(operand) >= 2:
            sec["page"]["columnSpacing"] = struct.unpack_from("<H", operand)[0]
        else:
            handled = False

        if not handled:
            unknown.append({
                "opcode": hex(sprm),
                "operand": operand.hex(),
                "raw": base64.b64encode(struct.pack("<H", sprm) + operand).decode("ascii"),
            })

    if unknown:
        sec["unknownSprms"] = unknown

    return sec


# --------------------------------
# SPRM Encoder
# --------------------------------

def encode_character_formatting(
    props: Dict[str, Any],
    font_table: Optional[Dict[str, int]] = None,
    style_table: Optional[Dict[str, int]] = None,
) -> bytes:
    """Encode run formatting AST into character GRPPRL bytes.

    Preserves unknown SPRMs from 'unknownSprms' bucket for lossless round-trip.
    """
    out = bytearray()

    # Character style
    if "style" in props and style_table:
        s_name = str(props["style"])
        if s_name in style_table:
            out.extend(struct.pack("<HH", SPRM_C_ISTD, style_table[s_name]))
    elif "styleIndex" in props and props["styleIndex"] is not None:
        out.extend(struct.pack("<HH", SPRM_C_ISTD, int(props["styleIndex"])))

    if "bold" in props:
        out.extend(struct.pack("<HB", SPRM_C_BOLD, 1 if props["bold"] else 0))

    if "italic" in props:
        out.extend(struct.pack("<HB", SPRM_C_ITALIC, 1 if props["italic"] else 0))

    if "strike" in props:
        out.extend(struct.pack("<HB", SPRM_C_STRIKE, 1 if props["strike"] else 0))

    if "outline" in props:
        out.extend(struct.pack("<HB", SPRM_C_OUTLINE, 1 if props["outline"] else 0))

    if "shadow" in props:
        out.extend(struct.pack("<HB", SPRM_C_SHADOW, 1 if props["shadow"] else 0))

    if "smallCaps" in props:
        out.extend(struct.pack("<HB", SPRM_C_SMALLCAPS, 1 if props["smallCaps"] else 0))

    if "caps" in props:
        out.extend(struct.pack("<HB", SPRM_C_CAPS, 1 if props["caps"] else 0))

    if "vanish" in props:
        out.extend(struct.pack("<HB", SPRM_C_VANISH, 1 if props["vanish"] else 0))

    if "underline" in props:
        u_val = props["underline"]
        kul_rmap = {"none": 0, "single": 1, "byWord": 2, "double": 3,
                    "dotted": 4, "hidden": 5, "thick": 6, "dash": 7,
                    "dotDash": 8, "dotDotDash": 9, "wave": 10}
        if isinstance(u_val, bool):
            kul = 1 if u_val else 0
        elif isinstance(u_val, str):
            kul = kul_rmap.get(u_val, 1 if u_val not in ("none", "false") else 0)
        else:
            kul = int(u_val)
        out.extend(struct.pack("<HB", SPRM_C_KUL, kul))

    if "size" in props:
        pts = float(props["size"])
        half_pts = _pt_to_half_points(pts)
        out.extend(struct.pack("<HH", SPRM_C_HPS, half_pts))

    if "color" in props:
        color_str = str(props["color"]).strip()
        bgr = _hex_to_bgr(color_str)
        out.extend(struct.pack("<HI", SPRM_C_COLOR_CV, bgr))

    if "colorIndex" in props:
        out.extend(struct.pack("<HB", SPRM_C_COLOR_IDX, int(props["colorIndex"])))

    if "highlight" in props:
        out.extend(struct.pack("<HB", SPRM_C_HIGHLIGHT, int(props["highlight"])))

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

    if "fontIndexEA" in props and props["fontIndexEA"] is not None:
        try:
            out.extend(struct.pack("<HH", SPRM_C_FTC1, int(props["fontIndexEA"])))
        except (ValueError, TypeError):
            pass

    if "fontIndexNFE" in props and props["fontIndexNFE"] is not None:
        try:
            out.extend(struct.pack("<HH", SPRM_C_FTC2, int(props["fontIndexNFE"])))
        except (ValueError, TypeError):
            pass

    if "language" in props:
        out.extend(struct.pack("<HH", SPRM_C_LANGUAGE, int(props["language"])))

    if "kerning" in props:
        out.extend(struct.pack("<HH", SPRM_C_KERNING, int(props["kerning"])))

    # Re-emit unknown SPRMs verbatim (lossless round-trip)
    for unk in props.get("unknownSprms", []):
        try:
            opcode_int = int(unk["opcode"], 16) if isinstance(unk["opcode"], str) else int(unk["opcode"])
            operand_bytes = bytes.fromhex(unk.get("operand", ""))
            out.extend(struct.pack("<H", opcode_int))
            out.extend(operand_bytes)
        except Exception:
            # If raw base64 available, use that as fallback
            raw_b64 = unk.get("raw", "")
            if raw_b64:
                try:
                    out.extend(base64.b64decode(raw_b64))
                except Exception:
                    pass

    return bytes(out)


def encode_paragraph_formatting(
    props: Dict[str, Any],
    style_table: Optional[Dict[str, int]] = None,
) -> bytes:
    """Encode paragraph formatting AST into paragraph GRPPRL bytes.

    Preserves unknown SPRMs from 'unknownSprms' bucket for lossless round-trip.
    """
    out = bytearray()

    # Style
    if "style" in props and style_table:
        s_name = str(props["style"])
        if s_name in style_table:
            out.extend(struct.pack("<HH", SPRM_P_ISTD, style_table[s_name]))
    elif "styleIndex" in props and props["styleIndex"] is not None:
        out.extend(struct.pack("<HH", SPRM_P_ISTD, int(props["styleIndex"])))

    # Alignment
    if "align" in props:
        al = _normalize_alignment(props["align"])
        jc_map = {"left": 0, "center": 1, "right": 2, "both": 3, "thai": 4, "lowKashida": 5}
        out.extend(struct.pack("<HB", SPRM_P_JC, jc_map.get(al, 0)))

    # Spacing
    spacing = props.get("spacing")
    if isinstance(spacing, dict):
        if "before" in spacing:
            out.extend(struct.pack("<HH", SPRM_P_DYA_BEFORE, int(spacing["before"])))
        if "after" in spacing:
            out.extend(struct.pack("<HH", SPRM_P_DYA_AFTER, int(spacing["after"])))
        if "line" in spacing:
            dya = int(spacing["line"])
            f_mult = 1 if spacing.get("lineRule", "auto") == "auto" else 0
            out.extend(struct.pack("<HhH", SPRM_P_DYA_LINE, dya, f_mult))

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
    if "pageBreakBefore" in props:
        out.extend(struct.pack("<HB", SPRM_P_PAGEBREAK, 1 if props["pageBreakBefore"] else 0))

    # Outline level
    if "outlineLevel" in props:
        out.extend(struct.pack("<HB", SPRM_P_OUTLINE_LVL, int(props["outlineLevel"])))

    # In Table
    if props.get("inTable"):
        out.extend(struct.pack("<HB", SPRM_P_IN_TABLE, 1))
    if props.get("tableRowTerminator"):
        out.extend(struct.pack("<HB", SPRM_P_TABLE_ROW, 1))

    # Shading (raw 2-byte value)
    shading = props.get("shading")
    if isinstance(shading, dict) and "raw" in shading:
        try:
            out.extend(struct.pack("<HH", SPRM_P_SHD, int(shading["raw"])))
        except Exception:
            pass

    # Borders (raw hex preserved)
    borders = props.get("borders")
    if isinstance(borders, dict):
        border_sprm_map = {
            "top": SPRM_P_BRC_TOP, "left": SPRM_P_BRC_LEFT,
            "bottom": SPRM_P_BRC_BOTTOM, "right": SPRM_P_BRC_RIGHT,
            "bar": SPRM_P_BRC_BAR, "between": SPRM_P_BETWEEN,
        }
        for side, sprm_code in border_sprm_map.items():
            b_item = borders.get(side)
            if isinstance(b_item, dict) and "raw" in b_item:
                try:
                    b_bytes = bytes.fromhex(b_item["raw"])
                    out.extend(struct.pack("<H", sprm_code))
                    out.extend(b_bytes)
                except Exception:
                    pass

    # Tabs (raw hex preserved)
    tabs = props.get("tabs")
    if isinstance(tabs, dict) and "raw" in tabs:
        try:
            t_bytes = bytes.fromhex(tabs["raw"])
            out.extend(struct.pack("<HB", SPRM_P_CHGTTABS, len(t_bytes)))
            out.extend(t_bytes)
        except Exception:
            pass

    # Re-emit unknown SPRMs verbatim (lossless round-trip)
    for unk in props.get("unknownSprms", []):
        try:
            opcode_int = int(unk["opcode"], 16) if isinstance(unk["opcode"], str) else int(unk["opcode"])
            operand_bytes = bytes.fromhex(unk.get("operand", ""))
            out.extend(struct.pack("<H", opcode_int))
            out.extend(operand_bytes)
        except Exception:
            raw_b64 = unk.get("raw", "")
            if raw_b64:
                try:
                    out.extend(base64.b64decode(raw_b64))
                except Exception:
                    pass

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

    if "columns" in page:
        out.extend(struct.pack("<HH", SPRM_S_COLUMNS, int(page["columns"])))

    if "columnSpacing" in page:
        out.extend(struct.pack("<HH", SPRM_S_COLS_SPACE, int(page["columnSpacing"])))

    # Section break type
    break_type = props.get("breakType")
    if break_type is not None:
        break_rmap = {"continuous": 0, "column": 1, "nextPage": 2, "evenPage": 3, "oddPage": 4}
        if isinstance(break_type, str):
            bkc = break_rmap.get(break_type, 2)
        else:
            bkc = int(break_type)
        out.extend(struct.pack("<HB", SPRM_S_BREAK_TYPE, bkc))

    # Re-emit unknown SPRMs
    for unk in props.get("unknownSprms", []):
        try:
            opcode_int = int(unk["opcode"], 16) if isinstance(unk["opcode"], str) else int(unk["opcode"])
            operand_bytes = bytes.fromhex(unk.get("operand", ""))
            out.extend(struct.pack("<H", opcode_int))
            out.extend(operand_bytes)
        except Exception:
            raw_b64 = unk.get("raw", "")
            if raw_b64:
                try:
                    out.extend(base64.b64decode(raw_b64))
                except Exception:
                    pass

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
