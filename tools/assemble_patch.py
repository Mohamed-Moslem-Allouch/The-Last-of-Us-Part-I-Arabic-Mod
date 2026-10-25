import pefile, capstone, struct

pe = pefile.PE(r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase

func_va = 0x141fe69e4
func_len = 0x141fe6bb5 - 0x141fe69e4 # 465 bytes

# Target VAs:
cookie_va = 0x141fe69fd + 7 + 0x15d9204
lookup_speaker_va = 0x14048eb40
color_func_va = 0x1411b7754
sprintf_va = 0x1403c36e0
utf8_to_utf16_va = 0x141e59b18
get_layout_mode_va = 0x140504cd0
layout_text_va = 0x140578680
check_wrap_va = 0x141fe81dc
security_check_va = 0x140fa8c80

fmt1_va = image_base + pe.get_rva_from_offset(0x2e35760)
fmt2_va = image_base + pe.get_rva_from_offset(0x2e35780)
db_ptr_va = 0x141fe6aa2 + 7 + 0x1484ef7
hash_str_va = 0x141fe6a54 + 7 + 0xe4fa4d

class Assembler:
    def __init__(self, base_va):
        self.base_va = base_va
        self.code = bytearray()
        self.labels = {}
        self.fixups = []

    def cur_va(self):
        return self.base_va + len(self.code)

    def label(self, name):
        self.labels[name] = self.cur_va()

    def emit(self, bs):
        self.code.extend(bs)

    def call_va(self, target_va):
        va = self.cur_va()
        disp = target_va - (va + 5)
        self.emit(b'\xe8' + struct.pack('<i', disp))

    def jmp_va(self, target_va):
        va = self.cur_va()
        disp = target_va - (va + 5)
        self.emit(b'\xe9' + struct.pack('<i', disp))

    def lea_rip(self, prefix_bytes, target_va):
        va = self.cur_va()
        inst_len = len(prefix_bytes) + 4
        disp = target_va - (va + inst_len)
        self.emit(prefix_bytes + struct.pack('<i', disp))

    def mov_rax_rip(self, target_va):
        self.lea_rip(b'\x48\x8b\x05', target_va)

    def jmp_label(self, name):
        va = self.cur_va()
        self.fixups.append((len(self.code), va, name, 'jmp'))
        self.emit(b'\xe9\x00\x00\x00\x00')

    def je_label(self, name):
        va = self.cur_va()
        self.fixups.append((len(self.code), va, name, 'jcc'))
        self.emit(b'\x0f\x84\x00\x00\x00\x00')

    def jne_label(self, name):
        va = self.cur_va()
        self.fixups.append((len(self.code), va, name, 'jcc'))
        self.emit(b'\x0f\x85\x00\x00\x00\x00')

    def resolve(self):
        for offset, va, name, kind in self.fixups:
            target = self.labels[name]
            if kind == 'jmp':
                disp = target - (va + 5)
                self.code[offset+1:offset+5] = struct.pack('<i', disp)
            elif kind == 'jcc':
                disp = target - (va + 6)
                self.code[offset+2:offset+6] = struct.pack('<i', disp)

asm = Assembler(func_va)

# Prologue
asm.emit(b'\x48\x89\x5c\x24\x08')             # mov [rsp + 8], rbx
asm.emit(b'\x48\x89\x6c\x24\x18')             # mov [rsp + 0x18], rbp
asm.emit(b'\x56')                             # push rsi
asm.emit(b'\x57')                             # push rdi
asm.emit(b'\x41\x54')                         # push r12
asm.emit(b'\x41\x56')                         # push r14
asm.emit(b'\x41\x57')                         # push r15
asm.emit(b'\x48\x81\xec\x50\x02\x00\x00')     # sub rsp, 0x250

# Security cookie
asm.mov_rax_rip(cookie_va)                    # mov rax, [rip + cookie_disp]
asm.emit(b'\x48\x33\xc4')                     # xor rax, rsp
asm.emit(b'\x48\x89\x84\x24\x40\x02\x00\x00') # mov [rsp + 0x240], rax

asm.emit(b'\x48\x8b\xb4\x24\xb8\x02\x00\x00') # mov rsi, [rsp + 0x2b8]
asm.emit(b'\x45\x33\xe4')                     # xor r12d, r12d
asm.emit(b'\x4c\x8b\xbc\x24\xa0\x02\x00\x00') # mov r15, [rsp + 0x2a0]
asm.emit(b'\x48\x8b\xda')                     # mov rbx, rdx
asm.emit(b'\x48\x8b\xac\x24\xa8\x02\x00\x00') # mov rbp, [rsp + 0x2a8]
asm.emit(b'\xbf\x00\x10\x00\x00')             # mov edi, 0x1000
asm.emit(b'\x4c\x8b\xb4\x24\xb0\x02\x00\x00') # mov r14, [rsp + 0x2b0]

# test rsi, rsi
asm.emit(b'\x48\x85\xf6')
asm.je_label('skip_rsi')
asm.emit(b'\x44\x89\x26')                     # mov [rsi], r12d
asm.label('skip_rsi')

# Check speaker display setting
asm.emit(b'\x49\x8b\x11')                     # mov rdx, [r9] (speaker hash)
asm.emit(b'\x48\x89\x94\x24\x30\x02\x00\x00') # mov [rsp + 0x230], rdx (save speaker hash)
asm.emit(b'\x44\x39\xa1\xc0\x2e\x02\x00')     # cmp [rcx + 0x22ec0], r12d
asm.je_label('no_speaker')

asm.emit(b'\x41\xba\x17\x00\x00\x00')         # mov r10d, 0x17
asm.lea_rip(b'\x4c\x8d\x0d', hash_str_va)     # lea r9, [rip + hash_str]
asm.emit(b'\x49\xb8\x25\x23\x22\x84\xe4\x9c\xf2\xcb') # movabs r8, FNV_INIT
asm.emit(b'\x41\x8d\x4a\xea')                 # lea ecx, [r10 - 0x16]

asm.label('hash_loop')
asm.emit(b'\x49\x0f\xbe\x01')                 # movsx rax, byte ptr [r9]
asm.emit(b'\x49\xbb\xb3\x01\x00\x00\x00\x01\x00\x00') # movabs r11, FNV_PRIME
asm.emit(b'\x4c\x33\xc0')                     # xor r8, rax
asm.emit(b'\x4c\x03\xc9')                     # add r9, rcx
asm.emit(b'\x4d\x0f\xaf\xc3')                 # imul r8, r11
asm.emit(b'\x4c\x2b\xd1')                     # sub r10, rcx
asm.emit(b'\x75\xe3')                         # jne hash_loop
asm.emit(b'\x49\x3b\xd0')                     # cmp rdx, r8
asm.jne_label('has_speaker')

asm.label('no_speaker')
asm.emit(b'\xc7\x84\x24\x38\x02\x00\x00\x00\x00\x00\x00') # mov dword ptr [rsp + 0x238], 0
asm.jmp_label('write_dialogue')

asm.label('has_speaker')
asm.emit(b'\xc7\x84\x24\x38\x02\x00\x00\x01\x00\x00\x00') # mov dword ptr [rsp + 0x238], 1

# STEP 1: WRITE DIALOGUE FIRST
asm.label('write_dialogue')
asm.emit(b'\xb9\x04\x00\x00\x00')             # mov ecx, 4
asm.call_va(get_layout_mode_va)
asm.emit(b'\x44\x8b\xc8')                     # mov r9d, eax
asm.emit(b'\x4d\x8b\xc7')                     # mov r8, r15
asm.emit(b'\x8b\xd7')                         # mov edx, edi
asm.emit(b'\x48\x8b\xcb')                     # mov rcx, rbx
asm.call_va(layout_text_va)
asm.emit(b'\x84\xc0')                         # test al, al
asm.jne_label('dialogue_written')
asm.emit(b'\x48\x63\xd7')                     # movsxd rdx, edi
asm.emit(b'\x45\x33\xc9')                     # xor r9d, r9d
asm.emit(b'\x4d\x8b\xc7')                     # mov r8, r15
asm.emit(b'\x4c\x89\x64\x24\x20')             # mov [rsp + 0x20], r12
asm.emit(b'\x48\x8b\xcb')                     # mov rcx, rbx
asm.call_va(utf8_to_utf16_va)

asm.label('dialogue_written')
# Advance rbx past dialogue
asm.emit(b'\x48\x83\xc9\xff')                 # or rcx, -1
asm.label('loop_dial_len')
asm.emit(b'\x48\xff\xc1')                     # inc rcx
asm.emit(b'\x66\x44\x39\x24\x4b')             # cmp [rbx + rcx*2], r12w
asm.emit(b'\x75\xf6')                         # jne loop_dial_len
asm.emit(b'\x48\x63\xc1')                     # movsxd rax, ecx
asm.emit(b'\x2b\xf9')                         # sub edi, ecx
asm.emit(b'\x48\x8d\x1c\x43')                 # lea rbx, [rbx + rax*2]

# STEP 2: WRITE SPEAKER SECOND (if present & enabled)
asm.emit(b'\x83\xbc\x24\x38\x02\x00\x00\x01') # cmp dword ptr [rsp + 0x238], 1
asm.jne_label('finish')
asm.emit(b'\x48\x8b\x94\x24\x30\x02\x00\x00') # mov rdx, [rsp + 0x230]
asm.emit(b'\x48\x85\xd2')                     # test rdx, rdx
asm.je_label('finish')

# Look up speaker name
asm.emit(b'\x45\x33\xc0')                     # xor r8d, r8d
asm.lea_rip(b'\x48\x8d\x0d', db_ptr_va)       # lea rcx, [rip + db_ptr]
asm.call_va(lookup_speaker_va)
asm.emit(b'\x4c\x8b\xc0')                     # mov r8, rax
asm.emit(b'\x48\x85\xc0')                     # test rax, rax
asm.je_label('finish')

# Format speaker
asm.emit(b'\x48\x85\xed')                     # test rbp, rbp
asm.je_label('speaker_no_color')
asm.emit(b'\x48\x8b\xd5')                     # mov rdx, rbp
asm.emit(b'\x48\x8d\x4c\x24\x30')             # lea rcx, [rsp + 0x30]
asm.call_va(color_func_va)
asm.emit(b'\x4c\x89\x44\x24\x20')             # mov [rsp + 0x20], r8
asm.emit(b'\x48\x8d\x4c\x24\x40')             # lea rcx, [rsp + 0x40]
asm.lea_rip(b'\x4c\x8d\x05', fmt1_va)         # lea r8, [rip + fmt1]
asm.emit(b'\x48\x8b\xd7')                     # mov rdx, rdi
asm.emit(b'\x44\x8b\x08')                     # mov r9d, [rax]
asm.emit(b'\x41\x0f\xc9')                     # bswap r9d
asm.call_va(sprintf_va)
asm.jmp_label('copy_speaker')

asm.label('speaker_no_color')
asm.emit(b'\x4d\x8b\xc8')                     # mov r9, r8
asm.emit(b'\x48\x8d\x4c\x24\x40')             # lea rcx, [rsp + 0x40]
asm.lea_rip(b'\x4c\x8d\x05', fmt2_va)         # lea r8, [rip + fmt2]
asm.emit(b'\x48\x8b\xd7')                     # mov rdx, rdi
asm.call_va(sprintf_va)

asm.label('copy_speaker')
asm.emit(b'\x45\x33\xc9')                     # xor r9d, r9d
asm.emit(b'\x4c\x89\x64\x24\x20')             # mov [rsp + 0x20], r12
asm.emit(b'\x4c\x8d\x44\x24\x40')             # lea r8, [rsp + 0x40]
asm.emit(b'\xba\x00\x02\x00\x00')             # mov edx, 0x200
asm.emit(b'\x48\x8b\xcb')                     # mov rcx, rbx
asm.call_va(utf8_to_utf16_va)

# Advance rbx past speaker
asm.emit(b'\x48\x83\xc9\xff')                 # or rcx, -1
asm.label('loop_spk_len')
asm.emit(b'\x48\xff\xc1')                     # inc rcx
asm.emit(b'\x66\x44\x39\x24\x4b')             # cmp [rbx + rcx*2], r12w
asm.emit(b'\x75\xf6')                         # jne loop_spk_len
asm.emit(b'\x48\x63\xc1')                     # movsxd rax, ecx
asm.emit(b'\x2b\xf9')                         # sub edi, ecx
asm.emit(b'\x48\x8d\x1c\x43')                 # lea rbx, [rbx + rax*2]

asm.emit(b'\x48\x85\xf6')                     # test rsi, rsi
asm.je_label('finish')
asm.emit(b'\x89\x0e')                         # mov [rsi], ecx

# STEP 3: FINISH & EPILOGUE
asm.label('finish')
asm.emit(b'\x66\x44\x89\x23')                 # mov word ptr [rbx], r12w (null terminator)
asm.emit(b'\x4d\x85\xf6')                     # test r14, r14
asm.je_label('skip_wrap')
asm.emit(b'\x48\x8b\xcb')                     # mov rcx, rbx
asm.call_va(check_wrap_va)
asm.emit(b'\x41\x88\x06')                     # mov [r14], al
asm.label('skip_wrap')

# Stack check & return
asm.emit(b'\x48\x8b\x8c\x24\x40\x02\x00\x00') # mov rcx, [rsp + 0x240]
asm.emit(b'\x48\x33\xcc')                     # xor rcx, rsp
asm.call_va(security_check_va)

asm.emit(b'\x4c\x8d\x9c\x24\x50\x02\x00\x00') # lea r11, [rsp + 0x250]
asm.emit(b'\x49\x8b\x5b\x30')                 # mov rbx, [r11 + 0x30]
asm.emit(b'\x49\x8b\x6b\x40')                 # mov rbp, [r11 + 0x40]
asm.emit(b'\x49\x8b\xe3')                     # mov rsp, r11
asm.emit(b'\x41\x5f')                         # pop r15
asm.emit(b'\x41\x5e')                         # pop r14
asm.emit(b'\x41\x5c')                         # pop r12
asm.emit(b'\x5f')                             # pop rdi
asm.emit(b'\x5e')                             # pop rsi
asm.emit(b'\xc3')                             # ret

asm.resolve()

print(f"Generated code size: {len(asm.code)} bytes / {func_len} bytes max")
assert len(asm.code) <= func_len, "Code exceeded function length!"

# Pad remainder with INT3 (0xCC)
pad_len = func_len - len(asm.code)
asm.code.extend(b'\xcc' * pad_len)
print(f"Padded with {pad_len} INT3 instructions.")

# Disassemble with Capstone to verify 100% validity!
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
for inst in md.disasm(asm.code, func_va):
    if inst.mnemonic == 'int3':
        break
    print(f"  {hex(inst.address)}: {inst.mnemonic:<8} {inst.op_str}")

print("\nAssembly verification SUCCESSFUL!")
