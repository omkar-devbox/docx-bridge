"""Common unit conversion utilities for document processing.

Shared conversions between twips (dxa), points (pt), half-points,
eighth-points, EMUs (English Metric Units), inches, and centimeters.
"""

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
# Twips / DXA Conversions
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


# --------------------------------
# EMU Conversions
# --------------------------------

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


# --------------------------------
# Font Size & Border Fractions
# --------------------------------

def half_points_to_pt(half_pts: int | float) -> float:
    """Convert half-points (standard font size unit in doc/docx) to points."""
    return float(half_pts) / HALF_POINTS_PER_PT


def pt_to_half_points(pt: int | float) -> int:
    """Convert points to half-points."""
    return round(float(pt) * HALF_POINTS_PER_PT)


def eighth_points_to_pt(eighth_pts: int | float) -> float:
    """Convert eighth-points (border width unit in doc/docx) to points."""
    return float(eighth_pts) / EIGHTH_POINTS_PER_PT


def pt_to_eighth_points(pt: int | float) -> int:
    """Convert points to eighth-points."""
    return round(float(pt) * EIGHTH_POINTS_PER_PT)


__all__ = [
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
]
