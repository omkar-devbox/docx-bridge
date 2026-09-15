"""Common data coercion and dictionary helpers for document handlers."""

from typing import Any


def to_number(value: Any) -> int | float | str | None:
    """Coerce value to integer or float if possible, else return string/None."""
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    # Check for integer (handles negative and positive integers)
    if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        return int(s)

    # Check for float
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
        # Word .doc SPRM values: 0=left, 1=center, 2=right, 3=both
        doc_map = {0: "left", 1: "center", 2: "right", 3: "both"}
        return doc_map.get(int_val, "left")

    return ALIGNMENT_MAP.get(str(align).strip().lower(), "left")


__all__ = [
    "to_number",
    "to_bool",
    "clean_dict",
    "normalize_alignment",
    "ALIGNMENT_MAP",
]
