import json
import tempfile
import unittest
from pathlib import Path

from config import (
    CONTENT_TYPES_DATA,
    CONTENT_TYPES_DEFAULTS,
    CONTENT_TYPES_NAMESPACE,
    CONTENT_TYPES_OVERRIDES,
    CORE_PROPERTIES_PART,
    DOCUMENT_PART,
    DOCUMENT_RELATIONSHIPS_PART,
    PACKAGE_RELATIONSHIPS_NS,
    RELATIONSHIP_TYPES,
    XML_DECLARATION,
)
from converter.docx.packaging import (
    build_content_types_xml,
    build_root_relationships,
    ensure_package_relationships,
    filter_standalone_relationships,
)
from converter.docx.json_to_docx import json_to_docx
from converter.docx.docx_to_json import docx_to_json
from formats.docx.reader import DocxReader


class TestConverterConfig(unittest.TestCase):

    def test_build_root_relationships_references_config(self):
        """Test build_root_relationships constructs XML from config JSON definitions."""
        xml = build_root_relationships(has_metadata=True)
        self.assertTrue(xml.startswith(XML_DECLARATION))
        self.assertIn(PACKAGE_RELATIONSHIPS_NS, xml)
        self.assertIn(RELATIONSHIP_TYPES["officeDocument"], xml)
        self.assertIn(f'Target="{DOCUMENT_PART}"', xml)
        self.assertIn(RELATIONSHIP_TYPES["coreProperties"], xml)
        self.assertIn(f'Target="{CORE_PROPERTIES_PART}"', xml)

    def test_build_content_types_xml_references_config(self):
        """Test build_content_types_xml constructs defaults and overrides from config."""
        data = {
            "styles": {},
            "numbering": {},
            "footnotes": {},
            "endnotes": {},
            "comments": {},
        }
        xml = build_content_types_xml(data)
        self.assertTrue(xml.startswith(XML_DECLARATION))
        self.assertIn(CONTENT_TYPES_NAMESPACE, xml)

        for ext, ct in CONTENT_TYPES_DEFAULTS.items():
            self.assertIn(f'Extension="{ext}" ContentType="{ct}"', xml)

        for part_key in [
            "/word/document.xml",
            "/word/styles.xml",
            "/word/numbering.xml",
            "/word/footnotes.xml",
            "/word/endnotes.xml",
            "/word/comments.xml",
            "/word/settings.xml",
            "/word/webSettings.xml",
            "/docProps/core.xml",
            "/docProps/app.xml",
        ]:
            if part_key in CONTENT_TYPES_OVERRIDES:
                self.assertIn(
                    f'PartName="{part_key}" ContentType="{CONTENT_TYPES_OVERRIDES[part_key]}"',
                    xml,
                )

    def test_ensure_package_relationships_references_config(self):
        """Test ensure_package_relationships uses RELATIONSHIP_TYPES from config."""
        rels = []
        data = {
            "styles": {},
            "numbering": {},
            "footnotes": {},
            "endnotes": {},
            "comments": {},
        }
        ensure_package_relationships(rels, data)
        types_added = {r["type"] for r in rels}

        self.assertIn(RELATIONSHIP_TYPES["styles"], types_added)
        self.assertIn(RELATIONSHIP_TYPES["numbering"], types_added)
        self.assertIn(RELATIONSHIP_TYPES["footnotes"], types_added)
        self.assertIn(RELATIONSHIP_TYPES["endnotes"], types_added)
        self.assertIn(RELATIONSHIP_TYPES["comments"], types_added)
        self.assertIn(RELATIONSHIP_TYPES["settings"], types_added)
        self.assertIn(RELATIONSHIP_TYPES["webSettings"], types_added)

    def test_roundtrip_with_config(self):
        """Test converting JSON to DOCX and back to JSON with config-driven converter."""
        test_data = {
            "sections": [
                {
                    "content": [
                        {
                            "type": "paragraph",
                            "runs": [{"text": "Testing converter config reference"}],
                        }
                    ]
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "test.json"
            docx_file = Path(tmpdir) / "test.docx"
            out_json = Path(tmpdir) / "roundtrip.json"

            json_file.write_text(json.dumps(test_data), encoding="utf-8")

            json_to_docx(json_file, docx_file)
            self.assertTrue(docx_file.exists())

            with DocxReader(docx_file) as reader:
                parts = reader.list_parts()
                self.assertIn(DOCUMENT_PART, parts)
                self.assertIn(DOCUMENT_RELATIONSHIPS_PART, parts)

            docx_to_json(docx_file, out_json)
            self.assertTrue(out_json.exists())

            loaded = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("sections", loaded)
            item = loaded["sections"][0]["content"][0]
            self.assertEqual(
                item.get("text") or item.get("runs", [{}])[0].get("text"),
                "Testing converter config reference",
            )


if __name__ == "__main__":
    unittest.main()
