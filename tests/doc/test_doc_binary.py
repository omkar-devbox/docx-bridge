"""Unit tests for Word 97-2003 binary structures: FIB, Piece Table, SPRM, FKP, STSH, LFO, OLE metadata."""

import io
import unittest

from formats.doc.fib import Fib, FibBase, FIB_MAGIC
from formats.doc.fkp import FkpBuilder, FkpParser, FormattedParagraph, FormattedRun
from formats.doc.piece_table import PieceDescriptor, PieceTable
from formats.doc.sprm import (
    decode_character_formatting,
    decode_paragraph_formatting,
    decode_section_formatting,
    encode_character_formatting,
    encode_paragraph_formatting,
    encode_section_formatting,
    get_sprm_operand_size,
)
from formats.doc.structures import (
    EscherParser,
    HeaderFooterTable,
    ListParser,
    PropertySetStream,
    SectionTable,
    StshParser,
)


class TestDocBinaryStructures(unittest.TestCase):
    """Test individual low-level binary DOC structures."""

    def test_fib_base_roundtrip(self):
        """Test FIB Base parsing and serialization."""
        base = FibBase(
            wIdent=FIB_MAGIC,
            nFib=0x00C3,
            fcMin=1024,
            fcMac=5000,
            fWhichTblStm=True,
            fComplex=True,
        )
        data = base.to_bytes()
        self.assertEqual(len(data), 32)

        parsed = FibBase.parse(data)
        self.assertEqual(parsed.wIdent, FIB_MAGIC)
        self.assertEqual(parsed.nFib, 0x00C3)
        self.assertEqual(parsed.fcMin, 1024)
        self.assertEqual(parsed.fcMac, 5000)
        self.assertTrue(parsed.fWhichTblStm)
        self.assertEqual(parsed.table_stream_name, "1Table")

    def test_fib_full_pointers(self):
        """Test full FIB extended pointer management and subdocument lengths."""
        fib = Fib()
        fib.base.fcMin = 1024
        fib.rg_lw.ccpText = 500
        fib.rg_lw.ccpHdd = 120
        fib.set_pointer("Clx", 200, 300)
        fib.set_pointer("Stshf", 500, 600)
        fib.set_pointer("PlcfSed", 1100, 40)

        fib_bytes = fib.to_bytes()
        self.assertEqual(len(fib_bytes) % 512, 0)

        parsed = Fib.parse(fib_bytes)
        self.assertEqual(parsed.base.fcMin, 1024)
        self.assertEqual(parsed.rg_lw.ccpText, 500)
        self.assertEqual(parsed.rg_lw.ccpHdd, 120)
        self.assertEqual(parsed.get_pointer("Clx"), (200, 300))
        self.assertEqual(parsed.get_pointer("Stshf"), (500, 600))
        self.assertEqual(parsed.get_pointer("PlcfSed"), (1100, 40))

    def test_piece_table_compressed_and_unicode(self):
        """Test piece table with both 8-bit compressed ANSI and 16-bit UTF-16LE text."""
        # 8-bit text
        ansi_text = "Standard 8-bit character text"
        chunk_ansi, clx_ansi, pt_ansi = PieceTable.build_from_text(ansi_text, start_fc=1024)
        self.assertTrue(pt_ansi.pieces[0].is_compressed)
        buf_ansi = b"\x00" * 1024 + chunk_ansi
        self.assertEqual(pt_ansi.get_text(buf_ansi), ansi_text)

        # Unicode text
        unicode_text = "Unicode text: ภาษาไทย, 日本語, 🌟"
        chunk_uni, clx_uni, pt_uni = PieceTable.build_from_text(unicode_text, start_fc=1024)
        self.assertFalse(pt_uni.pieces[0].is_compressed)
        buf_uni = b"\x00" * 1024 + chunk_uni
        self.assertEqual(pt_uni.get_text(buf_uni), unicode_text)

        # Multi-piece extraction
        pt_parsed = PieceTable.parse_clx(clx_uni)
        self.assertEqual(pt_parsed.get_text(buf_uni), unicode_text)

    def test_sprm_character_formatting(self):
        """Test character formatting SPRM encoding and decoding."""
        props_in = {
            "bold": True,
            "italic": True,
            "underline": "double",
            "strike": True,
            "size": 18.0,
            "color": "00FF00",
        }
        grpprl = encode_character_formatting(props_in)
        self.assertTrue(len(grpprl) > 0)

        props_out = decode_character_formatting(grpprl)
        self.assertTrue(props_out["bold"])
        self.assertTrue(props_out["italic"])
        self.assertEqual(props_out["underline"], "double")
        self.assertTrue(props_out["strike"])
        self.assertEqual(props_out["size"], 18.0)
        self.assertEqual(props_out["color"], "00FF00")

    def test_sprm_paragraph_formatting(self):
        """Test paragraph formatting SPRM encoding and decoding."""
        props_in = {
            "align": "right",
            "spacing": {"before": 200, "after": 400, "line": 240},
            "indent": {"left": 720, "firstLine": 360},
            "numbering": {"id": 5, "level": 1},
        }
        grpprl = encode_paragraph_formatting(props_in)
        self.assertTrue(len(grpprl) > 0)

        props_out = decode_paragraph_formatting(grpprl)
        self.assertEqual(props_out["align"], "right")
        self.assertEqual(props_out["spacing"]["before"], 200)
        self.assertEqual(props_out["spacing"]["after"], 400)
        self.assertEqual(props_out["spacing"]["line"], 240)
        self.assertEqual(props_out["indent"]["left"], 720)
        self.assertEqual(props_out["indent"]["firstLine"], 360)
        self.assertEqual(props_out["numbering"]["id"], 5)
        self.assertEqual(props_out["numbering"]["level"], 1)

    def test_fkp_chpx_and_papx_pages(self):
        """Test Formatted Disk Page (FKP) generation and bin-table parsing."""
        r1 = FormattedRun(1024, 1050, encode_character_formatting({"bold": True}))
        r2 = FormattedRun(1050, 1100, encode_character_formatting({"italic": True}))

        p1 = FormattedParagraph(1024, 1100, istd=1, grpprl=encode_paragraph_formatting({"align": "center"}))

        chpx_pages, plcf_chpx = FkpBuilder.build_chpx_pages([r1, r2], start_page_num=2)
        papx_pages, plcf_papx = FkpBuilder.build_papx_pages([p1], start_page_num=3)

        fake_word_doc = b"\x00" * 1024 + chpx_pages + papx_pages

        parsed_runs = FkpParser.parse_plcf_bte_chpx(plcf_chpx, fake_word_doc)
        self.assertEqual(len(parsed_runs), 2)
        self.assertTrue(parsed_runs[0].props.get("bold"))
        self.assertTrue(parsed_runs[1].props.get("italic"))

        parsed_paras = FkpParser.parse_plcf_bte_papx(plcf_papx, fake_word_doc)
        self.assertEqual(len(parsed_paras), 1)
        self.assertEqual(parsed_paras[0].props.get("align"), "center")

    def test_stsh_and_lists(self):
        """Test STSH stylesheet and LST/LFO list tables round-trip."""
        styles_data = {
            "styles": {
                "Title": {"type": "paragraph"},
                "Subtitle": {"type": "paragraph"},
            }
        }
        stsh_bytes, style_map = StshParser.build(styles_data)
        self.assertIn("Title", style_map)
        parsed_stsh = StshParser.parse(stsh_bytes)
        self.assertIn("Title", parsed_stsh["styles"])

        num_data = {"num": [{"id": 1}, {"id": 2}]}
        lst_b, lfo_b = ListParser.build(num_data)
        parsed_num = ListParser.parse(lst_b, lfo_b)
        self.assertEqual(len(parsed_num["num"]), 2)

    def test_property_set_summary_information(self):
        """Test OLE SummaryInformation metadata parsing and building."""
        meta_in = {
            "title": "Document Title",
            "author": "Antigravity Team",
            "subject": "DOC Binary Engine",
            "keywords": "doc, word, binary",
            "pageCount": 42,
            "wordCount": 1500,
        }
        stream_bytes = PropertySetStream.build_summary_information(meta_in)
        meta_out = PropertySetStream.parse(stream_bytes)

        self.assertEqual(meta_out.get("title"), "Document Title")
        self.assertEqual(meta_out.get("author"), "Antigravity Team")
        self.assertEqual(meta_out.get("subject"), "DOC Binary Engine")
        self.assertEqual(meta_out.get("keywords"), "doc, word, binary")
        self.assertEqual(meta_out.get("pageCount"), 42)
        self.assertEqual(meta_out.get("wordCount"), 1500)


if __name__ == "__main__":
    unittest.main()
