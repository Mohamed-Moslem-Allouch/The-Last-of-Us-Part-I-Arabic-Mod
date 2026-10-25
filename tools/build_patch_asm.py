import pefile, capstone, struct

pe = pefile.PE(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
tdata = bytearray(text_sec.get_data())
text_va = text_sec.VirtualAddress + image_base

func_va = 0x141fe69e4
func_offset = func_va - text_va
func_len = 0x141fe6bb5 - 0x141fe69e4

print(f"func_offset: {hex(func_offset)}, func_len: {func_len} bytes")

# Helper to compute 32-bit RIP-relative displacement
def rel_disp(from_va, to_va, inst_len):
    return to_va - (from_va + inst_len)

# Helper to encode CALL rel32
def call_rel(from_va, to_va):
    disp = rel_disp(from_va, to_va, 5)
    return b'\xe8' + struct.pack('<i', disp)

# Helper to encode LEA reg, [rip + disp32]
# rex_modrm is e.g. b'\x48\x8d\x0d' for lea rcx, [rip + disp32]
# or b'\x4c\x8d\x05' for lea r8, [rip + disp32]
def lea_rip(from_va, to_va, rex_modrm):
    inst_len = len(rex_modrm) + 4
    disp = rel_disp(from_va, to_va, inst_len)
    return rex_modrm + struct.pack('<i', disp)

# Target addresses of calls and symbols:
cookie_va = 0x141fe69fd + 7 + 0x15d9204
lookup_speaker_va = 0x14048eb40
color_func_va = 0x1411b7754
sprintf_va = 0x1403c36e0
utf8_to_utf16_va = 0x141e59b18
get_layout_mode_va = 0x140504cd0
layout_text_va = 0x140578680
check_wrap_va = 0x141fe81dc
security_check_va = 0x140fa8c80

fmt1_va = image_base + pe.get_rva_from_offset(0x2e35760)
fmt2_va = image_base + pe.get_rva_from_offset(0x2e35780)
db_ptr_va = 0x141fe6aa2 + 7 + 0x1484ef7
hash_str_va = 0x141fe6a54 + 7 + 0xe4fa4d

print(f"Verified all target VAs.")
