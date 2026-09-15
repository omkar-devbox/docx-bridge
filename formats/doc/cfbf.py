"""Compound File Binary Format (CFBF / OLE) implementation in pure Python.

Implements the [MS-CFB] v3 and v4 specifications without external libraries.
Supports reading and writing structured storage files containing streams and directories.
"""

from __future__ import annotations

import io
import math
import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple, Union

# --------------------------------
# Constants & Magic Identifiers
# --------------------------------

CFB_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
LITTLE_ENDIAN = 0xFFFE

# Major Versions
VERSION_3 = 0x0003  # 512-byte sectors
VERSION_4 = 0x0004  # 4096-byte sectors

# Sector Allocations & Special IDs
MAXREGSECT = 0xFFFFFFFA
DIFSECT = 0xFFFFFFFC
FATSECT = 0xFFFFFFFD
ENDOFCHAIN = 0xFFFFFFFE
FREESECT = 0xFFFFFFFF

# Directory Entry IDs
NOSTREAM = 0xFFFFFFFF

# Object Types
STGTY_INVALID = 0
STGTY_STORAGE = 1
STGTY_STREAM = 2
STGTY_LOCKBYTES = 3
STGTY_PROPERTY = 4
STGTY_ROOT = 5

# Color Flags (for Red-Black tree)
COLOR_RED = 0
COLOR_BLACK = 1

# Standard Cutoffs
MINI_STREAM_CUTOFF = 4096


# --------------------------------
# Helpers: FileTime & Strings
# --------------------------------

def filetime_to_datetime(ft: int) -> Optional[datetime]:
    """Convert Windows 64-bit FILETIME (100ns intervals since 1601-01-01) to UTC datetime."""
    if ft <= 0:
        return None
    try:
        epoch_diff = 116444736000000000
        unix_timestamp = (ft - epoch_diff) / 10000000.0
        return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    except Exception:
        return None


def datetime_to_filetime(dt: Optional[datetime]) -> int:
    """Convert datetime to Windows 64-bit FILETIME."""
    if not dt:
        return 0
    epoch_diff = 116444736000000000
    timestamp = dt.timestamp()
    return int(timestamp * 10000000.0) + epoch_diff


# --------------------------------
# Directory Entry Model
# --------------------------------

@dataclass
class DirectoryEntry:
    """A 128-byte CFBF directory entry."""

    index: int = 0
    name: str = ""
    entry_type: int = STGTY_STREAM
    color: int = COLOR_BLACK
    left_sibling: int = NOSTREAM
    right_sibling: int = NOSTREAM
    child: int = NOSTREAM
    clsid: bytes = b"\x00" * 16
    state_bits: int = 0
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    start_sector: int = ENDOFCHAIN
    size: int = 0

    # Hierarchical tree links
    children: List[DirectoryEntry] = field(default_factory=list)
    parent: Optional[DirectoryEntry] = None

    @classmethod
    def parse(cls, data: bytes, index: int) -> DirectoryEntry:
        """Parse a 128-byte directory entry."""
        if len(data) < 128:
            raise ValueError(f"Directory entry must be 128 bytes, got {len(data)}")

        raw_name = data[0:64]
        name_len = struct.unpack_from("<H", data, 64)[0]
        entry_type = data[66]
        color = data[67]
        left_sib = struct.unpack_from("<I", data, 68)[0]
        right_sib = struct.unpack_from("<I", data, 72)[0]
        child = struct.unpack_from("<I", data, 76)[0]
        clsid = data[80:96]
        state_bits = struct.unpack_from("<I", data, 96)[0]
        create_time = struct.unpack_from("<Q", data, 100)[0]
        modify_time = struct.unpack_from("<Q", data, 108)[0]
        start_sect = struct.unpack_from("<I", data, 116)[0]
        size = struct.unpack_from("<Q", data, 120)[0]

        # Name is UTF-16LE, including a null terminator
        name = ""
        if name_len > 2:
            try:
                name = raw_name[: name_len - 2].decode("utf-16le")
            except Exception:
                name = raw_name[:64].decode("latin-1", errors="ignore").rstrip("\x00")

        return cls(
            index=index,
            name=name,
            entry_type=entry_type,
            color=color,
            left_sibling=left_sib,
            right_sibling=right_sib,
            child=child,
            clsid=clsid,
            state_bits=state_bits,
            created=filetime_to_datetime(create_time),
            modified=filetime_to_datetime(modify_time),
            start_sector=start_sect,
            size=size,
        )

    def to_bytes(self) -> bytes:
        """Serialize entry to 128 bytes."""
        encoded_name = (self.name + "\x00").encode("utf-16le")
        if len(encoded_name) > 64:
            encoded_name = encoded_name[:64]
        name_bytes = encoded_name.ljust(64, b"\x00")
        name_len = len(encoded_name)

        create_ft = datetime_to_filetime(self.created)
        modify_ft = datetime_to_filetime(self.modified)

        return struct.pack(
            "<64sHBBIII16sIQQIQ",
            name_bytes,
            name_len,
            self.entry_type,
            self.color,
            self.left_sibling,
            self.right_sibling,
            self.child,
            self.clsid if len(self.clsid) == 16 else b"\x00" * 16,
            self.state_bits,
            create_ft,
            modify_ft,
            self.start_sector,
            self.size,
        )


# --------------------------------
# CFBF Reader
# --------------------------------

class CFBReader:
    """Reader for Compound File Binary Format (.doc, .xls, .ppt, OLE)."""

    def __init__(self, source: Union[str, Path, BinaryIO, bytes]):
        self._close_stream = False
        if isinstance(source, (str, Path)):
            self._stream: BinaryIO = open(source, "rb")
            self._close_stream = True
        elif isinstance(source, bytes):
            self._stream = io.BytesIO(source)
        else:
            self._stream = source

        self._read_header()
        self._read_difat()
        self._read_fat()
        self._read_directory()
        self._read_minifat()

    def close(self) -> None:
        if self._close_stream and self._stream and not self._stream.closed:
            self._stream.close()

    def __enter__(self) -> CFBReader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # --------------------------------
    # Header & Allocation Tables
    # --------------------------------

    def _read_header(self) -> None:
        self._stream.seek(0)
        hdr = self._stream.read(512)
        if len(hdr) < 512:
            raise ValueError("File is smaller than 512-byte CFBF header")

        sig = hdr[0:8]
        if sig != CFB_SIGNATURE:
            raise ValueError(f"Invalid CFBF signature: {sig!r}")

        byte_order = struct.unpack_from("<H", hdr, 28)[0]
        if byte_order != LITTLE_ENDIAN:
            raise ValueError(f"Unsupported byte order: {hex(byte_order)}")

        self.sector_shift = struct.unpack_from("<H", hdr, 30)[0]
        self.mini_sector_shift = struct.unpack_from("<H", hdr, 32)[0]
        self.sector_size = 1 << self.sector_shift
        self.mini_sector_size = 1 << self.mini_sector_shift

        self.num_dir_sectors = struct.unpack_from("<I", hdr, 40)[0]
        self.num_fat_sectors = struct.unpack_from("<I", hdr, 44)[0]
        self.first_dir_sector = struct.unpack_from("<I", hdr, 48)[0]
        self.mini_cutoff = struct.unpack_from("<I", hdr, 56)[0]
        self.first_minifat_sector = struct.unpack_from("<I", hdr, 60)[0]
        self.num_minifat_sectors = struct.unpack_from("<I", hdr, 64)[0]
        self.first_difat_sector = struct.unpack_from("<I", hdr, 68)[0]
        self.num_difat_sectors = struct.unpack_from("<I", hdr, 72)[0]

        # 109 initial DIFAT entries in header (bytes 76 to 512)
        self.difat_entries: List[int] = list(struct.unpack_from("<109I", hdr, 76))

    def _read_difat(self) -> None:
        """Read any additional DIFAT sectors beyond the 109 header entries."""
        self.fat_sector_locations: List[int] = [
            s for s in self.difat_entries if s < MAXREGSECT
        ]

        curr_difat = self.first_difat_sector
        entries_per_sector = (self.sector_size // 4) - 1  # Last entry is next DIFAT sector

        for _ in range(self.num_difat_sectors):
            if curr_difat >= MAXREGSECT:
                break
            difat_data = self._read_sector(curr_difat)
            entries = struct.unpack(f"<{self.sector_size // 4}I", difat_data)
            for s in entries[:entries_per_sector]:
                if s < MAXREGSECT:
                    self.fat_sector_locations.append(s)
            curr_difat = entries[entries_per_sector]

    def _read_sector(self, sector_id: int) -> bytes:
        """Read a regular sector by 0-based sector ID (offset is 512 + sector_id * sector_size)."""
        offset = 512 + (sector_id * self.sector_size)
        self._stream.seek(offset)
        data = self._stream.read(self.sector_size)
        if len(data) < self.sector_size:
            data = data.ljust(self.sector_size, b"\x00")
        return data

    def _read_fat(self) -> None:
        """Read full FAT chain table."""
        self.fat: List[int] = []
        uint32s_per_sector = self.sector_size // 4

        for fat_sector in self.fat_sector_locations:
            sector_bytes = self._read_sector(fat_sector)
            self.fat.extend(struct.unpack(f"<{uint32s_per_sector}I", sector_bytes))

    def _get_chain(self, start_sector: int) -> List[int]:
        """Follow FAT chain for regular streams."""
        chain = []
        curr = start_sector
        visited = set()
        while curr < MAXREGSECT and curr not in visited:
            visited.add(curr)
            chain.append(curr)
            if curr >= len(self.fat):
                break
            curr = self.fat[curr]
        return chain

    def _get_mini_chain(self, start_sector: int) -> List[int]:
        """Follow MiniFAT chain for small streams."""
        chain = []
        curr = start_sector
        visited = set()
        while curr < MAXREGSECT and curr not in visited:
            visited.add(curr)
            chain.append(curr)
            if curr >= len(self.minifat):
                break
            curr = self.minifat[curr]
        return chain

    # --------------------------------
    # Directory & Tree Construction
    # --------------------------------

    def _read_directory(self) -> None:
        """Read directory sectors and reconstruct hierarchy."""
        dir_chain = self._get_chain(self.first_dir_sector)
        dir_bytes = b"".join(self._read_sector(s) for s in dir_chain)

        self.entries: List[DirectoryEntry] = []
        num_entries = len(dir_bytes) // 128

        for i in range(num_entries):
            entry_data = dir_bytes[i * 128 : (i + 1) * 128]
            entry = DirectoryEntry.parse(entry_data, i)
            self.entries.append(entry)

        # Build directory tree starting with Root Entry (index 0)
        self.root = self.entries[0] if self.entries else None
        if self.root:
            self._build_tree(self.root)

        # Fast lookup mapping: full path / name -> DirectoryEntry
        self._entry_map: Dict[str, DirectoryEntry] = {}
        for entry in self.entries:
            if entry.entry_type in (STGTY_STREAM, STGTY_STORAGE, STGTY_ROOT) and entry.name:
                self._entry_map[entry.name] = entry

    def _build_tree(self, parent: DirectoryEntry) -> None:
        """Traverse child binary tree and attach child entries."""
        if parent.child == NOSTREAM or parent.child >= len(self.entries):
            return

        def visit(node_id: int):
            if node_id == NOSTREAM or node_id >= len(self.entries):
                return
            node = self.entries[node_id]
            node.parent = parent
            parent.children.append(node)
            visit(node.left_sibling)
            visit(node.right_sibling)
            if node.entry_type in (STGTY_STORAGE, STGTY_ROOT):
                self._build_tree(node)

        visit(parent.child)

    def _read_minifat(self) -> None:
        """Read MiniFAT and load MiniStream from Root Entry."""
        self.minifat: List[int] = []
        if self.first_minifat_sector < MAXREGSECT:
            minifat_chain = self._get_chain(self.first_minifat_sector)
            uint32s = self.sector_size // 4
            for s in minifat_chain:
                sector_bytes = self._read_sector(s)
                self.minifat.extend(struct.unpack(f"<{uint32s}I", sector_bytes))

        # Root entry holds the MiniStream data
        self._ministream_data = b""
        if self.root and self.root.start_sector < MAXREGSECT and self.root.size > 0:
            root_chain = self._get_chain(self.root.start_sector)
            raw = b"".join(self._read_sector(s) for s in root_chain)
            self._ministream_data = raw[: self.root.size]

    # --------------------------------
    # Public Stream Operations
    # --------------------------------

    def list_streams(self) -> List[str]:
        """List all stream names in the compound file."""
        return [
            e.name
            for e in self.entries
            if e.entry_type == STGTY_STREAM and e.name
        ]

    def has_stream(self, name: str) -> bool:
        """Check if a stream exists."""
        return name in self._entry_map and self._entry_map[name].entry_type == STGTY_STREAM

    def get_entry(self, name: str) -> Optional[DirectoryEntry]:
        """Get directory entry by stream name."""
        return self._entry_map.get(name)

    def read_stream(self, name: str) -> bytes:
        """Read full stream content as bytes."""
        entry = self._entry_map.get(name)
        if not entry:
            raise KeyError(f"Stream '{name}' not found in CFBF file. Available: {self.list_streams()}")
        if entry.entry_type != STGTY_STREAM:
            raise ValueError(f"Entry '{name}' is not a stream (type={entry.entry_type})")

        if entry.size == 0:
            return b""

        # Check if stream is in MiniStream (< cutoff size, usually 4096 bytes)
        if entry.size < self.mini_cutoff and entry.start_sector < MAXREGSECT:
            mini_chain = self._get_mini_chain(entry.start_sector)
            chunks = []
            for ms in mini_chain:
                offset = ms * self.mini_sector_size
                chunks.append(self._ministream_data[offset : offset + self.mini_sector_size])
            return b"".join(chunks)[: entry.size]

        # Regular stream via FAT sectors
        chain = self._get_chain(entry.start_sector)
        chunks = [self._read_sector(s) for s in chain]
        return b"".join(chunks)[: entry.size]


# --------------------------------
# CFBF Writer
# --------------------------------

class CFBWriter:
    """Writer for creating valid Compound File Binary Format (CFBF / OLE) files."""

    def __init__(self, target: Union[str, Path, BinaryIO]):
        self._target = target
        self._streams: Dict[str, bytes] = {}
        self._sector_size = 512
        self._mini_sector_size = 64
        self._mini_cutoff = 4096

    def write_stream(self, name: str, content: bytes) -> None:
        """Register a stream to write into the compound document."""
        self._streams[name] = bytes(content)

    def set_streams(self, streams: Dict[str, bytes]) -> None:
        """Batch set streams."""
        for k, v in streams.items():
            self.write_stream(k, v)

    def save(self) -> None:
        """Build and write the CFBF archive to destination target."""
        raw_bytes = self.build()
        if isinstance(self._target, (str, Path)):
            with open(self._target, "wb") as f:
                f.write(raw_bytes)
        else:
            self._target.seek(0)
            self._target.write(raw_bytes)
            self._target.truncate()

    def build(self) -> bytes:
        """Assemble all registered streams into a valid CFBF v3 binary byte array."""
        sector_size = self._sector_size
        mini_sector_size = self._mini_sector_size

        # Separate regular streams from mini streams
        mini_streams: Dict[str, bytes] = {}
        regular_streams: Dict[str, bytes] = {}

        for name, data in self._streams.items():
            if len(data) < self._mini_cutoff and len(data) > 0:
                mini_streams[name] = data
            else:
                regular_streams[name] = data

        # 1. Build MiniStream and MiniFAT
        ministream_bytes = bytearray()
        minifat_table: List[int] = []
        mini_allocations: Dict[str, Tuple[int, int]] = {}  # name -> (start_mini_sector, size)

        for name, data in mini_streams.items():
            start_ms = len(ministream_bytes) // mini_sector_size
            num_ms = math.ceil(len(data) / mini_sector_size)
            mini_allocations[name] = (start_ms, len(data))

            for i in range(num_ms - 1):
                minifat_table.append(start_ms + i + 1)
            minifat_table.append(ENDOFCHAIN)

            padded_data = data.ljust(num_ms * mini_sector_size, b"\x00")
            ministream_bytes.extend(padded_data)

        # Pad MiniFAT table to full sector boundaries
        minifat_ints_per_sector = sector_size // 4
        num_minifat_sectors = math.ceil(len(minifat_table) / minifat_ints_per_sector) if minifat_table else 0
        minifat_table.extend([FREESECT] * (num_minifat_sectors * minifat_ints_per_sector - len(minifat_table)))
        minifat_bytes = struct.pack(f"<{len(minifat_table)}I", *minifat_table) if minifat_table else b""

        # 2. Prepare Directory Entries
        # Index 0: Root Entry
        # Indices 1..N: Stream entries
        entries: List[DirectoryEntry] = []
        now = datetime.now(timezone.utc)

        root_entry = DirectoryEntry(
            index=0,
            name="Root Entry",
            entry_type=STGTY_ROOT,
            color=COLOR_BLACK,
            created=now,
            modified=now,
            size=len(ministream_bytes),
        )
        entries.append(root_entry)

        stream_names = list(self._streams.keys())
        for idx, name in enumerate(stream_names, start=1):
            data = self._streams[name]
            is_mini = name in mini_streams
            start_sect, size = (
                mini_allocations[name] if is_mini else (ENDOFCHAIN if len(data) == 0 else 0, len(data))
            )
            entry = DirectoryEntry(
                index=idx,
                name=name,
                entry_type=STGTY_STREAM,
                color=COLOR_BLACK,
                created=now,
                modified=now,
                start_sector=start_sect,
                size=size,
            )
            entries.append(entry)

        # Build balanced binary tree (Red-Black / BST) for children of Root Entry
        def build_child_tree(sub_entries: List[DirectoryEntry]) -> int:
            if not sub_entries:
                return NOSTREAM
            mid = len(sub_entries) // 2
            curr = sub_entries[mid]
            curr.left_sibling = build_child_tree(sub_entries[:mid])
            curr.right_sibling = build_child_tree(sub_entries[mid + 1 :])
            return curr.index

        # Sort children by name length and UTF-16LE uppercase comparison according to CFB spec
        def cfb_key(e: DirectoryEntry):
            return (len(e.name), e.name.upper())

        child_entries = sorted(entries[1:], key=cfb_key)
        root_entry.child = build_child_tree(child_entries)

        # Directory sectors: 4 entries (128 bytes each) per 512-byte sector
        entries_per_sector = sector_size // 128
        num_dir_sectors = math.ceil(len(entries) / entries_per_sector)
        # Pad entries
        while len(entries) < num_dir_sectors * entries_per_sector:
            entries.append(DirectoryEntry(index=len(entries), entry_type=STGTY_INVALID))

        # 3. Regular Sectors Allocation
        # Sector layout sequence:
        # Regular stream data -> MiniStream data -> MiniFAT sectors -> Directory sectors -> FAT sectors -> DIFAT sectors (if any)
        sectors: List[bytes] = []
        regular_allocations: Dict[str, Tuple[int, int]] = {}

        for name, data in regular_streams.items():
            if len(data) == 0:
                regular_allocations[name] = (ENDOFCHAIN, 0)
                continue
            start_s = len(sectors)
            num_s = math.ceil(len(data) / sector_size)
            regular_allocations[name] = (start_s, len(data))
            for s_idx in range(num_s):
                chunk = data[s_idx * sector_size : (s_idx + 1) * sector_size].ljust(sector_size, b"\x00")
                sectors.append(chunk)

        # MiniStream in regular sectors
        root_start_sector = ENDOFCHAIN
        if len(ministream_bytes) > 0:
            root_start_sector = len(sectors)
            num_root_s = math.ceil(len(ministream_bytes) / sector_size)
            for s_idx in range(num_root_s):
                chunk = bytes(ministream_bytes[s_idx * sector_size : (s_idx + 1) * sector_size]).ljust(sector_size, b"\x00")
                sectors.append(chunk)
        root_entry.start_sector = root_start_sector

        # Assign regular stream start sectors to Directory entries
        for entry in entries:
            if entry.entry_type == STGTY_STREAM and entry.name in regular_allocations:
                entry.start_sector = regular_allocations[entry.name][0]

        # MiniFAT sectors
        first_minifat_sector = ENDOFCHAIN
        if num_minifat_sectors > 0:
            first_minifat_sector = len(sectors)
            for s_idx in range(num_minifat_sectors):
                chunk = minifat_bytes[s_idx * sector_size : (s_idx + 1) * sector_size].ljust(sector_size, b"\x00")
                sectors.append(chunk)

        # Directory sectors
        first_dir_sector = len(sectors)
        dir_bytes = b"".join(e.to_bytes() for e in entries)
        for s_idx in range(num_dir_sectors):
            chunk = dir_bytes[s_idx * sector_size : (s_idx + 1) * sector_size].ljust(sector_size, b"\x00")
            sectors.append(chunk)

        # 4. Build FAT Chains for All Allocated Sectors
        total_data_sectors = len(sectors)
        fat: List[int] = [FREESECT] * total_data_sectors

        def link_chain(start_s: int, num_s: int):
            if num_s <= 0 or start_s == ENDOFCHAIN:
                return
            for i in range(num_s - 1):
                fat[start_s + i] = start_s + i + 1
            fat[start_s + num_s - 1] = ENDOFCHAIN

        # Link regular streams
        for name, (start_s, size) in regular_allocations.items():
            if size > 0:
                link_chain(start_s, math.ceil(size / sector_size))

        # Link MiniStream
        if len(ministream_bytes) > 0:
            link_chain(root_start_sector, math.ceil(len(ministream_bytes) / sector_size))

        # Link MiniFAT
        if num_minifat_sectors > 0:
            link_chain(first_minifat_sector, num_minifat_sectors)

        # Link Directory
        link_chain(first_dir_sector, num_dir_sectors)

        # 5. Calculate FAT & DIFAT Requirements
        # How many FAT sectors are needed to store `len(fat) + num_fat_sectors + num_difat_sectors` entries?
        fat_entries_per_sector = sector_size // 4
        num_fat_sectors = 0
        num_difat_sectors = 0

        while True:
            total_sectors = total_data_sectors + num_fat_sectors + num_difat_sectors
            needed_fat_sectors = math.ceil(total_sectors / fat_entries_per_sector)
            needed_difat_sectors = 0
            if needed_fat_sectors > 109:
                # 109 in header, rest in DIFAT sectors (127 per 512-byte sector, 1 pointer to next)
                difat_entries_per_sec = fat_entries_per_sector - 1
                needed_difat_sectors = math.ceil((needed_fat_sectors - 109) / difat_entries_per_sec)

            if needed_fat_sectors == num_fat_sectors and needed_difat_sectors == num_difat_sectors:
                break
            num_fat_sectors = needed_fat_sectors
            num_difat_sectors = needed_difat_sectors

        # Allocate FAT sectors
        fat_sector_indices = list(range(len(sectors), len(sectors) + num_fat_sectors))
        for _ in range(num_fat_sectors):
            sectors.append(b"\x00" * sector_size)

        # Allocate DIFAT sectors (if needed)
        difat_sector_indices = list(range(len(sectors), len(sectors) + num_difat_sectors))
        for _ in range(num_difat_sectors):
            sectors.append(b"\x00" * sector_size)

        # Expand FAT array to hold FAT and DIFAT sector markers
        fat.extend([FATSECT] * num_fat_sectors)
        fat.extend([DIFSECT] * num_difat_sectors)
        # Pad FAT to sector multiple
        fat.extend([FREESECT] * (num_fat_sectors * fat_entries_per_sector - len(fat)))

        # Pack FAT sectors into sector array
        for idx, fat_s in enumerate(fat_sector_indices):
            sub_fat = fat[idx * fat_entries_per_sector : (idx + 1) * fat_entries_per_sector]
            sectors[fat_s] = struct.pack(f"<{len(sub_fat)}I", *sub_fat)

        # 6. Build DIFAT
        difat_header_entries = fat_sector_indices[:109]
        if len(difat_header_entries) < 109:
            difat_header_entries.extend([FREESECT] * (109 - len(difat_header_entries)))

        first_difat_sector = ENDOFCHAIN
        if num_difat_sectors > 0:
            first_difat_sector = difat_sector_indices[0]
            remaining_fat_sectors = fat_sector_indices[109:]
            difat_entries_per_sec = fat_entries_per_sector - 1

            for d_idx, d_sector in enumerate(difat_sector_indices):
                chunk_fat = remaining_fat_sectors[d_idx * difat_entries_per_sec : (d_idx + 1) * difat_entries_per_sec]
                next_difat = difat_sector_indices[d_idx + 1] if d_idx + 1 < len(difat_sector_indices) else ENDOFCHAIN
                chunk_fat = chunk_fat + [FREESECT] * (difat_entries_per_sec - len(chunk_fat)) + [next_difat]
                sectors[d_sector] = struct.pack(f"<{fat_entries_per_sector}I", *chunk_fat)

        # 7. Build 512-byte CFBF Header
        header = bytearray(512)
        header[0:8] = CFB_SIGNATURE
        header[8:24] = b"\x00" * 16  # CLSID
        struct.pack_into("<H", header, 24, 0x003E)  # Minor version
        struct.pack_into("<H", header, 26, VERSION_3)  # Major version (v3)
        struct.pack_into("<H", header, 28, LITTLE_ENDIAN)  # Byte order
        struct.pack_into("<H", header, 30, 9)  # Sector shift (2^9 = 512)
        struct.pack_into("<H", header, 32, 6)  # Mini sector shift (2^6 = 64)
        header[34:40] = b"\x00" * 6  # Reserved
        struct.pack_into("<I", header, 40, 0)  # Directory sectors (must be 0 for v3)
        struct.pack_into("<I", header, 44, num_fat_sectors)
        struct.pack_into("<I", header, 48, first_dir_sector)
        struct.pack_into("<I", header, 52, 0)  # Transaction signature
        struct.pack_into("<I", header, 56, self._mini_cutoff)
        struct.pack_into("<I", header, 60, first_minifat_sector)
        struct.pack_into("<I", header, 64, num_minifat_sectors)
        struct.pack_into("<I", header, 68, first_difat_sector)
        struct.pack_into("<I", header, 72, num_difat_sectors)
        struct.pack_into("<109I", header, 76, *difat_header_entries)

        return bytes(header) + b"".join(sectors)


__all__ = [
    "CFBReader",
    "CFBWriter",
    "DirectoryEntry",
    "CFB_SIGNATURE",
    "VERSION_3",
    "VERSION_4",
    "ENDOFCHAIN",
    "FREESECT",
    "FATSECT",
    "DIFSECT",
    "STGTY_ROOT",
    "STGTY_STORAGE",
    "STGTY_STREAM",
]
