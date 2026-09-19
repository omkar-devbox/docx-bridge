import unittest

from config import (
    CONTENT_TYPES_NAMESPACE,
    PACKAGE_RELATIONSHIPS_NS,
    RELATIONSHIP_TYPES,
    XML_DECLARATION,
)
from parser.docx.json_to_xml import JsonToXmlParser
from parser.docx.xml_to_json import XmlToJsonParser


class TestParserConfig(unittest.TestCase):

    def test_json_to_xml_parser_relationships_references_config(self):
        """Test JsonToXmlParser uses config definitions for relationships XML."""
        parser = JsonToXmlParser()
        data = [
            {
                "id": "rId1",
                "type": "officeDocument",
                "target": "word/document.xml",
            }
        ]
        xml_bytes = parser.build_relationships_xml(data)
        xml_str = xml_bytes.decode("utf-8")

        self.assertTrue(xml_str.startswith(XML_DECLARATION))
        self.assertIn(f'xmlns="{PACKAGE_RELATIONSHIPS_NS}"', xml_str)
        self.assertIn(f'Type="{RELATIONSHIP_TYPES["officeDocument"]}"', xml_str)

    def test_json_to_xml_parser_with_custom_config(self):
        """Test JsonToXmlParser respects custom config overrides."""
        custom_docx_config = {
            "xml_declaration": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        }
        custom_rels_config = {
            "namespaces": {"package": "http://example.com/custom/relationships"},
            "types": {"officeDocument": "http://example.com/custom/officeDocument"},
        }

        parser = JsonToXmlParser(
            docx_config=custom_docx_config,
            relationships_config=custom_rels_config,
        )
        data = [
            {
                "id": "rId1",
                "type": "officeDocument",
                "target": "word/document.xml",
            }
        ]
        xml_bytes = parser.build_relationships_xml(data)
        xml_str = xml_bytes.decode("utf-8")

        self.assertTrue(xml_str.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertIn('xmlns="http://example.com/custom/relationships"', xml_str)
        self.assertIn('Type="http://example.com/custom/officeDocument"', xml_str)

    def test_parser_theme_and_content_types(self):
        """Test JsonToXmlParser and XmlToJsonParser for theme and content types."""
        json_parser = JsonToXmlParser()
        xml_parser = XmlToJsonParser()

        # Content Types
        ct_bytes = json_parser.build_content_types_xml({"defaults": {"xyz": "application/xyz"}})
        ct_str = ct_bytes.decode("utf-8") if isinstance(ct_bytes, bytes) else ct_bytes
        self.assertIn(CONTENT_TYPES_NAMESPACE, ct_str)
        self.assertIn('Extension="xyz"', ct_str)

        parsed_ct = xml_parser.parse_content_types(ct_bytes)
        self.assertIn("defaults", parsed_ct)
        self.assertEqual(parsed_ct["defaults"].get("xyz"), "application/xyz")

    def test_xml_to_json_parser_custom_relationships_config(self):
        """Test XmlToJsonParser uses custom relationships config for types & plumbing."""
        custom_rels_config = {
            "types": {
                "customDoc": "http://example.com/custom/officeDocument",
            },
            "internal_plumbing_targets": ["custom/plumbing.xml"],
        }
        xml_parser = XmlToJsonParser(relationships_config=custom_rels_config)
        rels_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'  <Relationship Id="rId1" Type="http://example.com/custom/officeDocument" Target="word/document.xml"/>'
            b'  <Relationship Id="rId2" Type="http://example.com/custom/plumbing" Target="custom/plumbing.xml"/>'
            b'</Relationships>'
        )

        # In simple mode, target in internal_plumbing_targets should be omitted
        parsed = xml_parser.parse_relationships(rels_xml, mode="simple")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["id"], "rId1")
        self.assertEqual(parsed[0]["type"], "customDoc")

    def test_parser_custom_content_types_config(self):
        """Test JsonToXmlParser and XmlToJsonParser with custom content types namespace."""
        custom_ct_config = {
            "namespace": "http://example.com/custom/content-types",
            "defaults": {"custom": "application/custom"},
            "overrides": {"/word/doc.xml": "application/custom-doc"},
        }
        json_parser = JsonToXmlParser(content_types_config=custom_ct_config)
        xml_parser = XmlToJsonParser(content_types_config=custom_ct_config)

        xml_bytes = json_parser.build_content_types_xml()
        xml_str = xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes
        self.assertIn("http://example.com/custom/content-types", xml_str)
        self.assertIn('Extension="custom"', xml_str)

        parsed = xml_parser.parse_content_types(xml_bytes)
        self.assertIn("custom", parsed["defaults"])
        self.assertEqual(parsed["defaults"]["custom"], "application/custom")


if __name__ == "__main__":
    unittest.main()

