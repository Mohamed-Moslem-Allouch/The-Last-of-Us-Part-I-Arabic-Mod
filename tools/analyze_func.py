import pefile, capstone

pe = pefile.PE(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
data = text_sec.get_data()
text_va = text_sec.VirtualAddress + image_base

start_va = 0x141fe69e4
offset = start_va - text_va
code = data[offset : offset + 465]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
instructions = list(md.disasm(code, start_va))

print(f"Total instructions in function: {len(instructions)}")
for i, inst in enumerate(instructions):
    if inst.address in (0x141fe6a42, 0x141fe6a8e, 0x141fe6a9f, 0x141fe6b04, 0x141fe6b3c, 0x141fe6b70):
        print(f"[{i:03d}] {hex(inst.address)}: {inst.mnemonic} {inst.op_str}")
