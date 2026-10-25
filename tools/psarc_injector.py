import os
import struct
import hashlib
import ctypes
from typing import Dict, List, Optional
from psarc import PsarcArchive, PsarcEntry, get_oodle

def compress_block(raw_chunk: bytes) -> tuple[bytes, int]:
    oodle = get_oodle()
    target_sz = len(raw_chunk)
    comp_buf = ctypes.create_string_buffer(target_sz + 32768)
    res = oodle.OodleLZ_Compress(
        8, # Kraken
        raw_chunk, target_sz,
        comp_buf,
        4, # level normal
        None, None, None, None, 0
    )
    if 0 < res < target_sz:
        return comp_buf.raw[:res], res
    else:
        return raw_chunk, 0 # uncompressed

def patch_psarc(src_psarc_path: str, dst_psarc_path: str, replacements: Dict[str, bytes]):
    """
    Takes src_psarc_path and writes dst_psarc_path, replacing the contents of files in `replacements`.
    Any file not in `replacements` has its raw compressed blocks copied directly.
    """
    with PsarcArchive(src_psarc_path) as arc:
        num_entries = len(arc.entries)
        block_sz = arc.block_sz
        comp = arc.comp

        # Map replacements by MD5
        repl_by_hash = {}
        for rel_path, data in replacements.items():
            h = hashlib.md5(rel_path.encode('utf-8')).digest()
            repl_by_hash[h] = (rel_path, data)

        print(f"Patching {src_psarc_path}: {len(replacements)} files to replace...")

        # Temporary file to stream output
        with open(dst_psarc_path, "wb") as out_fp:
            # We will first write a placeholder header and TOC
            # Calculate preliminary TOC sizes
            # Number of entries remains the same (assuming replacing existing files)
            # What about z_sizes?
            # For each entry, calculate how many blocks it will have
            entry_num_blocks = []
            for entry in arc.entries:
                if entry.md5_hash in repl_by_hash:
                    new_sz = len(repl_by_hash[entry.md5_hash][1])
                    num_b = (new_sz + block_sz - 1) // block_sz if new_sz > 0 else 0
                else:
                    new_sz = entry.uncomp_sz
                    num_b = (new_sz + block_sz - 1) // block_sz if new_sz > 0 else 0
                entry_num_blocks.append(num_b)

            total_z_entries = sum(entry_num_blocks)
            toc_len = 32 + num_entries * 30 + total_z_entries * 2

            # Reserve space for header and TOC
            out_fp.write(b'\x00' * toc_len)

            # Now write entry data blocks
            new_entries = []
            new_z_sizes = []
            current_z_idx = 0

            for i, entry in enumerate(arc.entries):
                new_off = out_fp.tell()
                if entry.md5_hash in repl_by_hash:
                    rel_name, new_data = repl_by_hash[entry.md5_hash]
                    new_uncomp_sz = len(new_data)
                    num_b = entry_num_blocks[i]
                    for b in range(num_b):
                        chunk = new_data[b * block_sz : (b + 1) * block_sz]
                        c_bytes, z_sz = compress_block(chunk)
                        out_fp.write(c_bytes)
                        new_z_sizes.append(z_sz)
                    new_entries.append((entry.md5_hash, current_z_idx, new_uncomp_sz, new_off))
                    current_z_idx += num_b
                else:
                    # Copy existing compressed blocks directly in one batch per entry
                    new_uncomp_sz = entry.uncomp_sz
                    num_b = entry_num_blocks[i]
                    if num_b > 0:
                        arc.fp.seek(entry.offset)
                        total_entry_bytes = 0
                        for b in range(num_b):
                            z_sz = arc.z_sizes[entry.z_index + b]
                            chunk_sz = z_sz if z_sz > 0 else min(block_sz, new_uncomp_sz - b * block_sz)
                            total_entry_bytes += chunk_sz
                            new_z_sizes.append(z_sz)
                        raw_data = arc.fp.read(total_entry_bytes)
                        out_fp.write(raw_data)
                    new_entries.append((entry.md5_hash, current_z_idx, new_uncomp_sz, new_off))
                    current_z_idx += num_b

            # Now rewind and write header and TOC
            out_fp.seek(0)
            # Header
            flags = 12 # archive_flags
            hdr = struct.pack('>4sHH4sIIIII', b'PSAR', 1, 4, comp, toc_len, 30, num_entries, block_sz, flags)
            out_fp.write(hdr)

            # Entries table (30 bytes per entry)
            for md5_h, z_idx, uncomp_sz, off in new_entries:
                uncomp_bytes = uncomp_sz.to_bytes(5, 'big')
                off_bytes = off.to_bytes(5, 'big')
                rec = md5_h + struct.pack('>I', z_idx) + uncomp_bytes + off_bytes
                out_fp.write(rec)

            # Z_sizes table
            z_table_bytes = bytearray()
            for z_sz in new_z_sizes:
                z_table_bytes.extend(struct.pack('>H', z_sz))
            out_fp.write(z_table_bytes)

            assert out_fp.tell() == toc_len, f"TOC write mismatch: {out_fp.tell()} != {toc_len}"

        print(f"Successfully patched PSARC saved to {dst_psarc_path}")
