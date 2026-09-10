"""Unit tests for section-wise JSON and CSS-like centralized styles."""

import unittest
from parser.xml_to_json import XmlToJsonParser
from parser.json_to_xml import JsonToXmlParser
from handlers.document import DocumentHandler
from handlers.media import MediaHandler
from handlers.styles import StylesHandler
from handlers.base import qn


SAMPLE_SECTION_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri"/>
          <w:b/>
          <w:color w:val="2F5496"/>
          <w:sz w:val="32"/>
        </w:rPr>
        <w:t>First Section Title</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:sectPr>
          <w:pgSz w:w="11906" w:h="16838" w:orient="portrait"/>
          <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
        </w:sectPr>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Times New Roman"/>
          <w:color w:val="333333"/>
          <w:sz w:val="24"/>
        </w:rPr>
        <w:t>Section 1 Paragraph</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri"/>
          <w:b/>
          <w:color w:val="2F5496"/>
          <w:sz w:val="32"/>
        </w:rPr>
        <w:t>Second Section Title</w:t>
      </w:r>
    </w:p>
    <w:sectPr>
      <w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>
      <w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


class TestSectionStyles(unittest.TestCase):
    """Test section-wise document structure and CSS-like reusable style classes."""

    def test_section_wise_parsing(self):
        """Verify XML with multiple sections parses into distinct section objects."""
        parser = XmlToJsonParser()
        data = parser.parse_document(SAMPLE_SECTION_XML, mode="simple")

        self.assertIn("sections", data)
        self.assertEqual(len(data["sections"]), 2)

        # Section 1 checks
        sec1 = data["sections"][0]
        self.assertEqual(sec1["page"]["size"], "a4")
        self.assertEqual(sec1["page"]["orientation"], "portrait")
        self.assertEqual(sec1["page"]["margins"]["top"], 1440)
        self.assertGreaterEqual(len(sec1["content"]), 2)

        # Section 2 checks
        sec2 = data["sections"][1]
        self.assertEqual(sec2["page"]["size"], "a4")
        self.assertEqual(sec2["page"]["orientation"], "landscape")
        self.assertEqual(sec2["page"]["margins"]["top"], 720)

    def test_css_like_style_deduplication(self):
        """Verify CSS-like style dictionary classes can be defined and referenced cleanly."""
        json_to_xml = JsonToXmlParser()
        doc_json = {
            "styles": {
                "TitleClass": {
                    "font": "Calibri",
                    "size": 32,
                    "color": "2F5496",
                    "bold": True
                }
            },
            "sections": [
                {
                    "content": [
                        {
                            "style": "TitleClass",
                            "text": "First Section Title"
                        }
                    ]
                }
            ]
        }
        xml_bytes = json_to_xml.build_document_xml(doc_json)
        self.assertIn(b"Calibri", xml_bytes)
        self.assertIn(b"2F5496", xml_bytes)
        self.assertIn(b"First Section Title", xml_bytes)

    def test_roundtrip_section_and_styles(self):
        """Verify JSON with styles and sections converts back to valid OpenXML preserving formatting."""
        json_to_xml = JsonToXmlParser()
        xml_to_json = XmlToJsonParser()

        doc_json = {
            "styles": {
                "TitleClass": {
                    "font": "Georgia",
                    "size": 36,
                    "color": "990000",
                    "bold": True,
                    "align": "center"
                },
                "BodyClass": {
                    "font": "Arial",
                    "size": 22,
                    "color": "222222"
                }
            },
            "sections": [
                {
                    "page": {
                        "size": "letter",
                        "orientation": "portrait",
                        "margins": {"top": 1440, "bottom": 1440, "left": 1440, "right": 1440}
                    },
                    "content": [
                        {
                            "style": "TitleClass",
                            "text": "Antigravity Architecture"
                        },
                        {
                            "style": "BodyClass",
                            "text": "Section-wise document representation with 100% fidelity."
                        }
                    ]
                }
            ]
        }

        # Convert JSON -> XML
        xml_bytes = json_to_xml.build_document_xml(doc_json)
        self.assertIn(b"Antigravity Architecture", xml_bytes)
        self.assertIn(b"Georgia", xml_bytes)
        self.assertIn(b"990000", xml_bytes)
        self.assertIn(b"center", xml_bytes)
        self.assertIn(b"12240", xml_bytes)  # letter width
        self.assertIn(b"15840", xml_bytes)  # letter height

        # Convert XML -> JSON again
        reparsed = xml_to_json.parse_document(xml_bytes, mode="simple")
        self.assertIn("sections", reparsed)
        self.assertEqual(len(reparsed["sections"]), 1)
        self.assertEqual(reparsed["sections"][0]["page"]["size"], "letter")
        self.assertEqual(reparsed["sections"][0]["content"][0]["text"], "Antigravity Architecture")

    def test_drawing_shapes_zero_raw_xml(self):
        """Verify vector shapes, groups, and paths convert cleanly without any raw XML strings."""
        handler = MediaHandler()
        shape_data = {
            "drawingType": "anchor",
            "positionH": {"relativeFrom": "page", "offset": 1000},
            "positionV": {"relativeFrom": "page", "offset": 2000},
            "extent": {"width": 500000, "height": 300000},
            "wrap": "none",
            "shapes": [
                {
                    "id": 1,
                    "name": "Custom Vector Shape",
                    "fill": "364248",
                    "stroke": "none",
                    "paths": [
                        {"d": "M 0 0 L 500000 0 L 250000 300000 Z", "width": 500000, "height": 300000}
                    ]
                }
            ]
        }

        elem = handler.to_xml(shape_data)
        self.assertIsNotNone(elem)
        self.assertIsNotNone(elem.find(f".//{qn('wpg:wgp')}"))
        self.assertIsNotNone(elem.find(f".//{qn('a:custGeom')}"))
        self.assertIsNotNone(elem.find(f".//{qn('a:solidFill')}"))

        # Reparse to JSON
        parsed_shape = handler.to_json(elem)
        self.assertNotIn("graphicDataXml", parsed_shape)
        self.assertEqual(parsed_shape["drawingType"], "shapeGroup")
        self.assertEqual(len(parsed_shape["shapes"]), 1)
        self.assertEqual(parsed_shape["shapes"][0]["fill"], "364248")
        self.assertIn("M 0 0 L 500000 0 L 250000 300000 Z", parsed_shape["shapes"][0]["paths"][0]["d"])


if __name__ == "__main__":
    unittest.main()
