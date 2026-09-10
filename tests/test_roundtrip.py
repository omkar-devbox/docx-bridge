"""Roundtrip test: XML -> JSON -> XML to ensure fidelity."""

import unittest
from parser.xml_to_json import XmlToJsonParser
from parser.json_to_xml import JsonToXmlParser


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

    def test_sudeep_singh_bish_roundtrip(self):
        """Verify SudeepSinghBish.docx converts to JSON and back with complete style fidelity."""
        from pathlib import Path
        import zipfile
        import xml.etree.ElementTree as ET
        from main import docx_to_json, json_to_docx

        docx_path = Path(__file__).resolve().parent.parent / "Test" / "files" / "SudeepSinghBish.docx"
        if not docx_path.exists():
            return

        json_temp = docx_path.parent / "temp_sudeep_test.json"
        docx_temp = docx_path.parent / "temp_sudeep_test.docx"

        try:
            docx_to_json(docx_path, json_temp, mode="simple")
            json_to_docx(json_temp, docx_temp)

            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            with zipfile.ZipFile(docx_path) as zo, zipfile.ZipFile(docx_temp) as zc:
                ro = ET.fromstring(zo.read('word/document.xml'))
                rc = ET.fromstring(zc.read('word/document.xml'))

            po = ro.findall('.//w:p', namespaces)
            pc = rc.findall('.//w:p', namespaces)
            self.assertEqual(len(po), len(pc))

            for i in range(len(po)):
                pPr_o = po[i].find('w:pPr', namespaces)
                pPr_c = pc[i].find('w:pPr', namespaces)
                pPr_o_tags = {elem.tag.split('}')[-1]: elem.attrib for elem in (pPr_o if pPr_o is not None else [])}
                pPr_c_tags = {elem.tag.split('}')[-1]: elem.attrib for elem in (pPr_c if pPr_c is not None else [])}
                self.assertEqual(pPr_o_tags, pPr_c_tags)

        finally:
            if json_temp.exists():
                json_temp.unlink()
            if docx_temp.exists():
                docx_temp.unlink()


if __name__ == "__main__":
    unittest.main()


