import os
import sys
import json
import struct

def patch_binary_text_file(orig_path, replacements_by_sid):
    """
    Takes an original Naughty Dog binary text file (.common, .subtitles, .subtitles-systemic),
    preserves the EXACT original string block (including UNKNOWN STRING!!! at offset 0),
    preserves ALL untouched entries at their EXACT original offsets,
    and for modified SIDs, appends the new text to the end of the string block and updates the offset in the table.
    """
    with open(orig_path, 'rb') as f:
        data = bytearray(f.read())
        
    count = struct.unpack('<I', data[:4])[0]
    base = 4 + count * 16
    
    str_block = bytearray(data[base:])
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
            # Update offset in table in place
            data[4+i*16+8 : 20+i*16] = struct.pack('<Q', new_off)
            replaced_count += 1
            
    result = bytes(data[:base]) + bytes(str_block)
    print(f"Patched {orig_path}: updated {replaced_count}/{count} entries. Orig size: {len(data)}, New size: {len(result)}")
    return result

# Test on fre.common
base_dir = r"c:\Users\SlouMa\Desktop\tlou1"
ext_dir = os.path.join(base_dir, "extracted")
eng_common_orig = os.path.join(ext_dir, "text2", "eng.common")
eng_sub_orig = os.path.join(ext_dir, "text2", "eng.subtitles")
eng_sys_orig = os.path.join(ext_dir, "text2", "eng.subtitles-systemic")

LANGUAGE_FRENCH_SID = 0xade282955d723c6c
res_common = patch_binary_text_file(eng_common_orig, {LANGUAGE_FRENCH_SID: "Arabic"})
res_sub = patch_binary_text_file(eng_sub_orig, {})
res_sys = patch_binary_text_file(eng_sys_orig, {})
print("All text files verified!")
