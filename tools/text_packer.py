import os
import struct
from typing import Dict, List, Tuple

def parse_text_file(filepath: str) -> List[Tuple[int, str]]:
    """
    Parses a Naughty Dog binary text file into a list of (sid, text).
    """
    entries = []
    with open(filepath, "rb") as f:
        count = struct.unpack("<I", f.read(4))[0]
        base = 4 + count * 16
        records = [struct.unpack("<QQ", f.read(16)) for _ in range(count)]
        for sid, off in records:
            f.seek(base + off)
            chars = []
            while True:
                b = f.read(1)
                if not b or b == b"\x00":
                    break
                chars.append(b)
            text = b"".join(chars).decode("utf-8", errors="replace")
            entries.append((sid, text))
    return entries

def pack_text_file(entries: List[Tuple[int, str]]) -> bytes:
    """
    Serializes a list of (sid, text) into Naughty Dog binary text file format.
    """
    count = len(entries)
    header = struct.pack("<I", count)
    str_block = bytearray()
    table = bytearray()

    for sid, text in entries:
        raw_bytes = text.encode("utf-8")
        off = len(str_block)
        table.extend(struct.pack("<QQ", sid, off))
        str_block.extend(raw_bytes + b"\x00")

    return header + table + bytes(str_block)
