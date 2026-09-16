import struct


class BinaryReader:
    """Helper for reading binary data sequentially, commonly used in .doc parsing."""

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.length = len(data)

    def seek(self, offset: int) -> None:
        """Move to a specific offset."""
        self.offset = offset

    def skip(self, size: int) -> None:
        """Skip a number of bytes."""
        self.offset += size

    def read_bytes(self, size: int) -> bytes:
        """Read an exact number of bytes."""
        if self.offset + size > self.length:
            raise EOFError(f"Cannot read {size} bytes at offset {self.offset}")
        val = self.data[self.offset : self.offset + size]
        self.offset += size
        return val

    def read_uint8(self) -> int:
        """Read an unsigned 8-bit integer."""
        if self.offset >= self.length:
            raise EOFError("Cannot read uint8: end of data reached")
        val = self.data[self.offset]
        self.offset += 1
        return val

    def read_int8(self) -> int:
        """Read a signed 8-bit integer."""
        val = self.read_uint8()
        return val - 256 if val > 127 else val

    def read_uint16(self) -> int:
        """Read an unsigned 16-bit integer (little-endian)."""
        if self.offset + 2 > self.length:
            raise EOFError("Cannot read uint16: end of data reached")
        val = struct.unpack_from("<H", self.data, self.offset)[0]
        self.offset += 2
        return val

    def read_int16(self) -> int:
        """Read a signed 16-bit integer (little-endian)."""
        if self.offset + 2 > self.length:
            raise EOFError("Cannot read int16: end of data reached")
        val = struct.unpack_from("<h", self.data, self.offset)[0]
        self.offset += 2
        return val

    def read_uint32(self) -> int:
        """Read an unsigned 32-bit integer (little-endian)."""
        if self.offset + 4 > self.length:
            raise EOFError("Cannot read uint32: end of data reached")
        val = struct.unpack_from("<I", self.data, self.offset)[0]
        self.offset += 4
        return val

    def read_int32(self) -> int:
        """Read a signed 32-bit integer (little-endian)."""
        if self.offset + 4 > self.length:
            raise EOFError("Cannot read int32: end of data reached")
        val = struct.unpack_from("<i", self.data, self.offset)[0]
        self.offset += 4
        return val
        
    def is_eof(self) -> bool:
        """Check if end of data has been reached."""
        return self.offset >= self.length


class BinaryWriter:
    """Helper for building binary data sequentially, commonly used in .doc serialization."""

    def __init__(self):
        self.buffer = bytearray()

    def write_bytes(self, data: bytes) -> None:
        """Write raw bytes."""
        self.buffer.extend(data)

    def write_uint8(self, val: int) -> None:
        """Write an unsigned 8-bit integer."""
        self.buffer.append(val & 0xFF)

    def write_int8(self, val: int) -> None:
        """Write a signed 8-bit integer."""
        self.buffer.extend(struct.pack("<b", val))

    def write_uint16(self, val: int) -> None:
        """Write an unsigned 16-bit integer (little-endian)."""
        self.buffer.extend(struct.pack("<H", val & 0xFFFF))

    def write_int16(self, val: int) -> None:
        """Write a signed 16-bit integer (little-endian)."""
        self.buffer.extend(struct.pack("<h", val))

    def write_uint32(self, val: int) -> None:
        """Write an unsigned 32-bit integer (little-endian)."""
        self.buffer.extend(struct.pack("<I", val & 0xFFFFFFFF))

    def write_int32(self, val: int) -> None:
        """Write a signed 32-bit integer (little-endian)."""
        self.buffer.extend(struct.pack("<i", val))

    def get_bytes(self) -> bytes:
        """Get the constructed bytes."""
        return bytes(self.buffer)
