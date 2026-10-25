import os, pefile, struct, capstone

def patch_tlou_exe(exe_path: str, backup_path: str):
    print(f"Patching executable: {exe_path}...")
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(exe_path, backup_path)
        print(f"Created backup at {backup_path}")

    with open(backup_path, "rb") as f:
        data = bytearray(f.read())

    # 1. Patch format strings in .rdata
    # Offset 0x2e35760: <font color="#%08X">%s:</font>_ ->  <font color="#%08X">:%s</font>
    off_fmt1 = 0x2e35760
    new_fmt1 = b' <font color="#%08X">:%s</font>\x00'
    assert len(new_fmt1) == 32
    data[off_fmt1:off_fmt1+32] = new_fmt1
    print("  Patched colored speaker format string:  <font color=\"#%08X\">:%s</font>")

    # Offset 0x2e35780: %s:_ ->  :%s
    off_fmt2 = 0x2e35780
    new_fmt2 = b' :%s\x00\x00\x00\x00'
    data[off_fmt2:off_fmt2+len(new_fmt2)] = new_fmt2
    print("  Patched uncolored speaker format string:  :%s")

    # 2. Patch function 0x141fe69e4 in .text (file offset 0x1fe5de4)
    # Target: Dialogue first, Speaker second
    # Function VA: 0x141fe69e4
    # Image base: 0x140000000
    pe = pefile.PE(backup_path, fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    text_sec = [s for s in pe.sections if s.Name.decode().strip('\x00') == '.text'][0]
    text_va = text_sec.VirtualAddress + image_base

    func_va = 0x141fe69e4
    func_off = pe.get_offset_from_rva(func_va - image_base)
    func_len = 0x141fe6bb5 - 0x141fe69e4 # 465 bytes

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

        def lea_rip(self, prefix_bytes, target_va):
            va = self.cur_va()
            inst_len = len(prefix_bytes) + 4
            disp = target_va - (va + inst_len)
            self.emit(prefix_bytes + struct.pack('<i', disp))

        def jmp_near(self, name):
            va = self.cur_va()
            self.fixups.append((len(self.code), va, name, 'jmp_near'))
            self.emit(b'\xe9\x00\x00\x00\x00')

        def je_near(self, name):
            va = self.cur_va()
            self.fixups.append((len(self.code), va, name, 'jcc_near'))
            self.emit(b'\x0f\x84\x00\x00\x00\x00')

        def jne_near(self, name):
            va = self.cur_va()
            self.fixups.append((len(self.code), va, name, 'jcc_near'))
            self.emit(b'\x0f\x85\x00\x00\x00\x00')

        def jmp_short(self, name):
            va = self.cur_va()
            self.fixups.append((len(self.code), va, name, 'jmp_short'))
            self.emit(b'\xeb\x00')

        def je_short(self, name):
            va = self.cur_va()
            self.fixups.append((len(self.code), va, name, 'jcc_short'))
            self.emit(b'\x74\x00')

        def jne_short(self, name):
            va = self.cur_va()
            self.fixups.append((len(self.code), va, name, 'jcc_short'))
            self.emit(b'\x75\x00')

        def resolve(self):
            for offset, va, name, kind in self.fixups:
                target = self.labels[name]
                if kind == 'jmp_short':
                    disp = target - (va + 2)
                    assert -128 <= disp <= 127, f"Jump to {name} out of short range ({disp})"
                    self.code[offset+1] = disp & 0xff
                elif kind == 'jcc_short':
                    disp = target - (va + 2)
                    assert -128 <= disp <= 127, f"Jcc to {name} out of short range ({disp})"
                    self.code[offset+1] = disp & 0xff
                elif kind == 'jmp_near':
                    disp = target - (va + 5)
                    self.code[offset+1:offset+5] = struct.pack('<i', disp)
                elif kind == 'jcc_near':
                    disp = target - (va + 6)
                    self.code[offset+2:offset+6] = struct.pack('<i', disp)

    asm = Assembler(func_va)

    # Prologue (exact original)
    asm.emit(b'\x48\x89\x5c\x24\x08')             # mov [rsp + 8], rbx
    asm.emit(b'\x48\x89\x6c\x24\x18')             # mov [rsp + 0x18], rbp
    asm.emit(b'\x56')                             # push rsi
    asm.emit(b'\x57')                             # push rdi
    asm.emit(b'\x41\x54')                         # push r12
    asm.emit(b'\x41\x56')                         # push r14
    asm.emit(b'\x41\x57')                         # push r15
    asm.emit(b'\x48\x81\xec\x50\x02\x00\x00')     # sub rsp, 0x250

    # Cookie
    asm.lea_rip(b'\x48\x8b\x05', cookie_va)       # mov rax, [rip + cookie]
    asm.emit(b'\x48\x33\xc4')                     # xor rax, rsp
    asm.emit(b'\x48\x89\x84\x24\x40\x02\x00\x00') # mov [rsp + 0x240], rax

    asm.emit(b'\x48\x8b\xb4\x24\xb8\x02\x00\x00') # mov rsi, [rsp + 0x2b8]
    asm.emit(b'\x45\x33\xe4')                     # xor r12d, r12d
    asm.emit(b'\x4c\x8b\xbc\x24\xa0\x02\x00\x00') # mov r15, [rsp + 0x2a0]
    asm.emit(b'\x48\x8b\xda')                     # mov rbx, rdx
    asm.emit(b'\x48\x89\x54\x24\x38')             # mov [rsp + 0x38], rdx (save start of buffer)
    asm.emit(b'\x48\x8b\xac\x24\xa8\x02\x00\x00') # mov rbp, [rsp + 0x2a8]
    asm.emit(b'\xbf\x00\x10\x00\x00')             # mov edi, 0x1000
    asm.emit(b'\x4c\x8b\xb4\x24\xb0\x02\x00\x00') # mov r14, [rsp + 0x2b0]

    asm.emit(b'\x48\x85\xf6')                     # test rsi, rsi
    asm.je_short('skip_rsi')
    asm.emit(b'\x44\x89\x26')                     # mov [rsi], r12d
    asm.label('skip_rsi')

    # Speaker check (always show speaker name when a character speaks)
    asm.emit(b'\x49\x8b\x11')                     # mov rdx, [r9] (speaker hash)
    asm.emit(b'\x48\x89\x54\x24\x28')             # mov [rsp + 0x28], rdx (save speaker hash)
    asm.emit(b'\x45\x33\xc9')                     # xor r9d, r9d (assume no speaker: r9d = 0)
    asm.emit(b'\x48\x85\xd2')                     # test rdx, rdx
    asm.je_short('save_spk_flag')
    asm.emit(b'\x48\xb8\xc4\x24\x52\xac\x55\x81\x07\xd4') # movabs rax, 0xd4078155ac5224c4 (SUBTITLE_CHARACTER_NONE)
    asm.emit(b'\x48\x39\xc2')                     # cmp rdx, rax
    asm.je_short('save_spk_flag')
    asm.emit(b'\x41\xb1\x01')                     # mov r9b, 1 (has speaker!)

    asm.label('save_spk_flag')
    # CRITICAL: Save has_speaker at [rsp + 0x238]!
    # [rsp + 0x20] is the shadow space argument slot and gets wiped by child function calls!
    asm.emit(b'\x44\x88\x8c\x24\x38\x02\x00\x00') # mov [rsp + 0x238], r9b

    # STEP 1: ALWAYS WRITE DIALOGUE FIRST
    asm.emit(b'\xb9\x04\x00\x00\x00')             # mov ecx, 4
    asm.call_va(get_layout_mode_va)
    asm.emit(b'\x44\x8b\xc8')                     # mov r9d, eax
    asm.emit(b'\x4d\x8b\xc7')                     # mov r8, r15
    asm.emit(b'\x8b\xd7')                         # mov edx, edi
    asm.emit(b'\x48\x8b\xcb')                     # mov rcx, rbx
    asm.call_va(layout_text_va)
    asm.emit(b'\x84\xc0')                         # test al, al
    asm.jne_short('dialogue_done')
    asm.emit(b'\x48\x63\xd7')                     # movsxd rdx, edi
    asm.emit(b'\x45\x33\xc9')                     # xor r9d, r9d
    asm.emit(b'\x4d\x8b\xc7')                     # mov r8, r15
    asm.emit(b'\x4c\x89\x64\x24\x20')             # mov [rsp + 0x20], r12
    asm.emit(b'\x48\x8b\xcb')                     # mov rcx, rbx
    asm.call_va(utf8_to_utf16_va)

    asm.label('dialogue_done')
    # Advance rbx past dialogue
    asm.emit(b'\x48\x83\xc9\xff')                 # or rcx, -1
    asm.label('loop_dial')
    asm.emit(b'\x48\xff\xc1')                     # inc rcx
    asm.emit(b'\x66\x44\x39\x24\x4b')             # cmp [rbx + rcx*2], r12w
    asm.emit(b'\x75\xf6')                         # jne loop_dial
    asm.emit(b'\x48\x63\xc1')                     # movsxd rax, ecx
    asm.emit(b'\x2b\xf9')                         # sub edi, ecx
    asm.emit(b'\x48\x8d\x1c\x43')                 # lea rbx, [rbx + rax*2]

    # STEP 2: WRITE SPEAKER SECOND (if has_speaker == 1)
    # Check preserved flag at [rsp + 0x238]
    asm.emit(b'\x80\xbc\x24\x38\x02\x00\x00\x01') # cmp byte ptr [rsp + 0x238], 1
    asm.jne_near('epilogue')
    asm.emit(b'\x48\x8b\x54\x24\x28')             # mov rdx, [rsp + 0x28]
    asm.emit(b'\x45\x33\xc0')                     # xor r8d, r8d
    asm.lea_rip(b'\x48\x8d\x0d', db_ptr_va)       # lea rcx, [rip + db_ptr]
    asm.call_va(lookup_speaker_va)
    asm.emit(b'\x4c\x8b\xc0')                     # mov r8, rax
    asm.emit(b'\x48\x85\xc0')                     # test rax, rax
    asm.je_near('epilogue')

    # Format speaker
    asm.emit(b'\x48\x85\xed')                     # test rbp, rbp
    asm.je_short('no_color')
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
    asm.jmp_short('copy_spk')

    asm.label('no_color')
    asm.emit(b'\x4d\x8b\xc8')                     # mov r9, r8
    asm.emit(b'\x48\x8d\x4c\x24\x40')             # lea rcx, [rsp + 0x40]
    asm.lea_rip(b'\x4c\x8d\x05', fmt2_va)         # lea r8, [rip + fmt2]
    asm.emit(b'\x48\x8b\xd7')                     # mov rdx, rdi
    asm.call_va(sprintf_va)

    asm.label('copy_spk')
    asm.emit(b'\x45\x33\xc9')                     # xor r9d, r9d
    asm.emit(b'\x4c\x89\x64\x24\x20')             # mov [rsp + 0x20], r12
    asm.emit(b'\x4c\x8d\x44\x24\x40')             # lea r8, [rsp + 0x40]
    asm.emit(b'\xba\x00\x02\x00\x00')             # mov edx, 0x200
    asm.emit(b'\x48\x8b\xcb')                     # mov rcx, rbx
    asm.call_va(utf8_to_utf16_va)

    # Advance rbx past speaker
    asm.emit(b'\x48\x83\xc9\xff')                 # or rcx, -1
    asm.label('loop_spk')
    asm.emit(b'\x48\xff\xc1')                     # inc rcx
    asm.emit(b'\x66\x44\x39\x24\x4b')             # cmp [rbx + rcx*2], r12w
    asm.emit(b'\x75\xf6')                         # jne loop_spk
    asm.emit(b'\x48\x63\xc1')                     # movsxd rax, ecx
    asm.emit(b'\x2b\xf9')                         # sub edi, ecx
    asm.emit(b'\x48\x8d\x1c\x43')                 # lea rbx, [rbx + rax*2]

    # 3. EPILOGUE
    asm.label('epilogue')
    asm.emit(b'\x66\x44\x89\x23')                 # mov word ptr [rbx], r12w (null terminator)
    asm.emit(b'\x4d\x85\xf6')                     # test r14, r14
    asm.je_short('skip_wrap')
    asm.emit(b'\x48\x8b\x4c\x24\x38')             # mov rcx, [rsp + 0x38] (start of buffer, NOT end)
    asm.call_va(check_wrap_va)
    asm.emit(b'\x41\x88\x06')                     # mov [r14], al
    asm.label('skip_wrap')

    # Security check & restore
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
    print(f"  Generated code size: {len(asm.code)} bytes (max: {func_len} bytes)")
    assert len(asm.code) <= func_len, "Code exceeded function length!"

    pad_len = func_len - len(asm.code)
    asm.code.extend(b'\xcc' * pad_len)

    # Write patched function into exe data
    data[func_off : func_off + func_len] = asm.code
    print(f"  Patched function at file offset {hex(func_off)}")

    # 3. Disable per-glyph black outline text (change jne to jmp so material 0x1f is skipped and replaced with 0x1e)
    # File offset 0x505078: 75 17 -> eb 17
    # File offset 0x21f5567: 75 09 -> eb 09
    off_outline1 = 0x505078
    assert data[off_outline1:off_outline1+2] == b'\x75\x17', f"Unexpected bytes at 0x505078: {data[off_outline1:off_outline1+2].hex()}"
    data[off_outline1] = 0xeb
    print("  Patched outline check 1 at 0x505078 (75 17 -> eb 17)")

    off_outline2 = 0x21f5567
    assert data[off_outline2:off_outline2+2] == b'\x75\x09', f"Unexpected bytes at 0x21f5567: {data[off_outline2:off_outline2+2].hex()}"
    data[off_outline2] = 0xeb
    print("  Patched outline check 2 at 0x21f5567 (75 09 -> eb 09)")

    with open(exe_path, "wb") as f:
        f.write(data)
    print(f"Successfully saved patched executable: {exe_path}")

if __name__ == "__main__":
    patch_tlou_exe(r"D:\The Last of Us\tlou-i.exe", r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe")
