import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from config import DEFAULT_ENCODING, XML_DECLARATION
from utils import (
    dump_json,
    element_to_string,
    load_json,
    parse_xml_bytes,
    parse_xml_string,
    save_json,
    serialize_xml,
)


class TestUtilsConfig(unittest.TestCase):
    """Test config-driven behaviors of utils."""

    def test_serialize_xml_default(self):
        """Test serialize_xml with default settings."""
        el = ET.Element("w:root")
        xml_bytes = serialize_xml(el)
        self.assertIsInstance(xml_bytes, bytes)
        self.assertTrue(xml_bytes.startswith(b"<?xml"))
        self.assertIn(b"<w:root", xml_bytes)

    def test_serialize_xml_none_element(self):
        """Test serialize_xml returns empty bytes when element is None."""
        self.assertEqual(serialize_xml(None), b"")

    def test_serialize_xml_custom_declaration_string(self):
        """Test serialize_xml with an explicit custom declaration string."""
        el = ET.Element("customRoot")
        custom_decl = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        xml_bytes = serialize_xml(el, xml_declaration=custom_decl)
        self.assertTrue(xml_bytes.startswith(custom_decl.encode("utf-8")))

    def test_serialize_xml_custom_docx_config(self):
        """Test serialize_xml using custom docx_config override."""
        el = ET.Element("docRoot")
        custom_docx_config = {
            "encoding": "utf-8",
            "xml_declaration": '<?xml version="2.0" encoding="UTF-8"?>',
        }
        xml_bytes = serialize_xml(el, docx_config=custom_docx_config)
        self.assertTrue(xml_bytes.startswith(b'<?xml version="2.0" encoding="UTF-8"?>'))

    def test_serialize_xml_without_declaration(self):
        """Test serialize_xml when xml_declaration is False."""
        el = ET.Element("body")
        xml_bytes = serialize_xml(el, xml_declaration=False)
        self.assertFalse(xml_bytes.startswith(b"<?xml"))
        self.assertIn(b"<body", xml_bytes)

    def test_parse_xml_string_and_bytes(self):
        """Test parse_xml_string with both str and bytes."""
        xml_str = '<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:r/></w:p>'
        el_from_str = parse_xml_string(xml_str)
        self.assertIsNotNone(el_from_str)

        el_from_bytes = parse_xml_string(xml_str.encode("utf-8"))
        self.assertIsNotNone(el_from_bytes)

        el_from_bytes_helper = parse_xml_bytes(xml_str.encode("utf-8"))
        self.assertIsNotNone(el_from_bytes_helper)

    def test_element_to_string(self):
        """Test element_to_string conversions."""
        self.assertEqual(element_to_string(None), "")
        el = ET.Element("item")
        el.text = "hello"
        s = element_to_string(el)
        self.assertIn("<item>hello</item>", s)

    def test_json_load_and_save_with_custom_config(self):
        """Test load_json and save_json with custom json_config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.json")
            data = {"key": "value", "binary": b"sample-bytes"}

            save_json(data, file_path, json_config={"indent": 4, "encoding": "utf-8"})
            self.assertTrue(os.path.exists(file_path))

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Indent of 4 should produce 4 spaces
                self.assertIn("    \"key\": \"value\"", content)

            loaded = load_json(file_path, json_config={"encoding": "utf-8"})
            self.assertEqual(loaded["key"], "value")
            # Bytes are base64 encoded by default serializer
            self.assertIn("binary", loaded)


if __name__ == "__main__":
    unittest.main()
