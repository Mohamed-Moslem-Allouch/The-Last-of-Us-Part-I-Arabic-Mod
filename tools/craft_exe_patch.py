import pefile, capstone

pe = pefile.PE(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
data = text_sec.get_data()
text_va = text_sec.VirtualAddress + image_base

# Let's see the exact file offsets of:
# 1. Format string 1: <font color="#%08X">%s:</font>_ -> replace with _<font color="#%08X">:%s</font>
# 2. Format string 2: %s:_ -> replace with _:%s
off_fmt1 = 0x2e35760
off_fmt2 = 0x2e35780

new_fmt1 = b'_<font color="#%08X">:%s</font>\x00'
new_fmt2 = b'_:%s\x00'

print(f"Format 1 len: {len(new_fmt1)} (matches 32 bytes)")
print(f"Format 2 len: {len(new_fmt2)} (matches 5 bytes)")

# Function start VA: 0x141fe69e4
# File offset: 0x1fe5de4
# Function size: 0x141fe6bb5 - 0x141fe69e4 = 0x1d1 = 465 bytes
