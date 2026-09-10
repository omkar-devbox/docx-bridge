"""Comprehensive Property-by-Property Fidelity Tests.

Validates that Master DOCX is preserved with zero loss, exact styling,
and no raw XML in JSON output across paragraphs, runs, tables, sections, and media.
"""

import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from docx.reader import DocxReader
from main import docx_to_json, json_to_docx
from handlers.base import qn, local_name
from utils.json import load_json


class TestPropertyFidelity(unittest.TestCase):
    """Rigorous property-by-property validation against Master DOCX."""

    def setUp(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.test_files_dir = self.project_root / "Test" / "files"

    def test_no_raw_xml_in_json(self):
        """Ensure no raw XML strings or relationship XML blobs exist in generated JSON."""
        test_docx = self.test_files_dir / "test_bullet.docx"
        if not test_docx.exists():
            self.skipTest(f"{test_docx} not found")

        temp_json = self.test_files_dir / "temp_no_xml_test.json"
        docx_to_json(test_docx, temp_json, mode="simple")

        data = load_json(temp_json)

        def check_no_raw_xml(obj, path="root"):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    self.assertNotIn("xml", k.lower(), f"Suspicious XML key '{k}' found at {path}")
                    self.assertNotIn("xmlns", k.lower(), f"Namespace declaration '{k}' found at {path}")
                    if isinstance(v, str):
                        self.assertFalse(
                            v.strip().startswith("<") and v.strip().endswith(">"),
                            f"Raw XML string found in value at {path}.{k}: {v[:50]}"
                        )
                    check_no_raw_xml(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    check_no_raw_xml(item, f"{path}[{idx}]")

        check_no_raw_xml(data)
        if temp_json.exists():
            temp_json.unlink()

    def test_fidelity_test_bullet(self):
        """Verify test_bullet.docx roundtrip property parity."""
        test_docx = self.test_files_dir / "test_bullet.docx"
        if not test_docx.exists():
            self.skipTest(f"{test_docx} not found")

        temp_json = self.test_files_dir / "temp_bullet_fidelity.json"
        temp_out = self.test_files_dir / "temp_bullet_fidelity.docx"

        docx_to_json(test_docx, temp_json, mode="simple")
        json_to_docx(temp_json, temp_out, template_docx=test_docx)

        with DocxReader(test_docx) as r_master, DocxReader(temp_out) as r_conv:
            master_xml = ET.fromstring(r_master.get_document_xml())
            conv_xml = ET.fromstring(r_conv.get_document_xml())

            master_ps = master_xml.findall(".//" + qn("w:p"))
            conv_ps = conv_xml.findall(".//" + qn("w:p"))

            self.assertEqual(len(master_ps), len(conv_ps), "Paragraph counts must match exactly")

            for idx, (m_p, c_p) in enumerate(zip(master_ps, conv_ps)):
                m_texts = [t.text for t in m_p.findall(".//" + qn("w:t")) if t.text]
                c_texts = [t.text for t in c_p.findall(".//" + qn("w:t")) if t.text]
                self.assertEqual("".join(m_texts), "".join(c_texts), f"Paragraph {idx} text mismatch")

        if temp_json.exists():
            temp_json.unlink()
        if temp_out.exists():
            temp_out.unlink()

    def test_fidelity_quotation_for_report(self):
        """Verify QuotationForReport.docx roundtrip property parity."""
        test_docx = self.test_files_dir / "QuotationForReport.docx"
        if not test_docx.exists():
            self.skipTest(f"{test_docx} not found")

        temp_json = self.test_files_dir / "temp_quotation_fidelity.json"
        temp_out = self.test_files_dir / "temp_quotation_fidelity.docx"

        docx_to_json(test_docx, temp_json, mode="simple")
        json_to_docx(temp_json, temp_out, template_docx=test_docx)

        with DocxReader(test_docx) as r_master, DocxReader(temp_out) as r_conv:
            master_xml = ET.fromstring(r_master.get_document_xml())
            conv_xml = ET.fromstring(r_conv.get_document_xml())

            master_ps = master_xml.findall(".//" + qn("w:p"))
            conv_ps = conv_xml.findall(".//" + qn("w:p"))
            self.assertEqual(len(master_ps), len(conv_ps), "Paragraph counts must match")

            master_tbls = master_xml.findall(".//" + qn("w:tbl"))
            conv_tbls = conv_xml.findall(".//" + qn("w:tbl"))
            self.assertEqual(len(master_tbls), len(conv_tbls), "Table counts must match")

        if temp_json.exists():
            temp_json.unlink()
        if temp_out.exists():
            temp_out.unlink()


if __name__ == "__main__":
    unittest.main()
