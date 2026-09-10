"""Comprehensive validation of Master DOCX <-> JSON <-> DOCX fidelity."""

import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from docx.reader import DocxReader
from main import docx_to_json, json_to_docx
from utils.json import load_json
from handlers.base import qn


class TestAuditFidelity(unittest.TestCase):
    """Audit test suite verifying zero-loss conversion, clean JSON, and consistent schemas."""

    def setUp(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.files_dir = self.project_root / "Test" / "files"

    def test_all_sample_files(self):
        test_files = [
            self.files_dir / "test_bullet.docx",
            self.files_dir / "QuotationForReport.docx",
            self.files_dir / "Apurva Jhunjhunwala.docx",
        ]

        for docx_file in test_files:
            if not docx_file.exists():
                continue
            with self.subTest(file=docx_file.name):
                json_file = docx_file.with_suffix(".json")
                out_docx = docx_file.parent / f"{docx_file.stem}_converted.docx"

                docx_to_json(docx_file, json_file, mode="simple")
                json_to_docx(json_file, out_docx, template_docx=docx_file)

                data = load_json(json_file)

                # 1. Check indent structure consistency
                def check_indents(obj):
                    if isinstance(obj, dict):
                        if "indent" in obj:
                            self.assertIsInstance(
                                obj["indent"], dict,
                                f"Found non-dict indent in {docx_file.name}: {obj['indent']}"
                            )
                        for v in obj.values():
                            check_indents(v)
                    elif isinstance(obj, list):
                        for it in obj:
                            check_indents(it)

                check_indents(data)

                # 2. Check no raw XML in relations or shapes
                if "relations" in data and isinstance(data["relations"], list):
                    for rel in data["relations"]:
                        target = rel.get("target", "")
                        self.assertFalse(
                            target.endswith(".xml") and ("styles" in target or "numbering" in target or "settings" in target or "theme" in target),
                            f"Internal OpenXML target '{target}' leaked into JSON relations"
                        )

                # 3. Check exact DOCX structural and text parity
                with DocxReader(docx_file) as r_orig, DocxReader(out_docx) as r_conv:
                    orig_xml = ET.fromstring(r_orig.get_document_xml())
                    conv_xml = ET.fromstring(r_conv.get_document_xml())

                    orig_ps = orig_xml.findall(".//" + qn("w:p"))
                    conv_ps = conv_xml.findall(".//" + qn("w:p"))
                    self.assertEqual(len(orig_ps), len(conv_ps), "Paragraph counts must match exactly")

                    orig_tbls = orig_xml.findall(".//" + qn("w:tbl"))
                    conv_tbls = conv_xml.findall(".//" + qn("w:tbl"))
                    self.assertEqual(len(orig_tbls), len(conv_tbls), "Table counts must match exactly")

                    orig_texts = [t.text for t in orig_xml.findall(".//" + qn("w:t")) if t.text]
                    conv_texts = [t.text for t in conv_xml.findall(".//" + qn("w:t")) if t.text]
                    self.assertEqual(orig_texts, conv_texts, "All paragraph texts must match 100%")


if __name__ == "__main__":
    unittest.main()
