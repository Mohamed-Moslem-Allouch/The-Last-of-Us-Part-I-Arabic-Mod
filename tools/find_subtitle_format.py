import pefile, struct, capstone

pe = pefile.PE(r'D:\The Last of Us\tlou-i.exe', fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(r'D:\The Last of Us\tlou-i.exe', 'rb') as f:
    data = f.read()

pos1 = data.find(b'<font color="#%08X">%s:</font> ')
pos2 = data.find(b'%s: ', 0x2e35500)
print(f'pos1: {hex(pos1)}, pos2: {hex(pos2)}')

va1 = image_base + pe.get_rva_from_offset(pos1)
va2 = image_base + pe.get_rva_from_offset(pos2)
print(f'va1: {hex(va1)}, va2: {hex(va2)}')

text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
tdata = text_sec.get_data()
text_va = text_sec.VirtualAddress + image_base

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
refs = []
for i in range(len(tdata) - 7):
    disp = struct.unpack('<i', tdata[i+3:i+7])[0]
    next_va = text_va + i + 7
    if next_va + disp in (va1, va2):
        target = next_va + disp
        refs.append((text_va + i, target))

print(f'Found {len(refs)} code references:')
for va, target in refs:
    print(f'  Ref at {hex(va)} -> {hex(target)}')
    offset = va - text_va
    code = tdata[max(0, offset - 30) : offset + 70]
    for inst in md.disasm(code, va - 30):
        print(f'    {hex(inst.address)}: {inst.mnemonic} {inst.op_str}')
