"""Common data coercion, alignment, unit, and color helpers for document handlers."""

from typing import Any, Tuple

# --------------------------------
# Unit Conversion Constants
# --------------------------------

DXA_PER_INCH: int = 1440
DXA_PER_CM: int = 567
DXA_PER_PT: int = 20

EMUS_PER_INCH: int = 914400
EMUS_PER_CM: int = 360000
EMUS_PER_PT: int = 12700
EMUS_PER_DXA: int = 635

HALF_POINTS_PER_PT: int = 2
EIGHTH_POINTS_PER_PT: int = 8


# --------------------------------
# Unit Conversions
# --------------------------------

def dxa_to_pt(dxa: int | float) -> float:
    """Convert dxa (twips) to points."""
    return float(dxa) / DXA_PER_PT


def pt_to_dxa(pt: int | float) -> int:
    """Convert points to dxa (twips)."""
    return round(float(pt) * DXA_PER_PT)


def inches_to_dxa(inches: int | float) -> int:
    """Convert inches to dxa (twips)."""
    return round(float(inches) * DXA_PER_INCH)


def dxa_to_inches(dxa: int | float) -> float:
    """Convert dxa (twips) to inches."""
    return float(dxa) / DXA_PER_INCH


def cm_to_dxa(cm: int | float) -> int:
    """Convert centimeters to dxa (twips)."""
    return round(float(cm) * DXA_PER_CM)


def dxa_to_cm(dxa: int | float) -> float:
    """Convert dxa (twips) to centimeters."""
    return float(dxa) / DXA_PER_CM


def emu_to_dxa(emu: int | float) -> int:
    """Convert EMUs to dxa (twips)."""
    return round(float(emu) / EMUS_PER_DXA)


def dxa_to_emu(dxa: int | float) -> int:
    """Convert dxa (twips) to EMUs."""
    return round(float(dxa) * EMUS_PER_DXA)


def emu_to_pt(emu: int | float) -> float:
    """Convert EMUs to points."""
    return float(emu) / EMUS_PER_PT


def pt_to_emu(pt: int | float) -> int:
    """Convert points to EMUs."""
    return round(float(pt) * EMUS_PER_PT)


def inches_to_emu(inches: int | float) -> int:
    """Convert inches to EMUs."""
    return round(float(inches) * EMUS_PER_INCH)


def emu_to_inches(emu: int | float) -> float:
    """Convert EMUs to inches."""
    return float(emu) / EMUS_PER_INCH


def half_points_to_pt(half_pts: int | float) -> float:
    """Convert half-points to points."""
    return float(half_pts) / HALF_POINTS_PER_PT


def pt_to_half_points(pt: int | float) -> int:
    """Convert points to half-points."""
    return round(float(pt) * HALF_POINTS_PER_PT)


def eighth_points_to_pt(eighth_pts: int | float) -> float:
    """Convert eighth-points to points."""
    return float(eighth_pts) / EIGHTH_POINTS_PER_PT


def pt_to_eighth_points(pt: int | float) -> int:
    """Convert points to eighth-points."""
    return round(float(pt) * EIGHTH_POINTS_PER_PT)


# --------------------------------
# Color Conversions
# --------------------------------

def bgr_to_hex(bgr_val: int) -> str:
    """Convert a 32-bit BGR integer to a 6-digit uppercase Hex RGB string."""
    if bgr_val is None or bgr_val < 0:
        return "auto"

    r = bgr_val & 0xFF
    g = (bgr_val >> 8) & 0xFF
    b = (bgr_val >> 16) & 0xFF
    return f"{r:02X}{g:02X}{b:02X}"


def hex_to_bgr(hex_str: str) -> int:
    """Convert a 6-digit Hex RGB string to a 32-bit BGR integer."""
    if not hex_str or hex_str.lower() in ("auto", "none"):
        return 0

    clean_hex = hex_str.lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join([c * 2 for c in clean_hex])

    if len(clean_hex) != 6:
        return 0

    try:
        r = int(clean_hex[0:2], 16)
        g = int(clean_hex[2:4], 16)
        b = int(clean_hex[4:6], 16)
        return (b << 16) | (g << 8) | r
    except ValueError:
        return 0


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert a 6-digit Hex RGB string to an (R, G, B) tuple of ints (0-255)."""
    clean_hex = hex_str.lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join([c * 2 for c in clean_hex])
    if len(clean_hex) != 6:
        return (0, 0, 0)
    try:
        return (
            int(clean_hex[0:2], 16),
            int(clean_hex[2:4], 16),
            int(clean_hex[4:6], 16),
        )
    except ValueError:
        return (0, 0, 0)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers (0-255) to a 6-digit uppercase Hex RGB string."""
    r_clamped = max(0, min(255, int(r)))
    g_clamped = max(0, min(255, int(g)))
    b_clamped = max(0, min(255, int(b)))
    return f"{r_clamped:02X}{g_clamped:02X}{b_clamped:02X}"


def normalize_hex_color(color_val: str | None) -> str | None:
    """Normalize color strings (stripping '#', resolving 'auto', ensuring 6 digits)."""
    if not color_val:
        return None
    val = color_val.strip()
    if val.lower() in ("auto", "none"):
        return val.lower()
    val = val.lstrip("#")
    if len(val) == 3:
        val = "".join([c * 2 for c in val])
    if len(val) == 6:
        return val.upper()
    return color_val


# --------------------------------
# General Helpers
# --------------------------------

def to_number(value: Any) -> int | float | str | None:
    """Coerce value to integer or float if possible, else return string/None."""
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        return int(s)

    try:
        f = float(s)
        return f
    except ValueError:
        return s


def to_bool(value: Any) -> bool:
    """Evaluate truthiness across XML strings, numbers, and bools."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0

    s = str(value).strip().lower()
    return s not in ("0", "false", "off", "none", "no", "")


def clean_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove empty dictionaries, None values, and empty lists."""
    cleaned = {}
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, dict):
            sub = clean_dict(v)
            if sub:
                cleaned[k] = sub
        elif isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, dict):
                    c = clean_dict(item)
                    if c:
                        new_list.append(c)
                elif item is not None:
                    new_list.append(item)
            if new_list:
                cleaned[k] = new_list
        else:
            cleaned[k] = v
    return cleaned


ALIGNMENT_MAP = {
    "left": "left",
    "center": "center",
    "right": "right",
    "both": "both",
    "justify": "both",
    "start": "left",
    "end": "right",
}


def normalize_alignment(align: str | int | None) -> str:
    """Normalize paragraph or table alignment to canonical AST string."""
    if align is None:
        return "left"

    if isinstance(align, int) or (isinstance(align, str) and align.isdigit()):
        int_val = int(align)
        doc_map = {0: "left", 1: "center", 2: "right", 3: "both"}
        return doc_map.get(int_val, "left")

    return ALIGNMENT_MAP.get(str(align).strip().lower(), "left")


__all__ = [
    # Data coercion
    "to_number",
    "to_bool",
    "clean_dict",
    "normalize_alignment",
    "ALIGNMENT_MAP",
    # Units
    "DXA_PER_INCH",
    "DXA_PER_CM",
    "DXA_PER_PT",
    "EMUS_PER_INCH",
    "EMUS_PER_CM",
    "EMUS_PER_PT",
    "EMUS_PER_DXA",
    "HALF_POINTS_PER_PT",
    "EIGHTH_POINTS_PER_PT",
    "dxa_to_pt",
    "pt_to_dxa",
    "inches_to_dxa",
    "dxa_to_inches",
    "cm_to_dxa",
    "dxa_to_cm",
    "emu_to_dxa",
    "dxa_to_emu",
    "emu_to_pt",
    "pt_to_emu",
    "inches_to_emu",
    "emu_to_inches",
    "half_points_to_pt",
    "pt_to_half_points",
    "eighth_points_to_pt",
    "pt_to_eighth_points",
    # Color
    "bgr_to_hex",
    "hex_to_bgr",
    "hex_to_rgb",
    "rgb_to_hex",
    "normalize_hex_color",
]
