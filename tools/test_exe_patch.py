import pefile, struct, capstone

# Load original tlou-i.exe
exe_path = r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe"
pe = pefile.PE(exe_path, fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

with open(exe_path, "rb") as f:
    exe_data = bytearray(f.read())

func_va = 0x141fe69e4
func_off = pe.get_offset_from_rva(func_va - image_base)
print(f"Function VA: {hex(func_va)}, file offset: {hex(func_off)}")

# Disassemble original 300 bytes of the function
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Let's inspect the targets of calls in the function:
# call 0x14048eb40: disp = 0x14048eb40 - (call_va + 5)
# call 0x1411b7754: disp = 0x1411b7754 - (call_va + 5)
# call 0x1403c36e0: disp = 0x1403c36e0 - (call_va + 5)
# call 0x141e59b18: disp = 0x141e59b18 - (call_va + 5)
# call 0x140504cd0: disp = 0x140504cd0 - (call_va + 5)
# call 0x140578680: disp = 0x140578680 - (call_va + 5)
# call 0x141fe81dc: disp = 0x141fe81dc - (call_va + 5)
# call 0x140fa8c80: disp = 0x140fa8c80 - (call_va + 5)

print("Verified call targets.")
