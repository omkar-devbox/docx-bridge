"""Unit tests for compact, AI-compatible, and developer-friendly JSON format."""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import NAMESPACES
from handlers import ParagraphHandler, TableHandler, DocumentHandler, qn
from parser.json_to_xml import JsonToXmlParser
from parser.xml_to_json import XmlToJsonParser


class TestSimpleFormat(unittest.TestCase):
    """Test the simplified AI and developer friendly JSON format."""

    def setUp(self):
        self.doc_handler = DocumentHandler()
        self.p_handler = ParagraphHandler()
        self.t_handler = TableHandler()
        self.json_to_xml = JsonToXmlParser()
        self.xml_to_json = XmlToJsonParser()

    def test_simple_paragraph_flat_properties(self):
        """Test converting flat paragraph dictionary directly to OpenXML."""
        data = {
            "type": "paragraph",
            "text": "Antigravity Assistant",
            "bold": True,
            "size": 28,
            "font": "Arial",
            "color": "1B2432",
            "align": "center",
            "indent": 1440,
        }
        elem = self.p_handler.to_xml(data)

        # Check paragraph properties
        jc = elem.find(f".//{qn('w:jc')}")
        self.assertIsNotNone(jc)
        self.assertEqual(jc.attrib.get(qn("w:val")), "center")

        ind = elem.find(f".//{qn('w:ind')}")
        self.assertIsNotNone(ind)
        self.assertEqual(ind.attrib.get(qn("w:left")), "1440")

        # Check run properties
        r = elem.find(qn("w:r"))
        self.assertIsNotNone(r)
        self.assertIsNotNone(r.find(f".//{qn('w:b')}"))

        sz = r.find(f".//{qn('w:sz')}")
        self.assertIsNotNone(sz)
        self.assertEqual(sz.attrib.get(qn("w:val")), "28")

        rf = r.find(f".//{qn('w:rFonts')}")
        self.assertIsNotNone(rf)
        self.assertEqual(rf.attrib.get(qn("w:ascii")), "Arial")

        col = r.find(f".//{qn('w:color')}")
        self.assertIsNotNone(col)
        self.assertEqual(col.attrib.get(qn("w:val")), "1B2432")

        t = r.find(qn("w:t"))
        self.assertIsNotNone(t)
        self.assertEqual(t.text, "Antigravity Assistant")

    def test_simple_heading(self):
        """Test heading shorthand format."""
        data = {
            "type": "heading",
            "level": 2,
            "text": "Work Experience",
        }
        elem = self.doc_handler.to_xml({"body": [data]})
        p = elem.find(f".//{qn('w:p')}")
        self.assertIsNotNone(p)

        style = p.find(f".//{qn('w:pStyle')}")
        self.assertIsNotNone(style)
        self.assertEqual(style.attrib.get(qn("w:val")), "Heading2")

        t = p.find(f".//{qn('w:t')}")
        self.assertEqual(t.text, "Work Experience")

    def test_simple_bullet_list(self):
        """Test bullet shorthand format."""
        data = {
            "type": "paragraph",
            "bullet": True,
            "text": "First milestone reached",
        }
        elem = self.p_handler.to_xml(data)
        num_pr = elem.find(f".//{qn('w:numPr')}")
        self.assertIsNotNone(num_pr)
        self.assertEqual(num_pr.find(qn("w:ilvl")).attrib.get(qn("w:val")), "0")
        self.assertEqual(num_pr.find(qn("w:numId")).attrib.get(qn("w:val")), "1")

    def test_simple_page_break(self):
        """Test page break shorthand format."""
        data = {"type": "pageBreak"}
        elem = self.doc_handler.to_xml({"body": [data]})
        br = elem.find(f".//{qn('w:br')}")
        self.assertIsNotNone(br)
        self.assertEqual(br.attrib.get(qn("w:type")), "page")

    def test_simple_table_2d_array(self):
        """Test table as a 2D matrix of plain strings."""
        data = {
            "type": "table",
            "rows": [
                ["Col 1", "Col 2"],
                ["Val 1", "Val 2"],
            ],
        }
        elem = self.t_handler.to_xml(data)
        rows = elem.findall(qn("w:tr"))
        self.assertEqual(len(rows), 2)

        # Check row 0 cells
        cells_0 = rows[0].findall(qn("w:tc"))
        self.assertEqual(len(cells_0), 2)
        t0 = cells_0[0].find(f".//{qn('w:t')}")
        t1 = cells_0[1].find(f".//{qn('w:t')}")
        self.assertEqual(t0.text, "Col 1")
        self.assertEqual(t1.text, "Col 2")

        # Check row 1 cells
        cells_1 = rows[1].findall(qn("w:tc"))
        self.assertEqual(len(cells_1), 2)
        self.assertEqual(cells_1[0].find(f".//{qn('w:t')}").text, "Val 1")

    def test_styled_table_cells(self):
        """Test table with styled cells and column spans."""
        data = {
            "type": "table",
            "rows": [
                [
                    {"text": "Merged Header", "colSpan": 2, "bold": True, "bg": "F2F2F2", "align": "center"},
                    {"text": "Regular Header", "bold": True},
                ],
                [
                    {"text": "Data 1"},
                    {"text": "Data 2"},
                    {"text": "Data 3"},
                ],
            ],
        }
        elem = self.t_handler.to_xml(data)
        rows = elem.findall(qn("w:tr"))
        self.assertEqual(len(rows), 2)

        # First cell in row 0
        cell_0 = rows[0].findall(qn("w:tc"))[0]
        grid_span = cell_0.find(f".//{qn('w:gridSpan')}")
        self.assertIsNotNone(grid_span)
        self.assertEqual(grid_span.attrib.get(qn("w:val")), "2")

        shd = cell_0.find(f".//{qn('w:shd')}")
        self.assertIsNotNone(shd)
        self.assertEqual(shd.attrib.get(qn("w:fill")), "F2F2F2")

        b = cell_0.find(f".//{qn('w:b')}")
        self.assertIsNotNone(b)

    def test_direct_body_list_document(self):
        """Test passing body directly as a list of elements."""
        doc_json = {
            "body": [
                {"type": "paragraph", "text": "Line 1"},
                {"type": "paragraph", "text": "Line 2", "bold": True},
            ]
        }
        xml_bytes = self.json_to_xml.build_document_xml(doc_json)
        self.assertIn(b"Line 1", xml_bytes)
        self.assertIn(b"Line 2", xml_bytes)
        self.assertIn(b"<w:b", xml_bytes)

    def test_simple_mode_xml_to_json(self):
        """Test parsing XML into simplified JSON mode."""
        xml_str = (
            f'<w:p xmlns:w="{NAMESPACES["w"]}">'
            '<w:pPr><w:jc w:val="center"/></w:pPr>'
            '<w:r><w:rPr><w:b/><w:sz w:val="24"/></w:rPr><w:t>Simple Title</w:t></w:r>'
            '</w:p>'
        )
        elem = ET.fromstring(xml_str)
        p_json = self.p_handler.to_json(elem, simple=True)

        self.assertEqual(p_json.get("type", "paragraph"), "paragraph")
        self.assertEqual(p_json["text"], "Simple Title")
        self.assertEqual(p_json["align"], "center")
        self.assertTrue(p_json["bold"])
        self.assertEqual(p_json["size"], 24)
        # Should not have nested runs or properties
        self.assertNotIn("runs", p_json)
        self.assertNotIn("properties", p_json)

    def test_reusable_styles_preset(self):
        """Test resolving style presets from top-level styles dictionary."""
        doc_json = {
            "styles": {
                "customTitle": {
                    "bold": True,
                    "size": 36,
                    "align": "center",
                    "color": "003366",
                }
            },
            "content": [
                {
                    "type": "p",
                    "style": "customTitle",
                    "text": "Executive Briefing",
                }
            ]
        }
        elem = self.doc_handler.to_xml(doc_json)
        p = elem.find(f".//{qn('w:p')}")
        self.assertIsNotNone(p)
        
        # Check alignment
        jc = p.find(f".//{qn('w:jc')}")
        self.assertIsNotNone(jc)
        self.assertEqual(jc.attrib.get(qn("w:val")), "center")
        
        # Check bold, size, color
        b = p.find(f".//{qn('w:b')}")
        self.assertIsNotNone(b)
        sz = p.find(f".//{qn('w:sz')}")
        self.assertEqual(sz.attrib.get(qn("w:val")), "36")
        col = p.find(f".//{qn('w:color')}")
        self.assertEqual(col.attrib.get(qn("w:val")), "003366")

    def test_page_setup_configuration(self):
        """Test converting page size and margins configuration to sectPr."""
        doc_json = {
            "page": {
                "size": "A4",
                "orientation": "landscape",
                "margins": {"top": 72, "bottom": 72, "left": 72, "right": 72}
            },
            "content": [
                {"type": "p", "text": "Landscape page test"}
            ]
        }
        elem = self.doc_handler.to_xml(doc_json)
        sect = elem.find(f".//{qn('w:sectPr')}")
        self.assertIsNotNone(sect)
        
        pg_sz = sect.find(qn("w:pgSz"))
        self.assertIsNotNone(pg_sz)
        self.assertEqual(pg_sz.attrib.get(qn("w:orient")), "landscape")
        # In A4 landscape, width > height (16838 x 11906)
        self.assertEqual(pg_sz.attrib.get(qn("w:w")), "16838")
        self.assertEqual(pg_sz.attrib.get(qn("w:h")), "11906")
        
        pg_mar = sect.find(qn("w:pgMar"))
        self.assertIsNotNone(pg_mar)
        # 72 points * 20 = 1440 twips (1 inch)
        self.assertEqual(pg_mar.attrib.get(qn("w:top")), "1440")

    def test_list_block_expansion(self):
        """Test expanding list item block into bullet and numbered paragraphs."""
        doc_json = {
            "content": [
                {
                    "type": "list",
                    "ordered": False,
                    "items": [
                        "First bullet",
                        {"text": "Nested bullet", "level": 1},
                        {"text": "Third bullet"}
                    ]
                }
            ]
        }
        elem = self.doc_handler.to_xml(doc_json)
        paragraphs = elem.findall(f".//{qn('w:p')}")
        self.assertEqual(len(paragraphs), 3)
        
        # Second paragraph should have level 1
        num_pr1 = paragraphs[1].find(f".//{qn('w:numPr')}")
        self.assertIsNotNone(num_pr1)
        self.assertEqual(num_pr1.find(qn("w:ilvl")).attrib.get(qn("w:val")), "1")

    def test_divider_block(self):
        """Test creating divider / horizontal rule."""
        doc_json = {
            "content": [
                {"type": "divider"}
            ]
        }
        elem = self.doc_handler.to_xml(doc_json)
        p = elem.find(f".//{qn('w:p')}")
        self.assertIsNotNone(p)
        bdr = p.find(f".//{qn('w:pBdr')}")
        self.assertIsNotNone(bdr)
        self.assertIsNotNone(bdr.find(qn("w:bottom")))


if __name__ == "__main__":
    unittest.main()

