import pefile, capstone, struct

pe = pefile.PE(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
tdata = bytearray(text_sec.get_data())
text_va = text_sec.VirtualAddress + image_base

# Let's inspect the exact bytes from 0x141fe6a8e to 0x141fe6bb5
start_va = 0x141fe6a8e
off = start_va - text_va
length = 0x141fe6bb5 - start_va

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
print("=== ORIGINAL CODE ===")
for inst in md.disasm(tdata[off:off+length], start_va):
    print(f"  {hex(inst.address)}: {inst.bytes.hex():<16} {inst.mnemonic:<8} {inst.op_str}")
