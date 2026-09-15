# --------------------------------
# Imports
# --------------------------------

import zipfile
from pathlib import Path
from typing import BinaryIO


# --------------------------------
# DOCX Writer
# --------------------------------

class DocxWriter:

    def __init__(self, target: str | Path | BinaryIO):
        self.target = target
        self.archive = zipfile.ZipFile(
            target,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        )

    # --------------------------------
    # Write Parts
    # --------------------------------

    def write_part(
        self,
        part_name: str,
        content: bytes | str,
    ) -> None:
        if isinstance(content, str):
            content = content.encode("utf-8")

        self.archive.writestr(
            part_name,
            content,
        )

    # --------------------------------
    # Archive Lifecycle
    # --------------------------------

    def close(self) -> None:
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        self.close()