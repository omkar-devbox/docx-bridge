from pathlib import Path
from typing import Any
import base64
import json
import os


# -------------------------------------------------
# Default Fallbacks (when config is loading)
# -------------------------------------------------
DEFAULT_JSON_INDENT: int = 2
DEFAULT_JSON_ENSURE_ASCII: bool = False
DEFAULT_JSON_ENCODING: str = "utf-8"


def _get_json_config() -> dict[str, Any]:
    """Retrieve JSON settings from active DOCX configuration."""
    try:
        from config import JSON_CONFIG
        return JSON_CONFIG
    except (ImportError, AttributeError):
        return {}


# -------------------------------------------------
# Serialization Helper
# -------------------------------------------------
def _json_default(obj: Any) -> str:
    if isinstance(obj, (bytes, bytearray)):
        return base64.b64encode(obj).decode("ascii")
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


# -------------------------------------------------
# Load JSON File
# -------------------------------------------------
def load_json(
    filepath: Path | str,
    encoding: str | None = None,
    json_config: dict[str, Any] | None = None,
) -> Any:
    """Read and deserialize JSON data from file using configuration defaults."""
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    cfg = json_config if json_config is not None else _get_json_config()
    enc = encoding or cfg.get("encoding") or DEFAULT_JSON_ENCODING

    with open(filepath, "r", encoding=enc) as file:
        return json.load(file)


# -------------------------------------------------
# Save JSON File
# -------------------------------------------------
def save_json(
    data: Any,
    filepath: Path | str,
    indent: int | None = None,
    ensure_ascii: bool | None = None,
    encoding: str | None = None,
    json_config: dict[str, Any] | None = None,
) -> None:
    """Serialize and write JSON data to file using configuration settings."""
    filepath = Path(filepath)

    directory = filepath.parent
    if directory:
        directory.mkdir(parents=True, exist_ok=True)

    cfg = json_config if json_config is not None else _get_json_config()
    ind = indent if indent is not None else cfg.get("indent", DEFAULT_JSON_INDENT)
    ascii_flag = (
        ensure_ascii
        if ensure_ascii is not None
        else cfg.get("ensure_ascii", DEFAULT_JSON_ENSURE_ASCII)
    )
    enc = encoding or cfg.get("encoding") or DEFAULT_JSON_ENCODING

    with open(filepath, "w", encoding=enc) as file:
        json.dump(
            data,
            file,
            indent=ind,
            ensure_ascii=ascii_flag,
            default=_json_default,
        )


# Alias dump_json to save_json for compatibility
dump_json = save_json

__all__ = [
    "load_json",
    "save_json",
    "dump_json",
]