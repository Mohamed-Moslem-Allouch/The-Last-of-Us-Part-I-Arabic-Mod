import os
import struct
import ctypes
import hashlib
import zlib
from typing import Dict, List, Optional, Tuple

OODLE_PATH = r"D:\The Last of Us\oo2core_9_win64.dll"

_oodle = None

def get_oodle():
    global _oodle
    if _oodle is None:
        if not os.path.exists(OODLE_PATH):
            raise FileNotFoundError(f"Oodle DLL not found at {OODLE_PATH}")
        dll = ctypes.cdll.LoadLibrary(OODLE_PATH)
        dll.OodleLZ_Decompress.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_int
        ]
        dll.OodleLZ_Decompress.restype = ctypes.c_int

        dll.OodleLZ_Compress.argtypes = [
            ctypes.c_int, # format (e.g. 8 for Leviathan, 9 for Kraken)
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_int, # level
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        ]
        dll.OodleLZ_Compress.restype = ctypes.c_int
        _oodle = dll
    return _oodle

class PsarcEntry:
    def __init__(self, md5_hash: bytes, z_index: int, uncomp_sz: int, offset: int, index: int):
        self.md5_hash = md5_hash
        self.z_index = z_index
        self.uncomp_sz = uncomp_sz
        self.offset = offset
        self.index = index
        self.name: Optional[str] = None

class PsarcArchive:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.fp = open(filepath, "rb")
        self.entries: List[PsarcEntry] = []
        self.hash_to_entry: Dict[bytes, PsarcEntry] = {}
        self.name_to_entry: Dict[str, PsarcEntry] = {}
        self.z_sizes: List[int] = []
        self.block_sz = 65536
        self._read_header()

    def close(self):
        if self.fp and not self.fp.closed:
            self.fp.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _read_header(self):
        self.fp.seek(0)
        hdr = self.fp.read(32)
        magic, ver_hi, ver_lo, comp, toc_len, entry_sz, num_entries, block_sz, flags = struct.unpack('>4sHH4sIIIII', hdr)
        if magic != b'PSAR':
            raise ValueError(f"Not a PSARC file: {self.filepath}")
        self.block_sz = block_sz
        self.num_entries = num_entries
        self.comp = comp

        for i in range(num_entries):
            raw = self.fp.read(30)
            h = raw[:16]
            z_idx = struct.unpack('>I', raw[16:20])[0]
            uncomp_sz = int.from_bytes(raw[20:25], 'big')
            off = int.from_bytes(raw[25:30], 'big')
            entry = PsarcEntry(h, z_idx, uncomp_sz, off, i)
            self.entries.append(entry)
            self.hash_to_entry[h] = entry

        z_table_len = toc_len - 32 - num_entries * 30
        if z_table_len > 0:
            z_table_raw = self.fp.read(z_table_len)
            self.z_sizes = [struct.unpack('>H', z_table_raw[i:i+2])[0] for i in range(0, z_table_len, 2)]

        # Read entry 0 (manifest) if available
        if num_entries > 0 and self.entries[0].md5_hash == b'\x00' * 16:
            manifest_bytes = self.extract_by_entry(self.entries[0])
            # Parse names
            raw_names = manifest_bytes.split(b'\x00')
            if len(raw_names) == 1 and b'\n' in raw_names[0]:
                raw_names = manifest_bytes.split(b'\n')
            
            # Map names by calculating MD5
            for raw_name in raw_names:
                clean_name = raw_name.decode('utf-8', errors='ignore').strip('\r\n\x00')
                if not clean_name:
                    continue
                name_hash = hashlib.md5(clean_name.encode('utf-8')).digest()
                if name_hash in self.hash_to_entry:
                    ent = self.hash_to_entry[name_hash]
                    ent.name = clean_name
                    self.name_to_entry[clean_name] = ent

    def extract_by_entry(self, entry: PsarcEntry) -> bytes:
        if entry.uncomp_sz == 0:
            return b""
        oodle = get_oodle()
        self.fp.seek(entry.offset)
        out_buf = bytearray()
        rem_sz = entry.uncomp_sz
        num_blocks = (entry.uncomp_sz + self.block_sz - 1) // self.block_sz

        for b in range(num_blocks):
            target_sz = min(self.block_sz, rem_sz)
            z_sz = self.z_sizes[entry.z_index + b]
            if z_sz == 0 or z_sz == target_sz:
                # Uncompressed block
                chunk = self.fp.read(target_sz)
                out_buf.extend(chunk)
            elif self.comp == b'zlib':
                chunk = self.fp.read(z_sz)
                decomp = zlib.decompress(chunk)
                out_buf.extend(decomp)
            elif self.comp == b'oodl':
                chunk = self.fp.read(z_sz)
                dst = ctypes.create_string_buffer(target_sz)
                res = oodle.OodleLZ_Decompress(
                    chunk, z_sz,
                    dst, target_sz,
                    0, 0, 0, None, 0, None, None, None, 0, 0
                )
                if res != target_sz:
                    raise RuntimeError(f"Decompression failed for entry {entry.name or entry.index}: expected {target_sz}, got {res}")
                out_buf.extend(dst.raw[:target_sz])
            else:
                raise NotImplementedError(f"Unsupported compression {self.comp}")
            rem_sz -= target_sz

        return bytes(out_buf)

    def extract_by_name(self, name: str) -> bytes:
        if name in self.name_to_entry:
            return self.extract_by_entry(self.name_to_entry[name])
        h = hashlib.md5(name.encode('utf-8')).digest()
        if h in self.hash_to_entry:
            return self.extract_by_entry(self.hash_to_entry[h])
        raise KeyError(f"File '{name}' not found in {self.filepath}")

    def extract_by_hash(self, md5_hash: bytes) -> bytes:
        if md5_hash in self.hash_to_entry:
            return self.extract_by_entry(self.hash_to_entry[md5_hash])
        raise KeyError(f"Hash {md5_hash.hex()} not found in {self.filepath}")
