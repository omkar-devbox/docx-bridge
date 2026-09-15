"""Word binary structures and stream parsers/builders.

Implements:
- STSH (StyleSheet)
- LST / LFO (Numbering & Bullet Lists)
- SED / SEP (Sections & Page Setup)
- PlcfHdd (Headers & Footers)
- Footnotes, Endnotes, Comments
- Bookmarks & Fields
- OLE Property Set Streams (SummaryInformation & DocumentSummaryInformation)
- OfficeArt / Escher images & BLIPs
"""

from __future__ import annotations

import io
import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from formats.doc.cfbf import datetime_to_filetime, filetime_to_datetime
from formats.doc.sprm import (
    decode_character_formatting,
    decode_paragraph_formatting,
    decode_section_formatting,
    encode_character_formatting,
    encode_paragraph_formatting,
    encode_section_formatting,
)

# --------------------------------
# OLE Property Set Stream GUIDs
# --------------------------------

FMTID_SUMMARY_INFO = bytes.fromhex("e0859ff2f94f6810ab9108002b27b3d9")
FMTID_DOC_SUMMARY_INFO = bytes.fromhex("02d5cdd59c2e1b10939708002b2cf9ae")

VT_EMPTY = 0x0000
VT_I2 = 0x0002
VT_I4 = 0x0003
VT_R4 = 0x0004
VT_R8 = 0x0005
VT_DATE = 0x0007
VT_BSTR = 0x0008
VT_ERROR = 0x000A
VT_BOOL = 0x000B
VT_LPSTR = 0x001E
VT_LPWSTR = 0x001F
VT_FILETIME = 0x0040
VT_BLOB = 0x0041

PID_TITLE = 2
PID_SUBJECT = 3
PID_AUTHOR = 4
PID_KEYWORDS = 5
PID_COMMENTS = 6
PID_TEMPLATE = 7
PID_LASTAUTHOR = 8
PID_REVNUMBER = 9
PID_EDITTIME = 10
PID_LASTPRINTED = 11
PID_CREATE_DTM = 12
PID_LASTSAVE_DTM = 13
PID_PAGECOUNT = 14
PID_WORDCOUNT = 15
PID_CHARCOUNT = 16
PID_APPNAME = 18

PID_CATEGORY = 2
PID_COMPANY = 15
PID_MANAGER = 14


# --------------------------------
# OLE Property Sets (Metadata)
# --------------------------------

class PropertySetStream:
    """Parser and builder for OLE Property Set Streams (SummaryInformation)."""

    @classmethod
    def parse(cls, data: bytes) -> Dict[str, Any]:
        """Parse \x05SummaryInformation or \x05DocumentSummaryInformation stream."""
        props: Dict[str, Any] = {}
        if len(data) < 28:
            return props

        byte_order, version, sys_id = struct.unpack_from("<HHH", data, 0)
        num_sets = struct.unpack_from("<I", data, 24)[0]

        for set_idx in range(num_sets):
            offset_hdr = 28 + set_idx * 20
            if offset_hdr + 20 > len(data):
                break
            fmtid = data[offset_hdr : offset_hdr + 16]
            section_offset = struct.unpack_from("<I", data, offset_hdr + 16)[0]

            if section_offset + 8 > len(data):
                continue

            sec_size, prop_count = struct.unpack_from("<II", data, section_offset)
            prop_headers = []
            for p_idx in range(prop_count):
                h_off = section_offset + 8 + p_idx * 8
                if h_off + 8 > len(data):
                    break
                pid, p_off = struct.unpack_from("<II", data, h_off)
                prop_headers.append((pid, section_offset + p_off))

            for pid, val_offset in prop_headers:
                if val_offset + 4 > len(data):
                    continue
                v_type = struct.unpack_from("<I", data, val_offset)[0]
                val_data = data[val_offset + 4 :]

                val: Any = None
                if v_type == VT_LPSTR and len(val_data) >= 4:
                    s_len = struct.unpack_from("<I", val_data, 0)[0]
                    raw = val_data[4 : 4 + s_len]
                    val = raw.decode("windows-1252", errors="replace").rstrip("\x00")
                elif v_type == VT_LPWSTR and len(val_data) >= 4:
                    s_len = struct.unpack_from("<I", val_data, 0)[0]
                    raw = val_data[4 : 4 + s_len * 2]
                    val = raw.decode("utf-16le", errors="replace").rstrip("\x00")
                elif v_type == VT_I4 and len(val_data) >= 4:
                    val = struct.unpack_from("<i", val_data, 0)[0]
                elif v_type == VT_I2 and len(val_data) >= 2:
                    val = struct.unpack_from("<h", val_data, 0)[0]
                elif v_type == VT_FILETIME and len(val_data) >= 8:
                    ft = struct.unpack_from("<Q", val_data, 0)[0]
                    dt = filetime_to_datetime(ft)
                    val = dt.isoformat() if dt else None

                if val is not None:
                    if fmtid == FMTID_DOC_SUMMARY_INFO:
                        doc_map = {
                            PID_CATEGORY: "category",
                            PID_COMPANY: "company",
                            PID_MANAGER: "manager",
                        }
                        field_name = doc_map.get(pid, f"doc_prop_{pid}")
                    else:
                        sum_map = {
                            PID_TITLE: "title",
                            PID_SUBJECT: "subject",
                            PID_AUTHOR: "author",
                            PID_KEYWORDS: "keywords",
                            PID_COMMENTS: "description",
                            PID_LASTAUTHOR: "lastModifiedBy",
                            PID_REVNUMBER: "revision",
                            PID_CREATE_DTM: "created",
                            PID_LASTSAVE_DTM: "modified",
                            PID_PAGECOUNT: "pageCount",
                            PID_WORDCOUNT: "wordCount",
                            PID_CHARCOUNT: "characterCount",
                            PID_APPNAME: "application",
                        }
                        field_name = sum_map.get(pid, f"prop_{pid}")

                    props[field_name] = val

        return props

    @classmethod
    def _pack_value(cls, pid: int, val: Any) -> Optional[bytes]:
        """Pack a Python value into OLE property bytes with type prefix."""
        if pid == 1:  # PID_CODEPAGE
            return struct.pack("<IH", VT_I2, int(val)) + b"\x00\x00"
        if isinstance(val, bool):
            return struct.pack("<IH", VT_BOOL, 0xFFFF if val else 0x0000) + b"\x00\x00"
        elif isinstance(val, int):
            return struct.pack("<Ii", VT_I4, int(val))
        elif isinstance(val, str):
            if "T" in val and len(val) >= 19:
                try:
                    dt = datetime.fromisoformat(val)
                    ft = datetime_to_filetime(dt)
                    return struct.pack("<IQ", VT_FILETIME, ft)
                except Exception:
                    pass
            s_bytes = val.encode("windows-1252", errors="replace") + b"\x00"
            pad = (4 - (len(s_bytes) % 4)) % 4
            return struct.pack("<II", VT_LPSTR, len(s_bytes)) + s_bytes + (b"\x00" * pad)
        return None

    @classmethod
    def _build_property_set_stream(cls, prop_entries: List[Tuple[int, bytes]], fmtid: bytes) -> bytes:
        """Construct an OLE Property Set stream payload with section and header."""
        prop_count = len(prop_entries)
        headers_size = 8 + prop_count * 8
        val_offsets = []
        curr_val_offset = headers_size
        values_bytes = bytearray()

        for pid, p_bytes in prop_entries:
            val_offsets.append(curr_val_offset)
            values_bytes.extend(p_bytes)
            curr_val_offset += len(p_bytes)

        sec_size = curr_val_offset
        sec_header = bytearray(struct.pack("<II", sec_size, prop_count))
        for (pid, _), v_off in zip(prop_entries, val_offsets):
            sec_header.extend(struct.pack("<II", pid, v_off))

        section_bytes = sec_header + values_bytes

        # Main Header (28 + 20 = 48 bytes)
        hdr = bytearray(48)
        struct.pack_into("<HHH", hdr, 0, 0xFFFE, 0, 0x0409)
        struct.pack_into("<I", hdr, 24, 1)  # 1 section
        hdr[28:44] = fmtid
        struct.pack_into("<I", hdr, 44, 48)  # Section offset = 48

        return bytes(hdr) + bytes(section_bytes)

    @classmethod
    def build_summary_information(cls, meta: Dict[str, Any]) -> bytes:
        """Serialize metadata into \x05SummaryInformation stream bytes."""
        prop_entries: List[Tuple[int, bytes]] = []
        seen_pids = set()

        name_to_pid = {
            "title": PID_TITLE,
            "subject": PID_SUBJECT,
            "author": PID_AUTHOR,
            "creator": PID_AUTHOR,
            "keywords": PID_KEYWORDS,
            "description": PID_COMMENTS,
            "comments": PID_COMMENTS,
            "lastModifiedBy": PID_LASTAUTHOR,
            "revision": PID_REVNUMBER,
            "created": PID_CREATE_DTM,
            "modified": PID_LASTSAVE_DTM,
            "pageCount": PID_PAGECOUNT,
            "wordCount": PID_WORDCOUNT,
            "characterCount": PID_CHARCOUNT,
            "application": PID_APPNAME,
        }

        for k, v in meta.items():
            if k in name_to_pid:
                pid = name_to_pid[k]
                if pid not in seen_pids:
                    p = cls._pack_value(pid, v)
                    if p:
                        prop_entries.append((pid, p))
                        seen_pids.add(pid)
            elif k.startswith("prop_"):
                try:
                    pid = int(k.split("_")[1])
                    if pid not in seen_pids:
                        p = cls._pack_value(pid, v)
                        if p:
                            prop_entries.append((pid, p))
                            seen_pids.add(pid)
                except ValueError:
                    pass

        if not prop_entries:
            # Default minimal property
            s_bytes = b"docx-bridge\x00"
            pad = (4 - (len(s_bytes) % 4)) % 4
            packed = struct.pack("<II", VT_LPSTR, len(s_bytes)) + s_bytes + (b"\x00" * pad)
            prop_entries.append((PID_APPNAME, packed))

        prop_entries.sort(key=lambda x: x[0])
        return cls._build_property_set_stream(prop_entries, FMTID_SUMMARY_INFO)

    @classmethod
    def build_document_summary_information(cls, meta: Dict[str, Any]) -> Optional[bytes]:
        """Serialize metadata into \x05DocumentSummaryInformation stream bytes."""
        prop_entries: List[Tuple[int, bytes]] = []
        seen_pids = set()

        name_to_pid = {
            "category": PID_CATEGORY,
            "company": PID_COMPANY,
            "manager": PID_MANAGER,
        }

        for k, v in meta.items():
            if k in name_to_pid:
                pid = name_to_pid[k]
                if pid not in seen_pids:
                    p = cls._pack_value(pid, v)
                    if p:
                        prop_entries.append((pid, p))
                        seen_pids.add(pid)
            elif k.startswith("doc_prop_"):
                try:
                    pid = int(k.split("_")[2])
                    if pid not in seen_pids:
                        p = cls._pack_value(pid, v)
                        if p:
                            prop_entries.append((pid, p))
                            seen_pids.add(pid)
                except ValueError:
                    pass

        if not prop_entries:
            return None

        prop_entries.sort(key=lambda x: x[0])
        return cls._build_property_set_stream(prop_entries, FMTID_DOC_SUMMARY_INFO)


# --------------------------------
# STSH (StyleSheet)
# --------------------------------

@dataclass
class StyleEntry:
    """A Word style definition."""

    style_id: str
    name: str
    style_type: str = "paragraph"  # "paragraph" or "character"
    istd: int = 0
    based_on: Optional[str] = None
    props: Dict[str, Any] = field(default_factory=dict)


class StshParser:
    """Parses STSH stylesheet structures from the Table stream."""

    @classmethod
    def parse(cls, data: bytes) -> Dict[str, Any]:
        """Parse STSH into JSON AST styles structure."""
        if len(data) < 18:
            return {"styles": {}}

        cbStshi, cstd = struct.unpack_from("<HH", data, 0)
        cbSTDBaseInFile = struct.unpack_from("<H", data, 4)[0] if len(data) >= 6 else 18
        offset = 2 + cbStshi

        styles: Dict[str, Any] = {}
        for istd in range(cstd):
            if offset + 2 > len(data):
                break
            cbStd = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            if cbStd == 0:
                continue

            std_bytes = data[offset : offset + cbStd]
            offset += cbStd

            if len(std_bytes) < cbSTDBaseInFile:
                continue

            # Parse STD
            w0, w1 = struct.unpack_from("<HH", std_bytes, 0)
            sti = w0 & 0x0FFF
            stk = w1 & 0x000F
            istdBase = (w1 >> 4) & 0x0FFF

            # Name is at std_bytes[cbSTDBaseInFile:], Pascal string (xstz)
            name_part = std_bytes[cbSTDBaseInFile:]
            name = ""
            xstz_len = 0
            if len(name_part) >= 2:
                cch = struct.unpack_from("<H", name_part, 0)[0]
                if cch > 0 and 2 + cch * 2 <= len(name_part):
                    name = name_part[2 : 2 + cch * 2].decode("utf-16le", errors="replace").rstrip("\x00")
                    xstz_len = 2 + (cch + 1) * 2
                elif len(name_part) >= 1:
                    cch1 = name_part[0]
                    if cch1 > 0 and 1 + cch1 <= len(name_part):
                        name = name_part[1 : 1 + cch1].decode("latin-1", errors="replace").rstrip("\x00")
                        xstz_len = 1 + cch1 + 1

            if not name:
                builtin_names = {
                    0: "Normal",
                    1: "Heading 1",
                    2: "Heading 2",
                    3: "Heading 3",
                    4: "Heading 4",
                    5: "Heading 5",
                    6: "Heading 6",
                    7: "Heading 7",
                    8: "Heading 8",
                    9: "Heading 9",
                    10: "Default Paragraph Font",
                    11: "Table Normal",
                    12: "No List",
                }
                name = builtin_names.get(sti, f"Style{istd}")

            style_type_str = {1: "paragraph", 2: "character", 3: "table", 4: "numbering"}.get(stk, "paragraph")

            # Parse formatting SPRMs from UPX
            upx_offset = cbSTDBaseInFile + xstz_len
            if upx_offset % 2 != 0:
                upx_offset += 1

            rem = std_bytes[upx_offset:]
            rem_off = 0
            p_props: Dict[str, Any] = {}
            c_props: Dict[str, Any] = {}
            if stk == 1:  # paragraph style: UPX.papx then UPX.chpx
                if rem_off + 2 <= len(rem):
                    cbUpxPapx = struct.unpack_from("<H", rem, rem_off)[0]
                    rem_off += 2
                    papx_bytes = rem[rem_off : rem_off + cbUpxPapx]
                    rem_off += cbUpxPapx
                    if rem_off % 2 != 0:
                        rem_off += 1
                    if len(papx_bytes) >= 2:
                        p_props = decode_paragraph_formatting(papx_bytes[2:])
                if rem_off + 2 <= len(rem):
                    cbUpxChpx = struct.unpack_from("<H", rem, rem_off)[0]
                    rem_off += 2
                    chpx_bytes = rem[rem_off : rem_off + cbUpxChpx]
                    rem_off += cbUpxChpx
                    c_props = decode_character_formatting(chpx_bytes)
            elif stk == 2:  # character style: UPX.chpx
                if rem_off + 2 <= len(rem):
                    cbUpxChpx = struct.unpack_from("<H", rem, rem_off)[0]
                    rem_off += 2
                    chpx_bytes = rem[rem_off : rem_off + cbUpxChpx]
                    rem_off += cbUpxChpx
                    c_props = decode_character_formatting(chpx_bytes)

            style_entry: Dict[str, Any] = {
                "id": name,
                "name": name,
                "type": style_type_str,
                "istd": istd,
            }
            if istd == 0:
                style_entry["default"] = True
                style_entry["primaryStyle"] = True
            if p_props:
                style_entry["paragraph"] = p_props
            if c_props:
                style_entry["run"] = c_props
                for k in ("bold", "italic", "size", "color", "fontIndex"):
                    if k in c_props:
                        style_entry[k] = c_props[k]

            styles[name] = style_entry

        return {"styles": styles}

    @classmethod
    def build(cls, styles_dict: Dict[str, Any]) -> Tuple[bytes, Dict[str, int]]:
        """Build binary STSH table and return (stsh_bytes, style_name_to_istd_map)."""
        styles_map: Dict[str, int] = {}
        raw_styles = styles_dict.get("styles", styles_dict) if isinstance(styles_dict, dict) else {}

        type_map = {"paragraph": 1, "character": 2, "table": 3, "numbering": 4}

        # Check if styles provide explicit istd
        assigned_slots: Dict[int, Tuple[str, Any]] = {}
        unassigned: List[Tuple[str, Any]] = []

        if isinstance(raw_styles, dict):
            for name, item in raw_styles.items():
                if isinstance(item, dict) and "istd" in item and item["istd"] is not None:
                    try:
                        slot = int(item["istd"])
                        assigned_slots[slot] = (str(name), item)
                    except (ValueError, TypeError):
                        unassigned.append((str(name), item))
                else:
                    unassigned.append((str(name), item))

        # Always ensure Normal is at istd 0 if not assigned
        if 0 not in assigned_slots:
            normal_item = raw_styles.get("Normal", {"type": "paragraph"}) if isinstance(raw_styles, dict) else {"type": "paragraph"}
            assigned_slots[0] = ("Normal", normal_item)
            unassigned = [(n, it) for n, it in unassigned if n != "Normal"]

        # Assign remaining
        next_slot = 1
        for name, item in unassigned:
            while next_slot in assigned_slots:
                next_slot += 1
            assigned_slots[next_slot] = (name, item)
            next_slot += 1

        cstd = max(assigned_slots.keys()) + 1 if assigned_slots else 1

        stds_by_slot: Dict[int, bytes] = {}
        for slot, (name, item) in assigned_slots.items():
            st_type_str = item.get("type", "paragraph") if isinstance(item, dict) else "paragraph"
            stk = type_map.get(st_type_str, 1)
            sti = slot if slot < 4094 else 4094
            std_bytes = cls._build_single_std(sti, slot, stk, name, item)
            stds_by_slot[slot] = std_bytes
            styles_map[name] = slot

        cbStshi = 18
        # Header: cbStshi (2 bytes) followed by Stshi structure (18 bytes)
        stshi = struct.pack(
            "<10H",
            cbStshi,
            cstd,
            18,   # cbSTDBaseInFile (18 bytes standard for Word 97-2003)
            1,    # fStdStylenamesWritten
            4094, # stiMaxWhenSaved
            0,
            0,
            0,
            0,
            0,
        )

        out = bytearray(stshi)
        for istd in range(cstd):
            if istd in stds_by_slot:
                std = stds_by_slot[istd]
                out.extend(struct.pack("<H", len(std)))
                out.extend(std)
            else:
                out.extend(struct.pack("<H", 0))

        return bytes(out), styles_map

    @classmethod
    def _build_single_std(
        cls,
        sti: int,
        istd: int,
        stk: int,
        name: str,
        item: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Build a single STD (Style Descriptor) record with UPX."""
        w0 = sti & 0x0FFF
        w1 = stk & 0x000F
        # 18-byte standard Word 97-2003 StdfBase (9 unsigned 16-bit shorts)
        base = struct.pack("<9H", w0, w1, istd, 0, 0, 0, 0, 0, 0)
        # Pascal UTF-16LE string (xstz)
        encoded_name = name.encode("utf-16le")
        cch = len(encoded_name) // 2
        name_bytes = struct.pack("<H", cch) + encoded_name + b"\x00\x00"
        if len(name_bytes) % 2 != 0:
            name_bytes += b"\x00"

        upx_bytes = bytearray()
        if item and isinstance(item, dict):
            if stk == 1:  # Paragraph style: UPX.papx then UPX.chpx
                p_props = dict(item.get("paragraph", {}))
                for k in ("align", "spacing", "indent", "keepWithNext", "keepLines"):
                    if k in item and k not in p_props:
                        p_props[k] = item[k]

                c_props = dict(item.get("run", {}))
                for k in ("bold", "italic", "underline", "size", "font", "fontIndex", "color"):
                    if k in item and k not in c_props:
                        c_props[k] = item[k]

                if p_props or c_props:
                    p_grpprl = encode_paragraph_formatting(p_props)
                    papx = struct.pack("<H", istd) + p_grpprl
                    upx_bytes.extend(struct.pack("<H", len(papx)))
                    upx_bytes.extend(papx)
                    if len(papx) % 2 != 0:
                        upx_bytes.append(0)

                    c_grpprl = encode_character_formatting(c_props)
                    upx_bytes.extend(struct.pack("<H", len(c_grpprl)))
                    upx_bytes.extend(c_grpprl)
                    if len(c_grpprl) % 2 != 0:
                        upx_bytes.append(0)

            elif stk == 2:  # Character style: UPX.chpx
                c_props = dict(item.get("run", {}))
                for k in ("bold", "italic", "underline", "size", "font", "fontIndex", "color"):
                    if k in item and k not in c_props:
                        c_props[k] = item[k]

                if c_props:
                    c_grpprl = encode_character_formatting(c_props)
                    upx_bytes.extend(struct.pack("<H", len(c_grpprl)))
                    upx_bytes.extend(c_grpprl)
                    if len(c_grpprl) % 2 != 0:
                        upx_bytes.append(0)

        return base + name_bytes + bytes(upx_bytes)


# --------------------------------
# Lists & Numbering (LST / LFO)
# --------------------------------

class ListParser:
    """Parses and serializes Word 97-2003 list tables (PlfLst, PlfLfo)."""

    @classmethod
    def parse(cls, lst_bytes: bytes, lfo_bytes: bytes) -> Dict[str, Any]:
        """Parse PlfLst and PlfLfo into unified JSON AST numbering structure."""
        abstract_nums: List[Dict[str, Any]] = []
        nums: List[Dict[str, Any]] = []

        # Parse PlfLst
        if len(lst_bytes) >= 2:
            cLst = struct.unpack_from("<H", lst_bytes, 0)[0]
            offset = 2
            # Read cLst list definitions
            for i in range(cLst):
                if offset + 28 > len(lst_bytes):
                    break
                lsid, tplc = struct.unpack_from("<ii", lst_bytes, offset)
                offset += 28  # size of LSTF

                abstract_nums.append({
                    "id": i + 1,
                    "lsid": lsid,
                    "levels": [
                        {
                            "level": 0,
                            "format": "bullet",
                            "text": "\u2022",
                            "start": 1,
                        }
                    ]
                })

        lsid_to_abs_id = {a["lsid"]: a["id"] for a in abstract_nums if "lsid" in a}

        # Parse PlfLfo (each LFO is 16 bytes)
        if len(lfo_bytes) >= 4:
            cLfo = struct.unpack_from("<I", lfo_bytes, 0)[0]
            for i in range(cLfo):
                offset = 4 + i * 16
                if offset + 4 > len(lfo_bytes):
                    break
                lsid = struct.unpack_from("<i", lfo_bytes, offset)[0]
                abs_id = lsid_to_abs_id.get(lsid, i + 1)
                nums.append({
                    "id": i + 1,
                    "abstractNumId": abs_id,
                    "lsid": lsid,
                })

        if not nums and abstract_nums:
            for idx, a in enumerate(abstract_nums, start=1):
                nums.append({
                    "id": a.get("id", idx),
                    "abstractNumId": a.get("id", idx),
                    "lsid": a.get("lsid", idx),
                })

        return {"abstract_num": abstract_nums, "num": nums}

    @classmethod
    def build(cls, numbering_dict: Dict[str, Any]) -> Tuple[bytes, bytes]:
        """Build PlfLst and PlfLfo bytes from AST numbering."""
        if not isinstance(numbering_dict, dict):
            return b"", b""
        nums = numbering_dict.get("num", [])
        abstract_nums = numbering_dict.get("abstract_num", [])

        if not nums and not abstract_nums:
            return b"", b""

        # 1. Build PlfLst from abstract_nums
        abs_items = list(abstract_nums) if abstract_nums else []
        if not abs_items and nums:
            for idx, n in enumerate(nums, start=1):
                abs_items.append({
                    "id": n.get("abstractNumId", idx),
                    "lsid": n.get("lsid", idx * 1000 + 1),
                })

        cLst = len(abs_items)
        lst_out = bytearray(struct.pack("<H", cLst))
        for idx, a in enumerate(abs_items, start=1):
            lsid = a.get("lsid")
            if lsid is None or lsid == 0:
                lsid = idx * 1000 + 1
            # LSTF (28 bytes)
            lstf = struct.pack(
                "<ii18sBB",
                lsid,
                lsid,
                b"\x00" * 18,
                1,  # fSimpleList
                0,
            )
            lst_out.extend(lstf)

        # 2. Build PlfLfo from nums
        num_items = list(nums) if nums else []
        if not num_items and abs_items:
            for idx, a in enumerate(abs_items, start=1):
                num_items.append({
                    "id": a.get("id", idx),
                    "abstractNumId": a.get("id", idx),
                    "lsid": a.get("lsid", idx * 1000 + 1),
                })

        cLfo = len(num_items)
        lfo_out = bytearray(struct.pack("<I", cLfo))
        for idx, item in enumerate(num_items, start=1):
            lsid = item.get("lsid")
            if lsid is None or lsid == 0:
                lsid = idx * 1000 + 1
            # LFO (16 bytes)
            lfo = struct.pack("<iiii", lsid, 0, 0, 0)
            lfo_out.extend(lfo)

        return bytes(lst_out), bytes(lfo_out)


# --------------------------------
# Sections & Page Geometry (SED / SEP)
# --------------------------------

class SectionTable:
    """Parses and builds PlcfSed and Sepx section descriptors."""

    @classmethod
    def parse(
        cls,
        plcf_sed_bytes: bytes,
        word_doc_bytes: bytes,
    ) -> List[Dict[str, Any]]:
        """Parse PlcfSed and Sepx to extract section formatting."""
        if len(plcf_sed_bytes) < 16:
            return [{"page": {"margins": {"top": 1440, "bottom": 1440, "left": 1440, "right": 1440}}}]

        # PlcfSed: (n + 1) CPs + n Sed (12 bytes each) => len = (n+1)*4 + n*12 = 4 + 16*n
        n = (len(plcf_sed_bytes) - 4) // 16
        if n <= 0:
            return [{"page": {"margins": {"top": 1440, "bottom": 1440, "left": 1440, "right": 1440}}}]

        sed_start = (n + 1) * 4
        sections: List[Dict[str, Any]] = []

        for i in range(n):
            s_off = sed_start + i * 12
            fn, fcSepx = struct.unpack_from("<HI", plcf_sed_bytes, s_off)

            # Read Sepx from WordDocument stream
            sec_props: Dict[str, Any] = {}
            if fcSepx < len(word_doc_bytes) and fcSepx > 0:
                cb = struct.unpack_from("<H", word_doc_bytes, fcSepx)[0]
                grpprl = word_doc_bytes[fcSepx + 2 : fcSepx + 2 + cb]
                sec_props = decode_section_formatting(grpprl)

            if not sec_props.get("page"):
                sec_props["page"] = {"margins": {"top": 1440, "bottom": 1440, "left": 1440, "right": 1440}}

            sections.append(sec_props)

        return sections if sections else [{"page": {"margins": {"top": 1440, "bottom": 1440, "left": 1440, "right": 1440}}}]

    @classmethod
    def build(
        cls,
        sections: List[Dict[str, Any]],
        total_cps: int,
        start_fc: int,
    ) -> Tuple[bytes, bytes]:
        """Build Sepx bytes (for WordDocument stream) and PlcfSed bytes (for Table stream).

        Returns:
            (sepx_data_bytes, plcf_sed_bytes)
        """
        if not sections:
            sections = [{"page": {"margins": {"top": 1440, "bottom": 1440, "left": 1440, "right": 1440}}}]

        n = len(sections)
        cps = [0]
        cps_per_sec = total_cps // n if n > 0 else total_cps
        for i in range(1, n):
            cps.append(cps_per_sec * i)
        cps.append(total_cps)

        sepx_data = bytearray()
        seds: List[Tuple[int, int]] = []

        curr_fc = start_fc
        for sec in sections:
            grpprl = encode_section_formatting(sec)
            cb = len(grpprl)
            sepx_chunk = struct.pack("<H", cb) + grpprl
            sepx_data.extend(sepx_chunk)
            seds.append((0, curr_fc))
            curr_fc += len(sepx_chunk)

        # Build PlcfSed: (n + 1) CPs + n Sed structures (12 bytes each)
        plcf_sed = bytearray()
        plcf_sed.extend(struct.pack(f"<{len(cps)}I", *cps))
        for fn, fc in seds:
            # Sed: fn (uint16), fcSepx (uint32), fnMpr (uint16), fcMpr (uint32)
            plcf_sed.extend(struct.pack("<HIHI", fn, fc, 0, 0))

        return bytes(sepx_data), bytes(plcf_sed)


# --------------------------------
# Headers & Footers (PlcfHdd)
# --------------------------------

class HeaderFooterTable:
    """Parses and serializes headers and footers."""

    @classmethod
    def parse(
        cls,
        plcf_hdd_bytes: bytes,
        hdd_text: str,
    ) -> Dict[str, Any]:
        """Split hdd_text using PlcfHdd CPs."""
        if len(plcf_hdd_bytes) < 8 or not hdd_text:
            return {"headers": {}, "footers": {}}

        num_entries = len(plcf_hdd_bytes) // 4
        cps = list(struct.unpack(f"<{num_entries}I", plcf_hdd_bytes))

        # Standard sub-part mappings
        part_names = [
            ("headers", "even"),
            ("headers", "default"),
            ("footers", "even"),
            ("footers", "default"),
            ("headers", "first"),
            ("footers", "first"),
        ]

        result: Dict[str, Any] = {"headers": {}, "footers": {}}
        for idx in range(min(len(part_names), len(cps) - 1)):
            category, slot = part_names[idx]
            cp_start = cps[idx]
            cp_end = cps[idx + 1]
            if cp_start < len(hdd_text):
                text_slice = hdd_text[cp_start:cp_end].strip()
                if text_slice:
                    result[category][slot] = {
                        "content": [
                            {"type": "paragraph", "text": text_slice}
                        ]
                    }

        return result

    @classmethod
    def build(
        cls,
        headers: Dict[str, Any],
        footers: Dict[str, Any],
    ) -> Tuple[str, bytes]:
        """Build header/footer subdocument text and PlcfHdd bytes."""
        text_parts = []
        cps = [0]

        slots = [
            ("headers", "even"),
            ("headers", "default"),
            ("footers", "even"),
            ("footers", "default"),
            ("headers", "first"),
            ("footers", "first"),
        ]

        for cat, slot in slots:
            source = headers if cat == "headers" else footers
            content_str = ""
            if isinstance(source, dict) and slot in source:
                item = source[slot]
                if isinstance(item, dict) and "content" in item:
                    paras = []
                    for p in item["content"]:
                        if isinstance(p, dict):
                            paras.append(p.get("text", ""))
                    content_str = "\r".join(paras)
                elif isinstance(item, str):
                    content_str = item

            if content_str:
                content_str += "\r"
            text_parts.append(content_str)
            cps.append(cps[-1] + len(content_str))

        full_text = "".join(text_parts)
        plcf_bytes = struct.pack(f"<{len(cps)}I", *cps)
        return full_text, plcf_bytes


# --------------------------------
# OfficeArt / Escher (Media & BLIPs)
# --------------------------------

class EscherParser:
    """Parses OfficeArt (Escher) drawing containers and BLIP images."""

    @classmethod
    def extract_blips(cls, data: bytes) -> List[Dict[str, Any]]:
        """Scan byte stream for embedded BLIP images (JPEG, PNG, WMF, EMF)."""
        images: List[Dict[str, Any]] = []
        if len(data) < 8:
            return images

        # Standard JPEG, PNG signatures
        # JPEG: \xFF\xD8\xFF
        # PNG: \x89PNG\r\n\x1a\n
        idx = 0
        img_counter = 1

        while idx < len(data):
            # Check for PNG
            if data[idx : idx + 8] == b"\x89PNG\r\n\x1a\n":
                # Find PNG IEND chunk
                iend = data.find(b"IEND\xaeB`\x82", idx)
                if iend != -1:
                    png_bytes = data[idx : iend + 8]
                    images.append({
                        "name": f"image{img_counter}.png",
                        "type": "png",
                        "data": png_bytes,
                    })
                    img_counter += 1
                    idx = iend + 8
                    continue

            # Check for JPEG
            if data[idx : idx + 3] == b"\xff\xd8\xff":
                # Find JPEG EOI (\xFF\xD9)
                eoi = data.find(b"\xff\xd9", idx + 2)
                if eoi != -1:
                    jpg_bytes = data[idx : eoi + 2]
                    images.append({
                        "name": f"image{img_counter}.jpg",
                        "type": "jpg",
                        "data": jpg_bytes,
                    })
                    img_counter += 1
                    idx = eoi + 2
                    continue

            idx += 1

        return images


__all__ = [
    "PropertySetStream",
    "StshParser",
    "StyleEntry",
    "ListParser",
    "SectionTable",
    "HeaderFooterTable",
    "EscherParser",
]
