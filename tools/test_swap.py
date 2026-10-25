import pefile, capstone, struct

pe = pefile.PE(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", "rb") as f:
    exe_data = bytearray(f.read())

# Check format string offsets:
off_fmt1 = 0x2e35760
off_fmt2 = 0x2e35780

print(f"Original fmt1: {repr(exe_data[off_fmt1:off_fmt1+32])}")
print(f"Original fmt2: {repr(exe_data[off_fmt2:off_fmt2+8])}")

new_fmt1 = b'_<font color="#%08X">:%s</font>\x00'
new_fmt2 = b'_:%s\x00'

assert len(new_fmt1) == 32
assert len(new_fmt2) <= 8

print("Format string patch verified.")
