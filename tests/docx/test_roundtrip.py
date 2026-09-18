"""Roundtrip test: XML -> JSON -> XML to ensure fidelity."""

import unittest
from parser.docx.xml_to_json import XmlToJsonParser
from parser.docx.json_to_xml import JsonToXmlParser


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:b/>
        </w:rPr>
        <w:t>Hello World</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>
"""


class TestRoundtrip(unittest.TestCase):
    def test_roundtrip_paragraph_and_run(self):
        """Verify parsing XML to JSON and reconstructing back to XML maintains content."""
        xml_to_json = XmlToJsonParser()
        json_to_xml = JsonToXmlParser()

        # Step 1: XML -> JSON
        json_doc = xml_to_json.parse_document(SAMPLE_XML)
        self.assertEqual(json_doc["type"], "document")
        self.assertEqual(len(json_doc["body"]["content"]), 1)

        p = json_doc["body"]["content"][0]
        self.assertEqual(p["type"], "paragraph")
        self.assertEqual(p["properties"]["style"], "Heading1")
        self.assertEqual(len(p["runs"]), 1)
        self.assertEqual(p["runs"][0]["text"], "Hello World")
        self.assertTrue(p["runs"][0]["properties"]["bold"])

        # Step 2: JSON -> XML
        reconstructed_xml_bytes = json_to_xml.build_document_xml(json_doc)
        self.assertIn(b"Hello World", reconstructed_xml_bytes)
        self.assertIn(b"Heading1", reconstructed_xml_bytes)
        self.assertIn(b"<w:b", reconstructed_xml_bytes)

        # Step 3: XML -> JSON again
        reparsed_json = xml_to_json.parse_document(reconstructed_xml_bytes)
        self.assertEqual(reparsed_json["body"]["content"][0]["runs"][0]["text"], "Hello World")
        self.assertTrue(reparsed_json["body"]["content"][0]["runs"][0]["properties"]["bold"])

    def _verify_docx_exact_match(self, filename: str):
        """Verify 100% exact match between parent DOCX and child DOCX."""
        from pathlib import Path
        import tempfile
        import zipfile
        import xml.etree.ElementTree as ET
        from main import docx_to_json, json_to_docx
        from utils.common.json import load_json

        docx_path = Path(__file__).resolve().parent.parent.parent / "Test" / "files" / filename
        if not docx_path.exists():
            self.skipTest(f"Test/files/{filename} not found")

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            parent_json = td_path / "parent.json"
            child_docx = td_path / f"{docx_path.stem}_child.docx"
            child_json = td_path / "child.json"

            # 1. Parent DOCX -> JSON AST
            docx_to_json(docx_path, parent_json, mode="simple")

            # 2. JSON AST -> Child DOCX (using parent as template)
            json_to_docx(parent_json, child_docx, template_docx=docx_path)

            # 3. Child DOCX -> JSON AST
            docx_to_json(child_docx, child_json, mode="simple")

            # 4. Assert 100% AST roundtrip exact match (zero differences)
            d_parent = load_json(parent_json)
            d_child = load_json(child_json)

            def deep_diff(d1, d2, path=""):
                diffs = []
                if type(d1) != type(d2):
                    return [(path, "type", type(d1).__name__, type(d2).__name__)]
                if isinstance(d1, dict):
                    for k in sorted(set(d1.keys()) - set(d2.keys())):
                        diffs.append((f"{path}.{k}", "missing_in_child", d1[k], None))
                    for k in sorted(set(d2.keys()) - set(d1.keys())):
                        diffs.append((f"{path}.{k}", "extra_in_child", None, d2[k]))
                    for k in sorted(set(d1.keys()) & set(d2.keys())):
                        diffs.extend(deep_diff(d1[k], d2[k], f"{path}.{k}"))
                elif isinstance(d1, list):
                    if len(d1) != len(d2):
                        diffs.append((path, f"length mismatch {len(d1)} vs {len(d2)}", None, None))
                    for i in range(min(len(d1), len(d2))):
                        diffs.extend(deep_diff(d1[i], d2[i], f"{path}[{i}]"))
                else:
                    if d1 != d2:
                        diffs.append((path, "value mismatch", d1, d2))
                return diffs

            diffs = deep_diff(d_parent, d_child)
            self.assertEqual(diffs, [], f"AST differences found in {filename}: {diffs[:5]}")

            # 5. Assert XML DOM structural and style parity
            with zipfile.ZipFile(docx_path) as zp, zipfile.ZipFile(child_docx) as zc:
                p_doc = ET.fromstring(zp.read("word/document.xml"))
                c_doc = ET.fromstring(zc.read("word/document.xml"))

                p_paras = list(p_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"))
                c_paras = list(c_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"))
                self.assertEqual(len(p_paras), len(c_paras), f"Paragraph count mismatch in {filename}")

                p_tbls = list(p_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl"))
                c_tbls = list(c_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl"))
                self.assertEqual(len(p_tbls), len(c_tbls), f"Table count mismatch in {filename}")

                p_runs = list(p_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"))
                c_runs = list(c_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"))
                self.assertEqual(len(p_runs), len(c_runs), f"Run count mismatch in {filename}")

                p_rprs = list(p_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr"))
                c_rprs = list(c_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr"))
                self.assertEqual(len(p_rprs), len(c_rprs), f"Run properties (rPr) count mismatch in {filename}")

                p_pprs = list(p_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"))
                c_pprs = list(c_doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"))
                self.assertEqual(len(p_pprs), len(c_pprs), f"Paragraph properties (pPr) count mismatch in {filename}")

    def test_sudeep_singh_bish_roundtrip(self):
        """Verify SudeepSinghBish.docx converts to JSON and back with 100% exact match fidelity."""
        self._verify_docx_exact_match("SudeepSinghBish.docx")

    def test_apurva_jhunjhunwala_roundtrip(self):
        """Verify Apurva Jhunjhunwala.docx converts to JSON and back with 100% exact match fidelity."""
        self._verify_docx_exact_match("Apurva Jhunjhunwala.docx")

    def test_bullet_roundtrip(self):
        """Verify test_bullet.docx converts to JSON and back with 100% exact match fidelity."""
        self._verify_docx_exact_match("test_bullet.docx")


if __name__ == "__main__":
    unittest.main()
