"""Unit tests for handlers and configuration loading."""

import unittest
import xml.etree.ElementTree as ET

from config import (
    NAMESPACES,
    XML_TO_JSON_TAGS,
    JSON_TO_XML_TAGS,
    tag_to_name,
    name_to_tag,
    get_tags_for_category,
)
from handlers import (
    HandlerRegistry,
    RunHandler,
    ParagraphHandler,
    TableHandler,
    StylesHandler,
    NumberingHandler,
    SectionsHandler,
    MediaHandler,
    RelationshipsHandler,
    qn,
)


class TestConfigJson(unittest.TestCase):
    """Test loading and mapping from config JSON files."""

    def test_namespaces_loaded(self):
        self.assertIn("w", NAMESPACES)
        self.assertEqual(NAMESPACES["w"], "http://schemas.openxmlformats.org/wordprocessingml/2006/main")
        self.assertIn("r", NAMESPACES)
        self.assertIn("wp", NAMESPACES)
        self.assertIn("a", NAMESPACES)
        self.assertIn("pic", NAMESPACES)
        self.assertGreater(len(NAMESPACES), 20)

    def test_master_tags_loaded(self):
        self.assertIn("w:p", XML_TO_JSON_TAGS)
        self.assertEqual(XML_TO_JSON_TAGS["w:p"], "paragraph")
        self.assertEqual(XML_TO_JSON_TAGS["w:r"], "run")
        self.assertEqual(XML_TO_JSON_TAGS["w:tbl"], "table")
        self.assertEqual(XML_TO_JSON_TAGS["w:b"], "bold")
        self.assertEqual(XML_TO_JSON_TAGS["w:pStyle"], "style")
        self.assertEqual(XML_TO_JSON_TAGS["w:sectPr"], "sectionProperties")
        self.assertGreater(len(XML_TO_JSON_TAGS), 100)

    def test_tag_name_helpers(self):
        self.assertEqual(tag_to_name("w:p"), "paragraph")
        self.assertEqual(tag_to_name(qn("w:p")), "paragraph")
        self.assertEqual(tag_to_name("w:r"), "run")
        self.assertEqual(name_to_tag("paragraph"), "w:p")
        self.assertEqual(name_to_tag("run"), "w:r")

    def test_tag_categories(self):
        style_tags = get_tags_for_category("style")
        self.assertIn("w:b", style_tags)
        self.assertIn("w:i", style_tags)


class TestHandlers(unittest.TestCase):
    """Test each individual handler."""

    def test_run_handler(self):
        handler = RunHandler()
        xml_str = (
            f'<w:r xmlns:w="{NAMESPACES["w"]}">'
            '<w:rPr><w:b/><w:i/><w:u w:val="single"/><w:color w:val="FF0000"/><w:sz w:val="28"/></w:rPr>'
            '<w:t>Sample Text</w:t>'
            '</w:r>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertEqual(data["type"], "run")
        self.assertEqual(data["text"], "Sample Text")
        self.assertTrue(data["properties"]["bold"])
        self.assertTrue(data["properties"]["italic"])
        self.assertEqual(data["properties"]["underline"], "single")
        self.assertEqual(data["properties"]["color"], "FF0000")
        self.assertEqual(data["properties"]["fontSize"], 28)

        # Roundtrip to XML
        out_elem = handler.to_xml(data)
        out_data = handler.to_json(out_elem)
        self.assertEqual(out_data["text"], data["text"])
        self.assertEqual(out_data["properties"]["bold"], data["properties"]["bold"])
        self.assertEqual(out_data["properties"]["fontSize"], data["properties"]["fontSize"])

    def test_paragraph_handler(self):
        handler = ParagraphHandler()
        xml_str = (
            f'<w:p xmlns:w="{NAMESPACES["w"]}">'
            '<w:pPr><w:pStyle w:val="Heading2"/><w:jc w:val="center"/></w:pPr>'
            '<w:r><w:t>Section 1</w:t></w:r>'
            '</w:p>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertEqual(data["type"], "paragraph")
        self.assertEqual(data["properties"]["style"], "Heading2")
        self.assertEqual(data["properties"]["alignment"], "center")
        self.assertEqual(len(data["runs"]), 1)
        self.assertEqual(data["runs"][0]["text"], "Section 1")

        # Roundtrip to XML
        out_elem = handler.to_xml(data)
        out_data = handler.to_json(out_elem)
        self.assertEqual(out_data["properties"]["style"], "Heading2")
        self.assertEqual(out_data["runs"][0]["text"], "Section 1")

    def test_table_handler(self):
        handler = TableHandler()
        xml_str = (
            f'<w:tbl xmlns:w="{NAMESPACES["w"]}">'
            '<w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="5000" w:type="dxa"/></w:tblPr>'
            '<w:tblGrid><w:gridCol w:w="2500"/><w:gridCol w:w="2500"/></w:tblGrid>'
            '<w:tr>'
            '<w:tc><w:p><w:r><w:t>Cell 1</w:t></w:r></w:p></w:tc>'
            '<w:tc><w:p><w:r><w:t>Cell 2</w:t></w:r></w:p></w:tc>'
            '</w:tr>'
            '</w:tbl>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertEqual(data["type"], "table")
        self.assertEqual(data["properties"]["style"], "TableGrid")
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(len(data["rows"][0]["cells"]), 2)
        self.assertEqual(data["rows"][0]["cells"][0]["content"][0]["runs"][0]["text"], "Cell 1")

        # Roundtrip to XML
        out_elem = handler.to_xml(data)
        out_data = handler.to_json(out_elem)
        self.assertEqual(len(out_data["rows"]), 1)
        self.assertEqual(out_data["rows"][0]["cells"][1]["content"][0]["runs"][0]["text"], "Cell 2")

    def test_sections_handler(self):
        handler = SectionsHandler()
        xml_str = (
            f'<w:sectPr xmlns:w="{NAMESPACES["w"]}">'
            '<w:pgSz w:w="12240" w:h="15840" w:orient="portrait"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>'
            '</w:sectPr>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertIn(data["type"], ("section", "sectionProperties"))
        self.assertEqual(data["pageSize"]["width"], 12240)
        self.assertEqual(data["margins"]["top"], 1440)

        out_elem = handler.to_xml(data)
        out_data = handler.to_json(out_elem)
        self.assertEqual(out_data["pageSize"]["width"], 12240)

    def test_styles_handler(self):
        handler = StylesHandler()
        xml_str = (
            f'<w:styles xmlns:w="{NAMESPACES["w"]}">'
            '<w:style w:type="paragraph" w:styleId="CustomStyle">'
            '<w:name w:val="Custom Style"/>'
            '<w:basedOn w:val="Normal"/>'
            '</w:style>'
            '</w:styles>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertEqual(len(data["styles"]), 1)
        self.assertEqual(data["styles"][0]["id"], "CustomStyle")
        self.assertEqual(data["styles"][0]["name"], "Custom Style")

        out_elem = handler.to_xml(data)
        out_data = handler.to_json(out_elem)
        self.assertEqual(out_data["styles"][0]["id"], "CustomStyle")

    def test_numbering_handler(self):
        handler = NumberingHandler()
        xml_str = (
            f'<w:numbering xmlns:w="{NAMESPACES["w"]}">'
            '<w:abstractNum w:abstractNumId="1">'
            '<w:lvl w:ilvl="0">'
            '<w:start w:val="1"/>'
            '<w:numFmt w:val="decimal"/>'
            '<w:lvlText w:val="%1."/>'
            '</w:lvl>'
            '</w:abstractNum>'
            '<w:num w:numId="10">'
            '<w:abstractNumId w:val="1"/>'
            '</w:num>'
            '</w:numbering>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertEqual(len(data["abstractNumbering"]), 1)
        self.assertEqual(data["abstractNumbering"][0]["id"], "1")
        self.assertEqual(len(data["numbering"]), 1)
        self.assertEqual(data["numbering"][0]["numId"], "10")

        out_elem = handler.to_xml(data)
        out_data = handler.to_json(out_elem)
        self.assertEqual(out_data["numbering"][0]["numId"], "10")

    def test_media_handler(self):
        handler = MediaHandler()
        raw_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b64 = handler.encode_media_to_base64(raw_image)
        self.assertEqual(handler.decode_media_from_base64(b64), raw_image)

        xml_str = (
            f'<w:drawing xmlns:w="{NAMESPACES["w"]}" '
            f'xmlns:wp="{NAMESPACES["wp"]}" '
            f'xmlns:a="{NAMESPACES["a"]}" '
            f'xmlns:r="{NAMESPACES["r"]}">'
            '<wp:inline>'
            '<wp:extent cx="1000" cy="2000"/>'
            '<wp:docPr id="5" name="Diagram"/>'
            '<a:graphic>'
            '<a:graphicData>'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:blipFill><a:blip r:embed="rId9"/></pic:blipFill>'
            '</pic:pic>'
            '</a:graphicData>'
            '</a:graphic>'
            '</wp:inline>'
            '</w:drawing>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertEqual(data["type"], "drawing")
        self.assertEqual(data["name"], "Diagram")
        self.assertEqual(data["relationshipId"], "rId9")
        self.assertEqual(data["extent"]["cx"], 1000)

    def test_relationships_handler(self):
        handler = RelationshipsHandler()
        xml_str = (
            f'<Relationships xmlns="{RelationshipsHandler.REL_NS}">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>'
        )
        elem = ET.fromstring(xml_str)
        data = handler.to_json(elem)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "rId1")
        self.assertEqual(data[0]["target"], "styles.xml")

    def test_handler_registry(self):
        registry = HandlerRegistry()
        p_handler = registry.get_handler_for_tag(qn("w:p"))
        self.assertIsInstance(p_handler, ParagraphHandler)
        p_handler_by_type = registry.get_handler_for_type("paragraph")
        self.assertEqual(p_handler, p_handler_by_type)


if __name__ == "__main__":
    unittest.main()
