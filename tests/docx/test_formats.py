import io
import unittest
import zipfile

from config import (
    CONTENT_TYPES_DATA,
    DOCX_CONFIG_DATA,
    DOCUMENT_PART,
    STYLES_PART,
    NUMBERING_PART,
    SETTINGS_PART,
    WEB_SETTINGS_PART,
    FONTS_PART,
    THEME_PART,
    FOOTNOTES_PART,
    ENDNOTES_PART,
    COMMENTS_PART,
    COMMENTS_EXTENDED_PART,
    COMMENTS_IDS_PART,
    GLOSSARY_PART,
    CORE_PROPERTIES_PART,
    APP_PROPERTIES_PART,
    CUSTOM_PROPERTIES_PART,
    DOCUMENT_RELATIONSHIPS_PART,
    PACKAGE_RELATIONSHIPS_PART,
    CONTENT_TYPES_PART,
    MEDIA_DIR,
)
from formats.docx.reader import DocxReader
from formats.docx.writer import DocxWriter


class TestDocxFormats(unittest.TestCase):

    def test_config_constants_match_jsons(self):
        """Verify that constants in config match content-types.json and docx.json."""
        self.assertEqual(DOCUMENT_PART, CONTENT_TYPES_DATA.get("document"))
        self.assertEqual(STYLES_PART, CONTENT_TYPES_DATA.get("styles"))
        self.assertEqual(NUMBERING_PART, CONTENT_TYPES_DATA.get("numbering"))
        self.assertEqual(SETTINGS_PART, CONTENT_TYPES_DATA.get("settings"))
        self.assertEqual(WEB_SETTINGS_PART, CONTENT_TYPES_DATA.get("web_settings"))
        self.assertEqual(FONTS_PART, CONTENT_TYPES_DATA.get("fonts"))
        self.assertEqual(THEME_PART, CONTENT_TYPES_DATA.get("theme"))
        self.assertEqual(FOOTNOTES_PART, CONTENT_TYPES_DATA.get("footnotes"))
        self.assertEqual(ENDNOTES_PART, CONTENT_TYPES_DATA.get("endnotes"))
        self.assertEqual(COMMENTS_PART, CONTENT_TYPES_DATA.get("comments"))
        self.assertEqual(COMMENTS_EXTENDED_PART, CONTENT_TYPES_DATA.get("comments_extended"))
        self.assertEqual(COMMENTS_IDS_PART, CONTENT_TYPES_DATA.get("comments_ids"))
        self.assertEqual(GLOSSARY_PART, CONTENT_TYPES_DATA.get("glossary"))
        self.assertEqual(CORE_PROPERTIES_PART, CONTENT_TYPES_DATA.get("core_properties"))
        self.assertEqual(APP_PROPERTIES_PART, CONTENT_TYPES_DATA.get("app_properties"))
        self.assertEqual(CUSTOM_PROPERTIES_PART, CONTENT_TYPES_DATA.get("custom_properties"))
        self.assertEqual(DOCUMENT_RELATIONSHIPS_PART, CONTENT_TYPES_DATA.get("document_relationships"))
        self.assertEqual(PACKAGE_RELATIONSHIPS_PART, CONTENT_TYPES_DATA.get("other", {}).get("package_relationships"))
        self.assertEqual(CONTENT_TYPES_PART, CONTENT_TYPES_DATA.get("other", {}).get("content_types"))

    def test_reader_and_writer_with_default_config(self):
        """Test DocxWriter writes parts and DocxReader reads parts according to config JSONs."""
        buffer = io.BytesIO()

        with DocxWriter(buffer) as writer:
            writer.write_document_xml("<w:document>doc</w:document>")
            writer.write_styles_xml("<w:styles>styles</w:styles>")
            writer.write_numbering_xml("<w:numbering>num</w:numbering>")
            writer.write_relationships_xml("<Relationships>doc_rels</Relationships>")
            writer.write_package_relationships_xml("<Relationships>pkg_rels</Relationships>")
            writer.write_content_types_xml("<Types>ct</Types>")
            writer.write_settings_xml("<w:settings>settings</w:settings>")
            writer.write_web_settings_xml("<w:webSettings>web</w:webSettings>")
            writer.write_core_properties_xml("<cp:coreProperties>core</cp:coreProperties>")
            writer.write_app_properties_xml("<ep:Properties>app</ep:Properties>")
            writer.write_custom_properties_xml("<op:Properties>custom</op:Properties>")
            writer.write_footnotes_xml("<w:footnotes>fn</w:footnotes>")
            writer.write_endnotes_xml("<w:endnotes>en</w:endnotes>")
            writer.write_comments_xml("<w:comments>comments</w:comments>")
            writer.write_comments_extended_xml("<w15:commentsEx>extended</w15:commentsEx>")
            writer.write_comments_ids_xml("<w16cid:commentsIds>ids</w16cid:commentsIds>")
            writer.write_font_table_xml("<w:fonts>fonts</w:fonts>")
            writer.write_theme_xml("<a:theme>theme</a:theme>")
            writer.write_glossary_xml("<w:glossaryDocument>glossary</w:glossaryDocument>")
            writer.write_media("image1.png", b"\x89PNG\r\n\x1a\n")
            writer.write_part("word/header1.xml", "<w:hdr>header 1</w:hdr>")
            writer.write_part("word/footer1.xml", "<w:ftr>footer 1</w:ftr>")

        buffer.seek(0)
        with DocxReader(buffer) as reader:
            self.assertEqual(reader.get_document_xml(), "<w:document>doc</w:document>")
            self.assertEqual(reader.get_styles_xml(), "<w:styles>styles</w:styles>")
            self.assertEqual(reader.get_numbering_xml(), "<w:numbering>num</w:numbering>")
            self.assertEqual(reader.get_relationships_xml(), "<Relationships>doc_rels</Relationships>")
            self.assertEqual(reader.get_package_relationships_xml(), "<Relationships>pkg_rels</Relationships>")
            self.assertEqual(reader.get_content_types_xml(), "<Types>ct</Types>")
            self.assertEqual(reader.get_settings_xml(), "<w:settings>settings</w:settings>")
            self.assertEqual(reader.get_web_settings_xml(), "<w:webSettings>web</w:webSettings>")
            self.assertEqual(reader.get_core_properties_xml(), "<cp:coreProperties>core</cp:coreProperties>")
            self.assertEqual(reader.get_app_properties_xml(), "<ep:Properties>app</ep:Properties>")
            self.assertEqual(reader.get_custom_properties_xml(), "<op:Properties>custom</op:Properties>")
            self.assertEqual(reader.get_footnotes_xml(), "<w:footnotes>fn</w:footnotes>")
            self.assertEqual(reader.get_endnotes_xml(), "<w:endnotes>en</w:endnotes>")
            self.assertEqual(reader.get_comments_xml(), "<w:comments>comments</w:comments>")
            self.assertEqual(reader.get_comments_extended_xml(), "<w15:commentsEx>extended</w15:commentsEx>")
            self.assertEqual(reader.get_comments_ids_xml(), "<w16cid:commentsIds>ids</w16cid:commentsIds>")
            self.assertEqual(reader.get_font_table_xml(), "<w:fonts>fonts</w:fonts>")
            self.assertEqual(reader.get_theme_xml(), "<a:theme>theme</a:theme>")
            self.assertEqual(reader.get_glossary_xml(), "<w:glossaryDocument>glossary</w:glossaryDocument>")

            media = reader.get_media()
            self.assertIn("word/media/image1.png", media)
            self.assertEqual(media["word/media/image1.png"], b"\x89PNG\r\n\x1a\n")

            headers = reader.get_headers_xml()
            self.assertIn("word/header1.xml", headers)
            self.assertEqual(headers["word/header1.xml"], "<w:hdr>header 1</w:hdr>")

            footers = reader.get_footers_xml()
            self.assertIn("word/footer1.xml", footers)
            self.assertEqual(footers["word/footer1.xml"], "<w:ftr>footer 1</w:ftr>")

    def test_reader_and_writer_with_custom_config(self):
        """Test DocxReader and DocxWriter dynamically use custom config dictionaries without hardcoding."""
        custom_content_types = {
            "document": "custom/main.xml",
            "styles": "custom/my_styles.xml",
            "media_dir": "custom/assets/",
            "headers": "custom/h_*.xml",
        }
        custom_docx_config = {
            "root_part": "custom/main.xml",
        }

        buffer = io.BytesIO()
        with DocxWriter(buffer, docx_config=custom_docx_config, content_types_config=custom_content_types) as writer:
            writer.write_document_xml("<custom>doc</custom>")
            writer.write_styles_xml("<custom>styles</custom>")
            writer.write_media("photo.jpg", b"fake-jpeg")
            writer.write_part("custom/h_primary.xml", "<custom>header</custom>")

        buffer.seek(0)
        with DocxReader(buffer, docx_config=custom_docx_config, content_types_config=custom_content_types) as reader:
            self.assertEqual(reader.get_document_xml(), "<custom>doc</custom>")
            self.assertEqual(reader.get_styles_xml(), "<custom>styles</custom>")

            media = reader.get_media()
            self.assertIn("custom/assets/photo.jpg", media)
            self.assertEqual(media["custom/assets/photo.jpg"], b"fake-jpeg")

            headers = reader.get_headers_xml()
            self.assertIn("custom/h_primary.xml", headers)
            self.assertEqual(headers["custom/h_primary.xml"], "<custom>header</custom>")


if __name__ == "__main__":
    unittest.main()
