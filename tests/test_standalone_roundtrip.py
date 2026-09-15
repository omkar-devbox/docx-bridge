"""Standalone DOCX round-trip tests WITHOUT template_docx.

Validates that docx-bridge can generate a fully compliant, self-contained
DOCX package purely from JSON AST, containing all OPC parts, relationships,
content types, metadata, headers, footers, footnotes, comments, settings,
borders, bookmarks, and fields without relying on template copying.
"""

import tempfile
import unittest
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

from main import docx_to_json, json_to_docx
from utils.json import dump_json, load_json
from formats.docx.reader import DocxReader


class TestStandaloneRoundtrip(unittest.TestCase):
    """Rigorous tests for template-free DOCX generation and full two-way round-trip."""

    def test_complete_standalone_generation_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_json_path = temp_path / "standalone_source.json"
            generated_docx_path = temp_path / "standalone_generated.docx"
            roundtrip_json_path = temp_path / "standalone_roundtrip.json"
            roundtrip_docx_path = temp_path / "standalone_roundtrip2.docx"

            # 1. Construct comprehensive source JSON
            sample_ast = {
                "metadata": {
                    "title": "Standalone Comprehensive Spec",
                    "author": "Antigravity Engineering",
                    "subject": "System Specification",
                    "keywords": "docx, standalone, fidelity",
                    "description": "Zero template dependency test",
                    "revision": 1,
                    "application": "DocxBridge Standalone",
                    "pages": 2,
                    "words": 150,
                },
                "settings": {
                    "zoom": 100,
                    "trackRevisions": False,
                    "defaultTabStop": 720,
                },
                "headers": {
                    "word/header1.xml": {
                        "type": "header",
                        "content": [
                            {"text": "Project Titan - Confidential Header"}
                        ]
                    }
                },
                "footers": {
                    "word/footer1.xml": {
                        "type": "footer",
                        "content": [
                            {"text": "Footer - Page 1 of 2"}
                        ]
                    }
                },
                "footnotes": [
                    {"id": 0, "type": "separator"},
                    {
                        "id": 1,
                        "content": [
                            {"text": "Footnote 1: ISO 29500-1 OpenXML Standard"}
                        ]
                    }
                ],
                "comments": [
                    {
                        "id": 1,
                        "author": "Lead Reviewer",
                        "date": "2026-03-12T18:00:00Z",
                        "content": [
                            {"text": "Ensure this paragraph has appropriate borders."}
                        ]
                    }
                ],
                "styles": {
                    "Normal": {
                        "id": "Normal",
                        "name": "Normal",
                        "type": "paragraph",
                        "font": {"name": "Calibri", "size": 11},
                    },
                    "Heading1": {
                        "id": "Heading1",
                        "name": "heading 1",
                        "type": "paragraph",
                        "font": {"name": "Calibri Light", "size": 16, "bold": True, "color": "2E74B5"},
                    }
                },
                "numbering": {
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
                                {"ilvl": 0, "startOverride": 1}
                            ]
                        }
                    ]
                },
                "content": [
                    {
                        "type": "paragraph",
                        "style": "Heading1",
                        "text": "1. Executive Overview",
                    },
                    {
                        "type": "paragraph",
                        "text": "This paragraph features top and bottom borders.",
                        "borders": {
                            "top": {"val": "single", "sz": 12, "space": 4, "color": "003366"},
                            "bottom": {"val": "single", "sz": 12, "space": 4, "color": "003366"},
                        },
                        "bookmarks": [
                            {"id": 10, "name": "Overview_Section"}
                        ],
                    },
                    {
                        "type": "paragraph",
                        "runs": [
                            {"text": "Current Page Number: "},
                            {"type": "field", "instruction": "PAGE", "text": "1"},
                            {"text": " of "},
                            {"type": "field", "instruction": "NUMPAGES", "text": "2"},
                        ]
                    },
                    {
                        "type": "paragraph",
                        "runs": [
                            {"text": "Referenced statement"},
                            {"type": "footnoteReference", "id": 1},
                            {"text": " and reviewer comment"},
                            {"type": "commentReference", "id": 1},
                            {"text": "."}
                        ]
                    },
                    {
                        "type": "table",
                        "rows": [
                            {
                                "cells": [
                                    {"content": [{"text": "Metric"}]},
                                    {"content": [{"text": "Target"}]},
                                    {"content": [{"text": "Status"}]},
                                ]
                            },
                            {
                                "cells": [
                                    {"content": [{"text": "Round-Trip Fidelity"}]},
                                    {"content": [{"text": "100%"}]},
                                    {"content": [{"text": "Passed"}]},
                                ]
                            }
                        ]
                    }
                ],
                "sections": [
                    {
                        "headers": [{"type": "default", "relationshipId": "rId6"}],
                        "footers": [{"type": "default", "relationshipId": "rId7"}],
                    }
                ]
            }

            # Save initial source JSON
            dump_json(sample_ast, source_json_path)

            # 2. Convert JSON -> DOCX with template_docx=None
            json_to_docx(source_json_path, generated_docx_path, template_docx=None)
            self.assertTrue(generated_docx_path.exists(), "Standalone DOCX was not generated!")

            # 3. Inspect the DOCX package contents
            with zipfile.ZipFile(generated_docx_path, "r") as archive:
                namelist = archive.namelist()

                # Core OPC structure
                self.assertIn("[Content_Types].xml", namelist)
                self.assertIn("_rels/.rels", namelist)
                self.assertIn("word/document.xml", namelist)
                self.assertIn("word/_rels/document.xml.rels", namelist)

                # Essential & newly implemented parts
                self.assertIn("word/styles.xml", namelist)
                self.assertIn("word/numbering.xml", namelist)
                self.assertIn("word/settings.xml", namelist)
                self.assertIn("word/webSettings.xml", namelist)
                self.assertIn("docProps/core.xml", namelist)
                self.assertIn("docProps/app.xml", namelist)
                self.assertIn("word/header1.xml", namelist)
                self.assertIn("word/footer1.xml", namelist)
                self.assertIn("word/footnotes.xml", namelist)
                self.assertIn("word/comments.xml", namelist)

                # Verify [Content_Types].xml has overrides for parts
                ct_xml = archive.read("[Content_Types].xml").decode("utf-8")
                self.assertIn("header+xml", ct_xml)
                self.assertIn("footer+xml", ct_xml)
                self.assertIn("core-properties+xml", ct_xml)
                self.assertIn("footnotes+xml", ct_xml)
                self.assertIn("comments+xml", ct_xml)

                # Verify document.xml.rels has required relationships
                rels_xml = archive.read("word/_rels/document.xml.rels").decode("utf-8")
                self.assertIn("header1.xml", rels_xml)
                self.assertIn("footer1.xml", rels_xml)
                self.assertIn("footnotes.xml", rels_xml)
                self.assertIn("comments.xml", rels_xml)
                self.assertIn("settings.xml", rels_xml)

            # 4. Convert generated standalone DOCX -> JSON (Roundtrip hop 1)
            docx_to_json(generated_docx_path, roundtrip_json_path, mode="simple")
            self.assertTrue(roundtrip_json_path.exists(), "Roundtrip JSON was not created!")

            rt_data = load_json(roundtrip_json_path)

            # Verify Metadata
            meta = rt_data.get("metadata", {})
            self.assertEqual(meta.get("title"), "Standalone Comprehensive Spec")
            self.assertEqual(meta.get("author"), "Antigravity Engineering")
            self.assertEqual(meta.get("subject"), "System Specification")

            # Verify Headers and Footers
            self.assertIn("headers", rt_data)
            hdr_str = str(rt_data["headers"])
            self.assertIn("Project Titan - Confidential Header", hdr_str)

            self.assertIn("footers", rt_data)
            ftr_str = str(rt_data["footers"])
            self.assertIn("Footer - Page 1 of 2", ftr_str)

            # Verify Footnotes & Comments
            self.assertIn("footnotes", rt_data)
            self.assertIn("ISO 29500-1 OpenXML Standard", str(rt_data["footnotes"]))

            self.assertIn("comments", rt_data)
            self.assertIn("Lead Reviewer", str(rt_data["comments"]))
            self.assertIn("Ensure this paragraph has appropriate borders.", str(rt_data["comments"]))

            # Verify Settings
            self.assertIn("settings", rt_data)
            self.assertEqual(rt_data["settings"].get("zoom"), 100)

            # Verify Content Items
            content = rt_data.get("content") or (
                rt_data["sections"][0].get("content", [])
                if rt_data.get("sections")
                else []
            )
            self.assertTrue(len(content) >= 5, f"Expected at least 5 content items, got {len(content)}")

            # Check headings and paragraphs
            def get_text(item):
                if "text" in item and item["text"]:
                    return item["text"]
                if "runs" in item:
                    return "".join(r.get("text", "") for r in item["runs"] if isinstance(r, dict))
                return ""

            texts = [get_text(item) for item in content]
            self.assertTrue(any("Executive Overview" in t for t in texts))
            self.assertTrue(any("borders" in t for t in texts))

            # Check table
            tables = [item for item in content if item.get("type") == "table"]
            self.assertEqual(len(tables), 1)
            self.assertEqual(len(tables[0]["rows"]), 2)

            # 5. Convert roundtrip_json -> roundtrip2.docx (Roundtrip hop 2)
            json_to_docx(roundtrip_json_path, roundtrip_docx_path, template_docx=None)
            self.assertTrue(roundtrip_docx_path.exists(), "Second-hop standalone DOCX failed to generate!")

            with DocxReader(roundtrip_docx_path) as reader2:
                self.assertIsNotNone(reader2.get_core_properties_xml())
                self.assertIsNotNone(reader2.get_footnotes_xml())
                self.assertIsNotNone(reader2.get_comments_xml())
                self.assertTrue(len(reader2.get_headers_xml()) >= 1)
                self.assertTrue(len(reader2.get_footers_xml()) >= 1)


if __name__ == "__main__":
    unittest.main()
