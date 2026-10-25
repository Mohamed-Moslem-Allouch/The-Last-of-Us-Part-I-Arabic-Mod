import pefile, struct, capstone

pe = pefile.PE('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# In function 0x141fe69e4 (our subtitle format function):
# Let's inspect the original function instructions in backup/tlou-i.exe:
off = pe.get_offset_from_rva(0x141fe69e4 - base)
with open('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', 'rb') as f:
    f.seek(off)
    code = f.read(300)

for inst in cs.disasm(code, 0x141fe69e4):
    print(f'0x{inst.address:x}: {inst.mnemonic} {inst.op_str}')
    if inst.address > 0x141fe6aa0:
        break
