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


if __name__ == "__main__":
    unittest.main()
