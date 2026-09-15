"""Integration tests for DOC -> JSON, JSON -> DOC, DOC -> DOCX, and DocHandlerRegistry."""

import json
import tempfile
import unittest
from pathlib import Path

from cli import main as cli_main
from converter import doc_to_json, docx_to_json, json_to_doc, json_to_docx
from formats.doc.reader import DocReader
from formats.doc.writer import DocWriter
from handlers import DocHandlerRegistry
from handlers.doc import (
    DocDocumentHandler,
    DocMediaHandler,
    DocNumberingHandler,
    DocParagraphHandler,
    DocRunHandler,
    DocSectionsHandler,
    DocStylesHandler,
    DocTableHandler,
)


class TestDocPipeline(unittest.TestCase):
    """End-to-end integration and round-trip tests for Word 97-2003 (.doc)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_sample_doc_ast(self) -> dict:
        """Construct a comprehensive AST representation of a document."""
        return {
            "metadata": {
                "title": "Comprehensive Test Document",
                "author": "Antigravity Engineer",
                "subject": "DOC Binary Integration",
                "keywords": "word, binary, ast, python",
                "pageCount": 3,
                "wordCount": 120,
            },
            "styles": {
                "Heading 1": {"id": "Heading 1", "name": "Heading 1", "type": "paragraph"},
                "Heading 2": {"id": "Heading 2", "name": "Heading 2", "type": "paragraph"},
            },
            "numbering": {
                "num": [{"id": 1}],
                "abstract_num": [{"id": 1}],
            },
            "sections": [
                {
                    "page": {
                        "size": "a4",
                        "orientation": "portrait",
                        "margins": {
                            "top": 1440,
                            "bottom": 1440,
                            "left": 1440,
                            "right": 1440,
                        },
                    },
                    "content": [
                        {
                            "type": "paragraph",
                            "style": "Heading 1",
                            "text": "Antigravity Word Document Engine",
                            "runs": [
                                {
                                    "type": "run",
                                    "text": "Antigravity Word Document Engine",
                                    "bold": True,
                                    "size": 22.0,
                                    "color": "003366",
                                }
                            ],
                        },
                        {
                            "type": "paragraph",
                            "text": "This paragraph tests inline rich formatting across runs.",
                            "align": "center",
                            "spacing": {"before": 180, "after": 240},
                            "indent": {"left": 720, "firstLine": 360},
                            "runs": [
                                {"type": "run", "text": "This paragraph tests ", "bold": True},
                                {"type": "run", "text": "inline rich formatting ", "italic": True},
                                {"type": "run", "text": "across runs.", "underline": "single", "color": "CC0000"},
                            ],
                        },
                        {
                            "type": "paragraph",
                            "text": "Bullet item for numbering test",
                            "numbering": {"id": 1, "level": 0},
                            "runs": [{"type": "run", "text": "Bullet item for numbering test"}],
                        },
                        {
                            "type": "table",
                            "properties": {"alignment": "center"},
                            "rows": [
                                {
                                    "cells": [
                                        {"content": [{"type": "paragraph", "text": "Row 1 Cell 1"}]},
                                        {"content": [{"type": "paragraph", "text": "Row 1 Cell 2"}]},
                                    ]
                                },
                                {
                                    "cells": [
                                        {"content": [{"type": "paragraph", "text": "Row 2 Cell 1"}]},
                                        {"content": [{"type": "paragraph", "text": "Row 2 Cell 2"}]},
                                    ]
                                },
                            ],
                        },
                    ],
                }
            ],
            "headers": {
                "default": {"content": [{"type": "paragraph", "text": "Header - Antigravity Test"}]}
            },
            "footers": {
                "default": {"content": [{"type": "paragraph", "text": "Footer - Page 1"}]}
            },
        }

    def test_doc_writer_and_reader_roundtrip(self):
        """Test DOC creation from AST and subsequent parsing back to AST."""
        ast_in = self._create_sample_doc_ast()
        doc_path = self.work_dir / "test_doc.doc"

        with DocWriter(doc_path) as writer:
            writer.build_document(ast_in)

        self.assertTrue(doc_path.exists())
        self.assertGreater(doc_path.stat().st_size, 1024)

        with DocReader(doc_path) as reader:
            ast_out = reader.parse_document()

        # Verify metadata
        self.assertEqual(ast_out.get("metadata", {}).get("title"), "Comprehensive Test Document")
        self.assertEqual(ast_out.get("metadata", {}).get("author"), "Antigravity Engineer")

        # Verify sections & content
        sections = ast_out.get("sections", [])
        self.assertEqual(len(sections), 1)
        content = sections[0].get("content", [])
        self.assertGreaterEqual(len(content), 3)

        # Check heading
        self.assertIn("Antigravity Word Document Engine", content[0].get("text", ""))

        # Check table
        table_items = [c for c in content if c.get("type") == "table"]
        self.assertEqual(len(table_items), 1)
        self.assertEqual(len(table_items[0]["rows"]), 2)

        # Check headers / footers
        self.assertIn("Header", ast_out.get("headers", {}).get("default", {}).get("content", [{}])[0].get("text", ""))
        self.assertIn("Footer", ast_out.get("footers", {}).get("default", {}).get("content", [{}])[0].get("text", ""))

    def test_converter_pipelines_doc_to_json_and_json_to_doc(self):
        """Test doc_to_json and json_to_doc standalone conversion pipelines."""
        ast_in = self._create_sample_doc_ast()
        json_path = self.work_dir / "sample.json"
        doc_path = self.work_dir / "sample.doc"
        json_out_path = self.work_dir / "roundtrip.json"
        doc_out_path = self.work_dir / "roundtrip.doc"

        # 1. Save input AST JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ast_in, f, indent=2)

        # 2. JSON -> DOC
        json_to_doc(json_path, doc_path)
        self.assertTrue(doc_path.exists())

        # 3. DOC -> JSON
        doc_to_json(doc_path, json_out_path)
        self.assertTrue(json_out_path.exists())

        with open(json_out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("metadata", {}).get("title"), "Comprehensive Test Document")

        # 4. JSON -> DOC (round-trip)
        json_to_doc(json_out_path, doc_out_path)
        self.assertTrue(doc_out_path.exists())

    def test_cross_conversion_doc_and_docx(self):
        """Test converting between DOC and DOCX via shared JSON AST."""
        ast_in = self._create_sample_doc_ast()
        doc_path = self.work_dir / "cross.doc"
        docx_path = self.work_dir / "cross.docx"
        doc_from_docx_path = self.work_dir / "cross_back.doc"

        # Build DOC
        with DocWriter(doc_path) as writer:
            writer.build_document(ast_in)

        # DOC -> JSON -> DOCX
        with DocReader(doc_path) as reader:
            doc_ast = reader.parse_document()

        tmp_json = self.work_dir / "doc_ast.json"
        with open(tmp_json, "w", encoding="utf-8") as f:
            json.dump(doc_ast, f, indent=2)

        json_to_docx(tmp_json, docx_path)
        self.assertTrue(docx_path.exists())

        # DOCX -> JSON -> DOC
        tmp_docx_json = self.work_dir / "docx_ast.json"
        docx_to_json(docx_path, tmp_docx_json)
        json_to_doc(tmp_docx_json, doc_from_docx_path)
        self.assertTrue(doc_from_docx_path.exists())

    def test_cli_commands(self):
        """Test CLI command dispatching for doc-to-json and json-to-doc."""
        ast_in = self._create_sample_doc_ast()
        json_path = self.work_dir / "cli_test.json"
        doc_path = self.work_dir / "cli_test.doc"
        json_res = self.work_dir / "cli_res.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ast_in, f, indent=2)

        # CLI: json-to-doc
        cli_main(["json-to-doc", str(json_path), "-o", str(doc_path)])
        self.assertTrue(doc_path.exists())

        # CLI: doc-to-json
        cli_main(["doc-to-json", str(doc_path), "-o", str(json_res)])
        self.assertTrue(json_res.exists())

    def test_doc_handler_registry(self):
        """Verify DocHandlerRegistry registers all legacy DOC handlers."""
        reg = DocHandlerRegistry()
        self.assertIsInstance(reg.get("document"), DocDocumentHandler)
        self.assertIsInstance(reg.get("paragraph"), DocParagraphHandler)
        self.assertIsInstance(reg.get("run"), DocRunHandler)
        self.assertIsInstance(reg.get("table"), DocTableHandler)
        self.assertIsInstance(reg.get("section"), DocSectionsHandler)
        self.assertIsInstance(reg.get("styles"), DocStylesHandler)
        self.assertIsInstance(reg.get("numbering"), DocNumberingHandler)
        self.assertIsInstance(reg.get("media"), DocMediaHandler)

        # Native stream dispatch
        self.assertEqual(reg.get_handler_for_native("WordDocument"), reg.document_handler)
        self.assertEqual(reg.get_handler_for_native("1Table"), reg.document_handler)
        self.assertEqual(reg.get_handler_for_native("character"), reg.run_handler)
        self.assertEqual(reg.get_handler_for_native("paragraph"), reg.paragraph_handler)

    def test_doc_with_media_roundtrip(self):
        """Verify DOC with embedded media serializes to JSON without TypeError and roundtrips."""
        ast_in = self._create_sample_doc_ast()
        # Minimal valid 1x1 PNG bytes
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00"
            b"\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        ast_in["media"] = {
            "image1.png": {
                "bytes": png_bytes,
                "contentType": "image/png",
            }
        }
        doc_path = self.work_dir / "media_test.doc"
        json_path = self.work_dir / "media_test.json"
        doc_roundtrip = self.work_dir / "media_roundtrip.doc"

        # Write to DOC
        with DocWriter(doc_path) as writer:
            writer.build_document(ast_in)
        self.assertTrue(doc_path.exists())

        # Convert DOC -> JSON (must not raise TypeError for bytes)
        doc_to_json(doc_path, json_path)
        self.assertTrue(json_path.exists())

        # Verify JSON contains media with base64 string
        with open(json_path, "r", encoding="utf-8") as f:
            saved_json = json.load(f)
        self.assertIn("media", saved_json)
        self.assertIn("image1.png", saved_json["media"])
        self.assertIsInstance(saved_json["media"]["image1.png"]["bytes"], str)

        # Convert JSON -> DOC
        json_to_doc(json_path, doc_roundtrip)
        self.assertTrue(doc_roundtrip.exists())

        # Re-read roundtripped DOC
        with DocReader(doc_roundtrip) as reader:
            parsed = reader.parse_document()
        self.assertIn("media", parsed)
        self.assertIn("image1.png", parsed["media"])

    def test_q_doc_exact_match_roundtrip(self):
        """Verify Q.doc AST extraction and roundtrip fidelity."""
        q_doc_path = Path(__file__).resolve().parent.parent / "Test" / "files" / "Q.doc"
        if not q_doc_path.exists():
            self.skipTest("Test/files/Q.doc not present")

        # 1. Read Q.doc
        with DocReader(q_doc_path) as r:
            d_orig = r.parse_document()

        self.assertEqual(len(d_orig.get("styles", {})), 86)
        content_orig = d_orig["sections"][0]["content"]
        self.assertEqual(len(content_orig), 291)

        # Verify tables in Q.doc
        tables_orig = [c for c in content_orig if c.get("type") == "table"]
        self.assertEqual(len(tables_orig), 4)
        self.assertEqual([len(t["rows"]) for t in tables_orig], [18, 23, 33, 12])

        # 2. Write to temp DOC
        temp_doc = self.work_dir / "Q_roundtrip.doc"
        with DocWriter(temp_doc) as w:
            w.build_document(d_orig)

        # 3. Re-read temp DOC
        with DocReader(temp_doc) as r:
            d_conv = r.parse_document()

        # 4. Verify styles and content match exactly
        self.assertEqual(len(d_conv.get("styles", {})), 86)
        content_conv = d_conv["sections"][0]["content"]
        self.assertEqual(len(content_conv), 291)

        tables_conv = [c for c in content_conv if c.get("type") == "table"]
        self.assertEqual(len(tables_conv), 4)
        self.assertEqual([len(t["rows"]) for t in tables_conv], [18, 23, 33, 12])

        # Compare items
        for i, (a, b) in enumerate(zip(content_orig, content_conv)):
            self.assertEqual(a, b, f"Mismatch at content item [{i}]")


if __name__ == "__main__":
    unittest.main()
