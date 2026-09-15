"""Common color conversion utilities for document processing.

Handles conversion between BGR integers (Word .doc COLORREF format),
RGB hexadecimal strings (OpenXML .docx / JSON AST format), and RGB tuples.
"""

from typing import Tuple


def bgr_to_hex(bgr_val: int) -> str:
    """Convert a 32-bit BGR integer (Word .doc COLORREF) to a 6-digit uppercase Hex RGB string.

    Format of 0x00BBGGRR:
    - Red is in lowest byte (0x0000FF)
    - Green is in middle byte (0x00FF00)
    - Blue is in highest byte (0xFF0000)
    """
    if bgr_val is None or bgr_val < 0:
        return "auto"

    r = bgr_val & 0xFF
    g = (bgr_val >> 8) & 0xFF
    b = (bgr_val >> 16) & 0xFF
    return f"{r:02X}{g:02X}{b:02X}"


def hex_to_bgr(hex_str: str) -> int:
    """Convert a 6-digit Hex RGB string to a 32-bit BGR integer (Word .doc COLORREF)."""
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


__all__ = [
    "bgr_to_hex",
    "hex_to_bgr",
    "hex_to_rgb",
    "rgb_to_hex",
    "normalize_hex_color",
]
