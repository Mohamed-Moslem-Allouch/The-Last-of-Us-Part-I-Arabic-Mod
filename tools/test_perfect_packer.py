import struct

def perfect_pack_text(entries):
    """
    entries: list of (sid, text_or_bytes)
    Ensures table is strictly sorted by SID.
    Offset 0 of string block is b'UNKNOWN STRING!!!\\x00' (18 bytes).
    """
    sorted_entries = sorted(entries, key=lambda x: x[0])
    count = len(sorted_entries)
    header = struct.pack('<I', count)
    
    str_block = bytearray(b'UNKNOWN STRING!!!\x00')
    table = bytearray()
    
    for sid, text in sorted_entries:
        if isinstance(text, str):
            raw = text.encode('utf-8')
        else:
            raw = text
        off = len(str_block)
        table.extend(struct.pack('<QQ', sid, off))
        str_block.extend(raw + b'\x00')
        
    return header + table + bytes(str_block)

# Test with original eng.common
with open('c:/Users/SlouMa/Desktop/tlou1/extracted/text2/eng.common', 'rb') as f:
    orig_data = f.read()

count = struct.unpack('<I', orig_data[:4])[0]
base = 4 + count * 16
orig_entries = []
for i in range(count):
    sid, off = struct.unpack('<QQ', orig_data[4+i*16 : 20+i*16])
    end = orig_data.find(b'\x00', base + off)
    orig_entries.append((sid, orig_data[base+off:end]))

packed = perfect_pack_text(orig_entries)
print('Orig len:', len(orig_data), 'Packed len:', len(packed))
print('Difference in len:', len(packed) - len(orig_data))
