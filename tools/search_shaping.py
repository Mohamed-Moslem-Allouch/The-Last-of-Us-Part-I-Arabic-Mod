import struct, pefile

exe_path = r'c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe'
with open(exe_path, 'rb') as f:
    exe = f.read()

pe = pefile.PE(exe_path, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
text_data = text_sec.get_data()
text_va = base + text_sec.VirtualAddress

target_off = exe.find(b'String contains a glyph')
target_va = base + pe.get_rva_from_offset(target_off)
print('Target string VA:', hex(target_va))

refs = []
for i in range(len(text_data) - 4):
    disp = struct.unpack('<i', text_data[i:i+4])[0]
    rip = text_va + i + 4
    if rip + disp == target_va:
        refs.append((text_sec.PointerToRawData + i, rip))

for raw, rip in refs:
    print(f'Reference at raw=0x{raw:X}, VA=0x{rip:X}')
