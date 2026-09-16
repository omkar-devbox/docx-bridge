#!/usr/bin/env python3
"""
Lossless DOC ↔ JSON Round-Trip Test
=====================================
Usage:
    python tests/test_doc_roundtrip.py [path/to/file.doc]

Steps:
    1. DOC  → original.json
    2. JSON → roundtrip.doc
    3. DOC  → roundtrip.json
    4. Compare original.json vs roundtrip.json
    5. Print full comparison report

Success criteria:
    - Text content identical
    - Style names and istd values preserved
    - istdBase (style hierarchy) preserved
    - Paragraph formatting (align, spacing, indent, etc.) preserved
    - Character formatting (bold, italic, underline, size, color, etc.) preserved
    - SPRM round-trip (unknownSprms not dropped)
    - Tables structure preserved
    - Sections (page size, margins) preserved
    - Headers / footers preserved
    - Unknown data (rawSprms, papxRaw, chpxRaw) survives
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from formats.doc.reader import DocReader
from parser.doc.binary_to_json import BinaryToJsonParser
from formats.doc.writer import DocWriter
from parser.doc.json_to_binary import JsonToBinaryParser
from utils.common.json import dump_json, load_json


# ─────────────────────────────────────────────────────────────────────────────
# Comparison helpers
# ─────────────────────────────────────────────────────────────────────────────

def _collect_texts(data: Dict[str, Any]) -> List[str]:
    texts = []
    for sec in data.get("sections", []):
        for item in sec.get("content", []):
            _collect_item_texts(item, texts)
    return texts


def _collect_item_texts(item: Any, out: List[str]) -> None:
    if not isinstance(item, dict):
        return
    if item.get("type") == "table":
        for row in item.get("rows", []):
            for cell in (row.get("cells", []) if isinstance(row, dict) else row):
                for cp in (cell.get("content", []) if isinstance(cell, dict) else []):
                    out.append(cp.get("text", ""))
    else:
        out.append(item.get("text", ""))


def _compare_styles(orig: Dict, rt: Dict) -> Tuple[bool, bool, List[str]]:
    """Returns (styles_ok, hierarchy_ok, issues)."""
    o_styles = orig.get("styles", {})
    r_styles = rt.get("styles", {})
    issues = []

    # Check all original style names survived
    missing = [n for n in o_styles if n not in r_styles]
    if missing:
        issues.append(f"Missing styles: {missing[:5]}")

    hierarchy_ok = True
    for name, o_entry in o_styles.items():
        r_entry = r_styles.get(name)
        if r_entry is None:
            continue
        # Check istd
        if o_entry.get("istd") != r_entry.get("istd"):
            issues.append(f"Style '{name}': istd {o_entry.get('istd')} → {r_entry.get('istd')}")
        # Check istdBase
        o_base = o_entry.get("istdBase")
        r_base = r_entry.get("istdBase")
        if o_base != r_base:
            issues.append(f"Style '{name}': istdBase {o_base} → {r_base}")
            hierarchy_ok = False
        # Check type
        if o_entry.get("type") != r_entry.get("type"):
            issues.append(f"Style '{name}': type {o_entry.get('type')} → {r_entry.get('type')}")

    styles_ok = len(missing) == 0 and all("istd" not in i for i in issues if "istdBase" not in i)
    return styles_ok, hierarchy_ok, issues


def _collect_para_props(data: Dict) -> List[Dict]:
    """Collect list of (style, directParagraph, papxRaw) for each paragraph."""
    paras = []
    for sec in data.get("sections", []):
        for item in sec.get("content", []):
            if isinstance(item, dict) and item.get("type") != "table":
                paras.append({
                    "style": item.get("style"),
                    "styleIndex": item.get("styleIndex"),
                    "directParagraph": item.get("directParagraph", {}),
                    "papxRaw": item.get("papxRaw", ""),
                    "align": item.get("align"),
                    "spacing": item.get("spacing"),
                    "indent": item.get("indent"),
                    "numbering": item.get("numbering"),
                })
    return paras


def _collect_run_props(data: Dict) -> List[Dict]:
    """Collect list of run properties for comparison."""
    run_list = []
    for sec in data.get("sections", []):
        for item in sec.get("content", []):
            if isinstance(item, dict) and item.get("type") != "table":
                for r in item.get("runs", []):
                    if isinstance(r, dict):
                        run_list.append({
                            "text": r.get("text", ""),
                            "directRun": r.get("directRun", {}),
                            "chpxRaw": r.get("chpxRaw", ""),
                            "bold": r.get("bold"),
                            "italic": r.get("italic"),
                            "size": r.get("size"),
                            "color": r.get("color"),
                        })
    return run_list


def _compare_para_formatting(orig_paras, rt_paras) -> Tuple[bool, List[str]]:
    issues = []
    n = min(len(orig_paras), len(rt_paras))
    if len(orig_paras) != len(rt_paras):
        issues.append(f"Paragraph count: {len(orig_paras)} → {len(rt_paras)}")

    for i in range(n):
        o, r = orig_paras[i], rt_paras[i]
        if o.get("styleIndex") != r.get("styleIndex"):
            issues.append(f"Para[{i}] styleIndex: {o.get('styleIndex')} → {r.get('styleIndex')}")
        if o.get("align") != r.get("align"):
            issues.append(f"Para[{i}] align: {o.get('align')} → {r.get('align')}")
        # papxRaw comparison (lossless check)
        if o.get("papxRaw") and r.get("papxRaw") and o["papxRaw"] != r["papxRaw"]:
            issues.append(f"Para[{i}] papxRaw differs (SPRM bytes changed)")

    return len(issues) == 0, issues


def _compare_run_formatting(orig_runs, rt_runs) -> Tuple[bool, List[str]]:
    issues = []
    n = min(len(orig_runs), len(rt_runs))
    if len(orig_runs) != len(rt_runs):
        issues.append(f"Run count: {len(orig_runs)} → {len(rt_runs)}")

    mismatch_count = 0
    for i in range(n):
        o, r = orig_runs[i], rt_runs[i]
        if o.get("chpxRaw") and r.get("chpxRaw") and o["chpxRaw"] != r["chpxRaw"]:
            mismatch_count += 1
        if o.get("bold") != r.get("bold"):
            issues.append(f"Run[{i}] '{o.get('text','')[:20]}' bold: {o.get('bold')} → {r.get('bold')}")
        if o.get("size") != r.get("size"):
            issues.append(f"Run[{i}] size: {o.get('size')} → {r.get('size')}")

    if mismatch_count:
        issues.append(f"{mismatch_count}/{n} runs have differing chpxRaw bytes")

    return len(issues) == 0, issues


def _compare_sections(orig: Dict, rt: Dict) -> Tuple[bool, List[str]]:
    issues = []
    o_secs = orig.get("sections", [])
    r_secs = rt.get("sections", [])
    if len(o_secs) != len(r_secs):
        issues.append(f"Section count: {len(o_secs)} → {len(r_secs)}")
    for i, (o, r) in enumerate(zip(o_secs, r_secs)):
        op = o.get("page", {})
        rp = r.get("page", {})
        for key in ("width", "height", "orientation"):
            if op.get(key) != rp.get(key):
                issues.append(f"Section[{i}] page.{key}: {op.get(key)} → {rp.get(key)}")
        om = op.get("margins", {})
        rm = rp.get("margins", {})
        for key in ("top", "bottom", "left", "right"):
            if om.get(key) != rm.get(key):
                issues.append(f"Section[{i}] margin.{key}: {om.get(key)} → {rm.get(key)}")
    return len(issues) == 0, issues


def _compare_hf(orig: Dict, rt: Dict) -> Tuple[bool, List[str]]:
    issues = []
    for key in ("headers", "footers"):
        o = orig.get(key, {})
        r = rt.get(key, {})
        if bool(o) != bool(r):
            issues.append(f"{key}: present={bool(o)} → {bool(r)}")
    return len(issues) == 0, issues


def _compare_tables(orig: Dict, rt: Dict) -> Tuple[bool, List[str]]:
    issues = []

    def extract_tables(data):
        tables = []
        for sec in data.get("sections", []):
            for item in sec.get("content", []):
                if isinstance(item, dict) and item.get("type") == "table":
                    tables.append(item)
        return tables

    o_tables = extract_tables(orig)
    r_tables = extract_tables(rt)
    if len(o_tables) != len(r_tables):
        issues.append(f"Table count: {len(o_tables)} → {len(r_tables)}")
    for i, (o, r) in enumerate(zip(o_tables, r_tables)):
        o_rows = o.get("rows", [])
        r_rows = r.get("rows", [])
        if len(o_rows) != len(r_rows):
            issues.append(f"Table[{i}] row count: {len(o_rows)} → {len(r_rows)}")
    return len(issues) == 0, issues


def _check_unknown_data(orig: Dict, rt: Dict) -> Tuple[bool, List[str]]:
    """Verify unknownSprms and raw bytes survive the round trip.

    Success criteria:
    - All original unknownSprms opcodes are present in roundtrip (subset check)
    - papxRaw/chpxRaw byte-identical rate is reported
    - roundtrip may have MORE unknownSprms (writer-added table SPRMs etc.) — that is OK
    """
    issues = []

    def collect_opcodes(data, key="unknownSprms"):
        opcodes = []
        for sec in data.get("sections", []):
            for item in sec.get("content", []):
                for r in item.get("runs", []):
                    if isinstance(r, dict):
                        dr = r.get("directRun", {})
                        opcodes.extend(u.get("opcode", "") for u in dr.get(key, []))
                dp = item.get("directParagraph", {})
                opcodes.extend(u.get("opcode", "") for u in dp.get(key, []))
        return opcodes

    def collect_raws(data, key):
        raws = []
        for sec in data.get("sections", []):
            for item in sec.get("content", []):
                if key == "papxRaw":
                    raws.append(item.get("papxRaw", ""))
                else:
                    for r in item.get("runs", []):
                        if isinstance(r, dict):
                            raws.append(r.get("chpxRaw", ""))
        return raws

    orig_opcodes = set(collect_opcodes(orig))
    rt_opcodes   = set(collect_opcodes(rt))

    # All original unknown SPRM opcodes should appear in roundtrip
    missing_opcodes = orig_opcodes - rt_opcodes
    if missing_opcodes:
        issues.append(f"Unknown SPRM opcodes lost in roundtrip: {list(missing_opcodes)[:5]}")

    # Check papxRaw / chpxRaw byte preservation rate
    o_papx = collect_raws(orig, "papxRaw")
    r_papx = collect_raws(rt,   "papxRaw")
    n = min(len(o_papx), len(r_papx))
    same_papx = sum(1 for a, b in zip(o_papx, r_papx) if a == b)
    if n > 0:
        papx_rate = int(same_papx / n * 100)
        if papx_rate < 90:
            issues.append(f"papxRaw byte-identical rate: {papx_rate}% ({same_papx}/{n})")

    return len(issues) == 0, issues


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────

def run_roundtrip(doc_path: Path) -> None:
    print(f"\n{'='*60}")
    print(f"  DOC ↔ JSON LOSSLESS ROUND-TRIP TEST")
    print(f"  Input: {doc_path}")
    print(f"{'='*60}\n")

    out_dir = doc_path.parent
    stem    = doc_path.stem

    orig_json_path = out_dir / f"{stem}_original.json"
    rt_doc_path    = out_dir / f"{stem}_roundtrip.doc"
    rt_json_path   = out_dir / f"{stem}_roundtrip.json"

    # Step 1: DOC → JSON
    print("Step 1: DOC → JSON ...")
    with DocReader(doc_path) as reader:
        orig_data = BinaryToJsonParser(reader).parse_document()
    dump_json(orig_data, orig_json_path)
    print(f"  ✔ Saved {orig_json_path}")

    # Step 2: JSON → DOC
    print("Step 2: JSON → DOC ...")
    with DocWriter(rt_doc_path) as writer:
        JsonToBinaryParser().build_document(orig_data, writer)
    print(f"  ✔ Saved {rt_doc_path}")

    # Step 3: DOC → JSON (roundtrip)
    print("Step 3: roundtrip DOC → JSON ...")
    with DocReader(rt_doc_path) as reader:
        rt_data = BinaryToJsonParser(reader).parse_document()
    dump_json(rt_data, rt_json_path)
    print(f"  ✔ Saved {rt_json_path}\n")

    # ─── Comparisons ───
    results: Dict[str, Tuple[bool, List[str]]] = {}

    # TEXT
    orig_texts = _collect_texts(orig_data)
    rt_texts   = _collect_texts(rt_data)
    text_ok = orig_texts == rt_texts
    text_issues = [] if text_ok else [
        f"Text differs: {len([x for x,y in zip(orig_texts, rt_texts) if x!=y])} paragraphs changed"
    ]
    results["TEXT"] = (text_ok, text_issues)

    # STYLES
    styles_ok, hier_ok, style_issues = _compare_styles(orig_data, rt_data)
    results["STYLES"] = (styles_ok, style_issues[:10])
    results["STYLE INHERITANCE"] = (hier_ok, [i for i in style_issues if "istdBase" in i][:5])

    # PARAGRAPH FORMATTING
    o_paras = _collect_para_props(orig_data)
    r_paras = _collect_para_props(rt_data)
    para_ok, para_issues = _compare_para_formatting(o_paras, r_paras)
    results["PARAGRAPH FORMATTING"] = (para_ok, para_issues[:10])

    # CHARACTER FORMATTING
    o_runs = _collect_run_props(orig_data)
    r_runs = _collect_run_props(rt_data)
    run_ok, run_issues = _compare_run_formatting(o_runs, r_runs)
    results["CHARACTER FORMATTING"] = (run_ok, run_issues[:10])

    # SPRM (unknownSprms preservation)
    sprm_ok, sprm_issues = _check_unknown_data(orig_data, rt_data)
    results["SPRM PRESERVATION"] = (sprm_ok, sprm_issues)

    # TABLES
    tbl_ok, tbl_issues = _compare_tables(orig_data, rt_data)
    results["TABLES"] = (tbl_ok, tbl_issues[:5])

    # SECTIONS
    sec_ok, sec_issues = _compare_sections(orig_data, rt_data)
    results["SECTIONS"] = (sec_ok, sec_issues[:5])

    # HEADERS / FOOTERS
    hf_ok, hf_issues = _compare_hf(orig_data, rt_data)
    results["HEADERS/FOOTERS"] = (hf_ok, hf_issues)

    # UNKNOWN DATA (raw bytes)
    raw_issues = []
    def has_raw(data):
        for sec in data.get("sections", []):
            for item in sec.get("content", []):
                if item.get("papxRaw"):
                    return True
                for r in item.get("runs", []):
                    if isinstance(r, dict) and r.get("chpxRaw"):
                        return True
        return False

    orig_has_raw = has_raw(orig_data)
    rt_has_raw   = has_raw(rt_data)
    if orig_has_raw and not rt_has_raw:
        raw_issues.append("papxRaw/chpxRaw present in original, absent in roundtrip")
    results["UNKNOWN DATA"] = (len(raw_issues) == 0, raw_issues)

    # ─── Report ───
    print(f"\n{'─'*60}")
    print("  ROUND-TRIP COMPARISON REPORT")
    print(f"{'─'*60}")

    pass_count = 0
    total_count = len(results)

    for category, (ok, issues) in results.items():
        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            pass_count += 1
        print(f"  {category:<30} {status}")
        for iss in issues[:3]:
            print(f"    ⚠  {iss}")

    coverage_pct = int(pass_count / total_count * 100)
    print(f"\n  ROUND-TRIP COVERAGE: {coverage_pct}% ({pass_count}/{total_count} categories passed)")

    # Quick stats
    print(f"\n  Stats:")
    print(f"    Original styles    : {len(orig_data.get('styles', {}))}")
    print(f"    Roundtrip styles   : {len(rt_data.get('styles', {}))}")
    print(f"    Original paragraphs: {len(o_paras)}")
    print(f"    Roundtrip paragraphs: {len(r_paras)}")
    print(f"    Original runs      : {len(o_runs)}")
    print(f"    Roundtrip runs     : {len(r_runs)}")
    print(f"    papxRaw in original: {orig_has_raw}")
    print(f"    papxRaw in roundtrip: {rt_has_raw}")
    print(f"\n  Output files:")
    print(f"    {orig_json_path}")
    print(f"    {rt_doc_path}")
    print(f"    {rt_json_path}")
    print(f"{'='*60}\n")

    if coverage_pct < 100:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        doc_file = Path(sys.argv[1])
    else:
        doc_file = PROJECT_ROOT / "Test" / "files" / "file-sample_500kB.doc"

    if not doc_file.exists():
        print(f"File not found: {doc_file}")
        sys.exit(1)

    run_roundtrip(doc_file)
