"""Unit tests for newly implemented DOCX features and handlers."""

import unittest
import xml.etree.ElementTree as ET

from handlers.docx import DocxHandlerRegistry
from handlers.docx.base import qn
from handlers.docx.header_footer import HeaderFooterHandler
from handlers.docx.properties import PropertiesHandler
from handlers.docx.notes import NotesHandler
from handlers.docx.comments import CommentsHandler
from handlers.docx.settings import SettingsHandler
from handlers.docx.paragraph import ParagraphHandler
from handlers.docx.run import RunHandler
from handlers.docx.numbering import NumberingHandler
from parser.xml_to_json import XmlToJsonParser
from parser.json_to_xml import JsonToXmlParser


class TestNewDocxFeatures(unittest.TestCase):
    """Test suite covering the 10 priority DOCX features."""

    def setUp(self):
        self.registry = DocxHandlerRegistry()
        self.xml_parser = XmlToJsonParser(registry=self.registry)
        self.json_parser = JsonToXmlParser(registry=self.registry)

    # ----------------------------------------------------
    # 1. Header and Footer Handlers
    # ----------------------------------------------------
    def test_header_footer_roundtrip(self):
        handler = HeaderFooterHandler()

        # Header JSON -> XML
        header_data = {
            "type": "header",
            "content": [
                {"text": "Confidential Header Document"}
            ],
        }
        hdr_element = handler.to_xml(header_data, is_footer=False)
        self.assertEqual(hdr_element.tag, qn("w:hdr"))
        p_elem = hdr_element.find(qn("w:p"))
        self.assertIsNotNone(p_elem)

        # Header XML -> JSON
        parsed_hdr = handler.to_json(hdr_element, simple=True)
        self.assertEqual(parsed_hdr["type"], "header")
        self.assertTrue(len(parsed_hdr["content"]) >= 1)
        self.assertIn("Confidential Header Document", str(parsed_hdr["content"]))

        # Footer JSON -> XML
        footer_data = {
            "type": "footer",
            "content": [
                {"text": "Page 1 of 10"}
            ],
        }
        ftr_element = handler.to_xml(footer_data, is_footer=True)
        self.assertEqual(ftr_element.tag, qn("w:ftr"))

        parsed_ftr = handler.to_json(ftr_element, simple=True)
        self.assertEqual(parsed_ftr["type"], "footer")
        self.assertIn("Page 1 of 10", str(parsed_ftr["content"]))

    # ----------------------------------------------------
    # 2. Metadata / Properties (Core & App)
    # ----------------------------------------------------
    def test_properties_metadata(self):
        handler = PropertiesHandler()

        meta_input = {
            "title": "Quarterly Financial Report",
            "author": "Alice Doe",
            "subject": "Finance",
            "keywords": "quarter, finance, 2026",
            "description": "Financial summary for Q1",
            "revision": 3,
            "application": "DocxBridge Pro",
            "appVersion": "16.0000",
            "pages": 15,
            "words": 4200,
        }

        # Build Core XML
        core_bytes = handler.to_core_xml(meta_input)
        self.assertIn(b"Quarterly Financial Report", core_bytes)
        self.assertIn(b"Alice Doe", core_bytes)
        self.assertIn(b"Finance", core_bytes)

        # Build App XML
        app_bytes = handler.to_app_xml(meta_input)
        self.assertIn(b"DocxBridge Pro", app_bytes)
        self.assertIn(b"4200", app_bytes)

        # Parse back to JSON
        core_elem = ET.fromstring(core_bytes)
        app_elem = ET.fromstring(app_bytes)
        parsed_meta = handler.to_json(core_elem, app_element=app_elem)

        self.assertEqual(parsed_meta.get("title"), "Quarterly Financial Report")
        self.assertEqual(parsed_meta.get("author"), "Alice Doe")
        self.assertEqual(parsed_meta.get("subject"), "Finance")
        self.assertEqual(parsed_meta.get("revision"), 3)
        self.assertEqual(parsed_meta.get("application"), "DocxBridge Pro")
        self.assertEqual(parsed_meta.get("words"), 4200)

    # ----------------------------------------------------
    # 3. Bookmarks
    # ----------------------------------------------------
    def test_bookmarks_in_paragraph(self):
        handler = ParagraphHandler()

        p_data = {
            "type": "paragraph",
            "text": "Jump to this section",
            "bookmarks": [
                {"id": 1, "name": "Section_Summary"}
            ],
        }

        elem = handler.to_xml(p_data)
        bm_start = elem.find(qn("w:bookmarkStart"))
        bm_end = elem.find(qn("w:bookmarkEnd"))

        self.assertIsNotNone(bm_start)
        self.assertIsNotNone(bm_end)
        self.assertEqual(bm_start.attrib.get(qn("w:name")), "Section_Summary")
        self.assertEqual(bm_start.attrib.get(qn("w:id")), "1")
        self.assertEqual(bm_end.attrib.get(qn("w:id")), "1")

        # Parse XML back to JSON
        parsed_p = handler.to_json(elem, simple=False)
        self.assertIn("bookmarks", parsed_p)
        self.assertEqual(parsed_p["bookmarks"][0]["name"], "Section_Summary")
        self.assertEqual(parsed_p["bookmarks"][0]["id"], "1")

    # ----------------------------------------------------
    # 4. Field Codes (PAGE, NUMPAGES, DATE, TOC)
    # ----------------------------------------------------
    def test_fields_in_paragraph_and_run(self):
        p_handler = ParagraphHandler()
        r_handler = RunHandler()

        # Simple field: w:fldSimple
        simple_fld_data = {
            "type": "paragraph",
            "runs": [
                {"type": "field", "instruction": "PAGE", "text": "1"}
            ]
        }
        elem = p_handler.to_xml(simple_fld_data)
        fld_elem = elem.find(qn("w:fldSimple"))
        self.assertIsNotNone(fld_elem)
        self.assertEqual(fld_elem.attrib.get(qn("w:instr")), "PAGE")

        parsed = p_handler.to_json(elem, simple=False)
        runs = parsed.get("runs", [])
        field_runs = [r for r in runs if r.get("type") == "field" or "instruction" in r]
        self.assertTrue(len(field_runs) >= 1)
        self.assertEqual(field_runs[0].get("instruction"), "PAGE")

        # Complex field via runs: instrText
        instr_run = {"type": "run", "instruction": "NUMPAGES", "text": ""}
        r_elem = r_handler.to_xml(instr_run)
        instr_elem = r_elem.find(qn("w:instrText"))
        self.assertIsNotNone(instr_elem)
        self.assertEqual(instr_elem.text, "NUMPAGES")

    # ----------------------------------------------------
    # 5. Footnotes and Endnotes
    # ----------------------------------------------------
    def test_footnotes_and_endnotes(self):
        handler = NotesHandler()

        notes_data = [
            {
                "id": 1,
                "content": [
                    {"text": "Citation: Smith et al. (2024)"}
                ]
            },
            {
                "id": 2,
                "content": [
                    {"text": "Citation: Doe et al. (2025)"}
                ]
            }
        ]

        # Footnotes XML (contains 2 auto-generated separators + 2 user notes = 4 total elements)
        fn_elem = handler.to_xml(notes_data, is_endnotes=False)
        self.assertEqual(fn_elem.tag, qn("w:footnotes"))
        self.assertEqual(len(fn_elem.findall(qn("w:footnote"))), 4)

        parsed_fn = handler.to_json(fn_elem, is_endnotes=False, simple=True)
        self.assertEqual(len(parsed_fn), 2)
        self.assertEqual(parsed_fn[0]["id"], 1)
        self.assertEqual(parsed_fn[1]["id"], 2)
        self.assertIn("Citation: Smith", str(parsed_fn[0]["content"]))

        # Endnotes XML
        en_elem = handler.to_xml(notes_data, is_endnotes=True)
        self.assertEqual(en_elem.tag, qn("w:endnotes"))
        self.assertEqual(len(en_elem.findall(qn("w:endnote"))), 4)

        parsed_en = handler.to_json(en_elem, is_endnotes=True, simple=True)
        self.assertEqual(len(parsed_en), 2)
        self.assertEqual(parsed_en[0]["id"], 1)
        self.assertEqual(parsed_en[1]["id"], 2)

    # ----------------------------------------------------
    # 6. Comments
    # ----------------------------------------------------
    def test_comments_handler(self):
        handler = CommentsHandler()

        comments_data = [
            {
                "id": 1,
                "author": "Bob Reviewer",
                "date": "2026-03-10T10:00:00Z",
                "content": [
                    {"text": "Please clarify this assumption."}
                ]
            }
        ]

        elem = handler.to_xml(comments_data)
        self.assertEqual(elem.tag, qn("w:comments"))
        c_elem = elem.find(qn("w:comment"))
        self.assertIsNotNone(c_elem)
        self.assertEqual(c_elem.attrib.get(qn("w:author")), "Bob Reviewer")

        parsed = handler.to_json(elem, simple=True)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["author"], "Bob Reviewer")
        self.assertEqual(parsed[0]["id"], 1)
        self.assertIn("clarify this assumption", str(parsed[0]["content"]))

    # ----------------------------------------------------
    # 7. Paragraph Borders (w:pBdr)
    # ----------------------------------------------------
    def test_paragraph_borders(self):
        handler = ParagraphHandler()

        p_data = {
            "type": "paragraph",
            "text": "Boxed callout paragraph",
            "borders": {
                "top": {"val": "single", "sz": 12, "space": 4, "color": "003366"},
                "bottom": {"val": "double", "sz": 24, "space": 6, "color": "CC0000"},
                "left": {"val": "single", "sz": 18, "space": 2, "color": "003366"},
                "right": {"val": "none"},
            }
        }

        elem = handler.to_xml(p_data)
        p_pr = elem.find(qn("w:pPr"))
        self.assertIsNotNone(p_pr)
        pbdr = p_pr.find(qn("w:pBdr"))
        self.assertIsNotNone(pbdr)

        top_bdr = pbdr.find(qn("w:top"))
        self.assertIsNotNone(top_bdr)
        self.assertEqual(top_bdr.attrib.get(qn("w:val")), "single")
        self.assertEqual(top_bdr.attrib.get(qn("w:sz")), "12")
        self.assertEqual(top_bdr.attrib.get(qn("w:color")), "003366")

        # Parse XML back to JSON
        parsed_p = handler.to_json(elem, simple=False)
        p_props = parsed_p.get("properties", {})
        borders = p_props.get("borders", {})
        self.assertIn("top", borders)
        self.assertEqual(borders["top"]["val"], "single")
        self.assertEqual(borders["bottom"]["val"], "double")
        self.assertEqual(borders["bottom"]["sz"], 24)

    # ----------------------------------------------------
    # 8. Settings & WebSettings
    # ----------------------------------------------------
    def test_settings_handler(self):
        handler = SettingsHandler()

        settings_data = {
            "zoom": 100,
            "trackRevisions": True,
            "proofState": {"spelling": "clean", "grammar": "clean"},
            "defaultTabStop": 720,
        }

        elem = handler.to_xml(settings_data)
        self.assertEqual(elem.tag, qn("w:settings"))
        self.assertIsNotNone(elem.find(qn("w:zoom")))
        self.assertIsNotNone(elem.find(qn("w:trackRevisions")))

        web_bytes = handler.to_web_settings_xml()
        self.assertIn(b"webSettings", web_bytes)

        parsed = handler.to_json(elem)
        self.assertEqual(parsed.get("zoom"), 100)
        self.assertTrue(parsed.get("trackRevisions"))

    # ----------------------------------------------------
    # 9. Numbering Level Overrides (lvlOverride)
    # ----------------------------------------------------
    def test_numbering_lvl_override(self):
        handler = NumberingHandler()

        num_data = {
            "abstractNumbers": [
                {
                    "id": 0,
                    "levels": [
                        {"level": 0, "format": "decimal", "text": "%1."}
                    ]
                }
            ],
            "instances": [
                {
                    "id": 1,
                    "abstractNumId": 0,
                    "levelOverrides": [
                        {
                            "ilvl": 0,
                            "startOverride": 5,
                            "lvl": {
                                "format": "upperRoman",
                                "text": "%1.",
                            }
                        }
                    ]
                }
            ]
        }

        elem = handler.to_xml(num_data)
        self.assertEqual(elem.tag, qn("w:numbering"))

        num_elem = elem.find(qn("w:num"))
        self.assertIsNotNone(num_elem)
        lvl_override = num_elem.find(qn("w:lvlOverride"))
        self.assertIsNotNone(lvl_override)
        self.assertEqual(lvl_override.attrib.get(qn("w:ilvl")), "0")

        start_override = lvl_override.find(qn("w:startOverride"))
        self.assertIsNotNone(start_override)
        self.assertEqual(start_override.attrib.get(qn("w:val")), "5")

        # Parse back to JSON
        parsed = handler.to_json(elem, simple=True)
        instances = parsed.get("instances", [])
        self.assertEqual(len(instances), 1)
        overrides = instances[0].get("levelOverrides", [])
        self.assertEqual(len(overrides), 1)
        self.assertEqual(overrides[0].get("ilvl"), 0)
        self.assertEqual(overrides[0].get("startOverride"), 5)

    # ----------------------------------------------------
    # 10. DocxHandlerRegistry Registration & Lookup
    # ----------------------------------------------------
    def test_handler_registry(self):
        reg = DocxHandlerRegistry()

        # XML tag lookups
        self.assertIsInstance(reg.get_by_tag("w:hdr"), HeaderFooterHandler)
        self.assertIsInstance(reg.get_by_tag("w:ftr"), HeaderFooterHandler)
        self.assertIsInstance(reg.get_by_tag("w:footnotes"), NotesHandler)
        self.assertIsInstance(reg.get_by_tag("w:endnotes"), NotesHandler)
        self.assertIsInstance(reg.get_by_tag("w:comments"), CommentsHandler)
        self.assertIsInstance(reg.get_by_tag("w:settings"), SettingsHandler)

        # JSON name lookups
        self.assertIsInstance(reg.get_by_type("header"), HeaderFooterHandler)
        self.assertIsInstance(reg.get_by_type("footer"), HeaderFooterHandler)
        self.assertIsInstance(reg.get_by_type("footnotes"), NotesHandler)
        self.assertIsInstance(reg.get_by_type("comments"), CommentsHandler)
        self.assertIsInstance(reg.get_by_type("settings"), SettingsHandler)


if __name__ == "__main__":
    unittest.main()
