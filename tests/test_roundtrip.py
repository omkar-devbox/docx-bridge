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


if __name__ == "__main__":
    unittest.main()

