"""Unit tests for Compound File Binary Format (CFBF / OLE) implementation."""

import io
import struct
import unittest
from pathlib import Path

from formats.doc.cfbf import (
    CFB_SIGNATURE,
    CFBReader,
    CFBWriter,
    DirectoryEntry,
    ENDOFCHAIN,
    FREESECT,
    STGTY_ROOT,
    STGTY_STREAM,
    VERSION_3,
)


class TestDocCFBF(unittest.TestCase):
    """Test CFBF container reading, writing, allocation tables, and directory tree."""

    def test_small_and_large_streams(self):
        """Test reading and writing small (<4096 bytes via MiniFAT) and large (>=4096 bytes via FAT) streams."""
        buf = io.BytesIO()
        writer = CFBWriter(buf)

        small_content = b"Small stream in MiniStream"
        large_content = b"Large stream data block! " * 500  # 13,000 bytes
        empty_content = b""

        writer.write_stream("SmallStream", small_content)
        writer.write_stream("LargeStream", large_content)
        writer.write_stream("EmptyStream", empty_content)
        raw_cfb = writer.build()

        reader = CFBReader(raw_cfb)
        streams = reader.list_streams()
        self.assertIn("SmallStream", streams)
        self.assertIn("LargeStream", streams)
        self.assertIn("EmptyStream", streams)

        self.assertEqual(reader.read_stream("SmallStream"), small_content)
        self.assertEqual(reader.read_stream("LargeStream"), large_content)
        self.assertEqual(reader.read_stream("EmptyStream"), empty_content)

    def test_header_validation(self):
        """Test header signature and version checking."""
        invalid_sig = b"\x00" * 512
        with self.assertRaises(ValueError):
            CFBReader(invalid_sig)

        too_small = b"\x00" * 256
        with self.assertRaises(ValueError):
            CFBReader(too_small)

    def test_multiple_streams_directory_tree(self):
        """Test directory entry Red-Black binary search tree construction with multiple sorted streams."""
        buf = io.BytesIO()
        writer = CFBWriter(buf)

        names = ["WordDocument", "1Table", "\x05SummaryInformation", "Data", "Macros", "0Table"]
        for name in names:
            writer.write_stream(name, f"Content for {name}".encode("utf-8"))

        raw_bytes = writer.build()
        reader = CFBReader(raw_bytes)

        for name in names:
            self.assertTrue(reader.has_stream(name))
            content = reader.read_stream(name)
            self.assertEqual(content, f"Content for {name}".encode("utf-8"))

    def test_missing_stream_raises_keyerror(self):
        """Test reading non-existent stream raises KeyError."""
        writer = CFBWriter(io.BytesIO())
        writer.write_stream("TestStream", b"Data")
        reader = CFBReader(writer.build())

        with self.assertRaises(KeyError):
            reader.read_stream("NonExistentStream")

    def test_directory_entry_serialization(self):
        """Test 128-byte DirectoryEntry to_bytes and parse round-trip."""
        entry = DirectoryEntry(
            index=1,
            name="TestEntry",
            entry_type=STGTY_STREAM,
            size=1234,
            start_sector=5,
        )
        b = entry.to_bytes()
        self.assertEqual(len(b), 128)

        parsed = DirectoryEntry.parse(b, 1)
        self.assertEqual(parsed.name, "TestEntry")
        self.assertEqual(parsed.entry_type, STGTY_STREAM)
        self.assertEqual(parsed.size, 1234)
        self.assertEqual(parsed.start_sector, 5)


if __name__ == "__main__":
    unittest.main()
