"""Unit tests specifically covering handlers.doc component handlers."""

import io
import unittest

from handlers.doc import (
    DocDocumentHandler,
    DocHandlerRegistry,
    DocMediaHandler,
    DocNumberingHandler,
    DocParagraphHandler,
    DocRunHandler,
    DocSectionsHandler,
    DocStylesHandler,
    DocTableHandler,
)


class TestDocHandlers(unittest.TestCase):
    """Direct tests for individual DOC handlers."""

    def setUp(self):
        self.registry = DocHandlerRegistry()

    def test_run_handler(self):
        """Test DocRunHandler to_json and to_binary."""
        h = self.registry.run_handler

        # From dict
        r_dict = {"text": "Hello", "bold": True, "italic": True, "size": 14.0, "color": "FF0000"}
        res = h.to_json(r_dict)
        self.assertEqual(res["text"], "Hello")
        self.assertTrue(res["bold"])
        self.assertTrue(res["italic"])

        # From raw string
        res_str = h.to_json("Simple string")
        self.assertEqual(res_str["text"], "Simple string")

        # to_binary and back from bytes
        binary_bytes = h.to_binary(r_dict)
        self.assertTrue(len(binary_bytes) > 0)
        from_bytes = h.to_json(binary_bytes)
        self.assertTrue(from_bytes["bold"])
        self.assertTrue(from_bytes["italic"])
        self.assertEqual(from_bytes["size"], 14.0)

    def test_paragraph_handler(self):
        """Test DocParagraphHandler to_json and to_binary."""
        h = self.registry.paragraph_handler

        p_dict = {
            "text": "Para text",
            "align": "center",
            "spacing": {"before": 100, "after": 200},
            "indent": {"left": 720, "firstLine": 360},
            "runs": [{"type": "run", "text": "Para text", "bold": True}],
        }
        res = h.to_json(p_dict)
        self.assertEqual(res["align"], "center")
        self.assertEqual(res["spacing"]["before"], 100)
        self.assertEqual(len(res["runs"]), 1)

        # to_binary and back from bytes
        bin_bytes = h.to_binary(p_dict)
        self.assertTrue(len(bin_bytes) > 0)
        from_bytes = h.to_json(bin_bytes)
        self.assertEqual(from_bytes["align"], "center")
        self.assertEqual(from_bytes["spacing"]["before"], 100)

    def test_sections_handler(self):
        """Test DocSectionsHandler to_json and to_binary."""
        h = self.registry.sections_handler

        s_dict = {
            "page": {
                "margins": {"left": 1440, "right": 1440, "top": 720, "bottom": 720},
                "orientation": "landscape",
            }
        }
        res = h.to_json(s_dict)
        self.assertEqual(res["page"]["margins"]["left"], 1440)

        bin_bytes = h.to_binary(s_dict)
        self.assertTrue(len(bin_bytes) > 0)
        from_bytes = h.to_json(bin_bytes)
        self.assertEqual(from_bytes["page"]["margins"]["left"], 1440)

    def test_styles_handler(self):
        """Test DocStylesHandler to_json and to_binary."""
        h = self.registry.styles_handler

        styles_data = {"styles": {"Heading 1": {"id": "Heading 1", "name": "Heading 1"}}}
        bin_bytes = h.to_binary(styles_data)
        self.assertTrue(len(bin_bytes) > 0)

        from_bytes = h.to_json(bin_bytes)
        self.assertIn("Heading 1", from_bytes["styles"])

    def test_numbering_handler(self):
        """Test DocNumberingHandler to_json and to_binary."""
        h = self.registry.numbering_handler

        num_data = {"num": [{"id": 1}], "abstract_num": [{"id": 1}]}
        bin_bytes = h.to_binary(num_data)
        self.assertTrue(len(bin_bytes) > 0)

    def test_table_handler(self):
        """Test DocTableHandler to_json."""
        h = self.registry.table_handler

        t_dict = {
            "type": "table",
            "properties": {"alignment": "center", "indent": 360},
            "rows": [
                {
                    "cells": [
                        {"content": [{"type": "paragraph", "text": "Cell A"}]}
                    ]
                }
            ]
        }
        res = h.to_json(t_dict)
        self.assertEqual(res["properties"]["alignment"], "center")
        self.assertEqual(len(res["rows"]), 1)
        self.assertEqual(res["rows"][0]["cells"][0]["content"][0]["text"], "Cell A")

    def test_media_handler(self):
        """Test DocMediaHandler to_json and to_binary."""
        h = self.registry.media_handler

        m_dict = {"image1.png": {"bytes": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtestIEND\xaeB`\x82"}}
        bin_bytes = h.to_binary(m_dict)
        self.assertTrue(len(bin_bytes) > 0)

        from_bytes = h.to_json(bin_bytes)
        self.assertIn("image1.png", from_bytes)

    def test_document_handler_roundtrip(self):
        """Test DocDocumentHandler to_binary and to_json end-to-end."""
        h = self.registry.document_handler

        doc_ast = {
            "metadata": {"title": "DocHandler Test"},
            "sections": [
                {
                    "page": {"margins": {"top": 1440, "bottom": 1440, "left": 1440, "right": 1440}},
                    "content": [
                        {"type": "paragraph", "text": "Direct handler test", "runs": [{"type": "run", "text": "Direct handler test"}]}
                    ]
                }
            ]
        }
        doc_bytes = h.to_binary(doc_ast)
        self.assertTrue(len(doc_bytes) > 1024)

        parsed_ast = h.to_json(doc_bytes)
        self.assertEqual(parsed_ast.get("metadata", {}).get("title"), "DocHandler Test")
        self.assertEqual(len(parsed_ast.get("sections", [])), 1)


if __name__ == "__main__":
    unittest.main()
