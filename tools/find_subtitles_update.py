import pefile, capstone

pe = pefile.PE('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Look at Subtitles::Update
# Subtitles::Update is at offset 0x2e358f5 in .rdata
# Let's find code references to Subtitles::Update string
with open('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', 'rb') as f:
    exe = f.read()

p = exe.find(b'void __cdecl Subtitles::Update(void)')
rva = pe.get_rva_from_offset(p)
str_va = base + rva
print('String VA:', hex(str_va))

text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
with open('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', 'rb') as f:
    f.seek(text_sec.PointerToRawData)
    text = f.read(text_sec.SizeOfRawData)

for i in range(len(text)-7):
    if text[i] == 0x48 and text[i+1] == 0x8d:
        disp = int.from_bytes(text[i+3:i+7], byteorder='little', signed=True)
        inst_va = base + text_sec.VirtualAddress + i
        if inst_va + 7 + disp == str_va:
            print('Found Subtitles::Update at VA:', hex(inst_va))
            break
