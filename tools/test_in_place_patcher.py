import struct

def patch_common_file(orig_path, replacements_by_sid):
    """
    Takes an original .common binary file, preserves ALL original strings and offsets,
    and for modified SIDs, appends new strings to the string block and updates the table.
    """
    with open(orig_path, 'rb') as f:
        data = bytearray(f.read())
        
    count = struct.unpack('<I', data[:4])[0]
    base = 4 + count * 16
    
    # Extract string block and table
    str_block = bytearray(data[base:])
    
    # We update the table entries in place
    replaced_count = 0
    for i in range(count):
        sid, off = struct.unpack('<QQ', data[4+i*16 : 20+i*16])
        if sid in replacements_by_sid:
            new_text = replacements_by_sid[sid]
            if isinstance(new_text, str):
                raw = new_text.encode('utf-8')
            else:
                raw = new_text
            new_off = len(str_block)
            str_block.extend(raw + b'\x00')
            # Update record in table in place
            data[4+i*16+8 : 20+i*16] = struct.pack('<Q', new_off)
            replaced_count += 1
            
    # Combine header + table + new str_block
    new_data = bytes(data[:base]) + bytes(str_block)
    print(f"Patched {replaced_count} entries. Orig size: {len(data)}, New size: {len(new_data)}")
    return new_data

# Test:
orig_path = 'c:/Users/SlouMa/Desktop/tlou1/extracted/text2/eng.common'
res = patch_common_file(orig_path, {0xade282955d723c6c: "Arabic"})
print("Test completed successfully.")
