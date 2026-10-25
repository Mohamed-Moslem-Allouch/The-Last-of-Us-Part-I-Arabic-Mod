import pefile, capstone

pe = pefile.PE(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
data = text_sec.get_data()
text_va = text_sec.VirtualAddress + image_base

start_va = 0x141fe6a80
offset = start_va - text_va
code = data[offset : offset + 310]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
for inst in md.disasm(code, start_va):
    print(f"{hex(inst.address)}: {inst.bytes.hex():<16} {inst.mnemonic:<8} {inst.op_str}")
