import os
import sys
import shutil
import re
import struct
import hashlib
import ctypes
import time
import zipfile
from typing import Dict, List, Optional, Tuple

# Ensure safe console output on all Windows codepages
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

VERSION = "1.0.0"
AUTHOR = "Mohamed Moslem Allouch"

def get_bundle_dir() -> str:
    """Returns directory of embedded resources (sys._MEIPASS if PyInstaller, else script dir)."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def load_mod_asset(rel_path: str) -> bytes:
    """Loads a file from mod_data directory."""
    candidates = [
        os.path.join(os.path.dirname(sys.executable), "mod_data", rel_path),
        os.path.join(os.getcwd(), "mod_data", rel_path),
        os.path.join(get_bundle_dir(), "mod_data", rel_path),
        os.path.join(get_bundle_dir(), rel_path),
    ]
    for c in candidates:
        if os.path.exists(c):
            with open(c, "rb") as f:
                return f.read()

    zip_path = os.path.join(get_bundle_dir(), "mod_data.zip")
    norm_rel = rel_path.replace("\\", "/")
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, "r") as zf:
            return zf.read(norm_rel)

    raise FileNotFoundError(f"Required mod asset not found: {rel_path}. Please ensure 'mod_data' folder is in the same directory.")

def print_banner():
    print("=" * 72)
    print("   THE LAST OF US PART I - ARABIC LOCALIZATION MOD")
    print(f"   Created by: {AUTHOR}")
    print(f"   Nexus Mods Edition - Version {VERSION}")
    print("=" * 72)
    print()

def find_game_directory() -> Optional[str]:
    # Check current directory and parent directory first
    candidates = [
        os.getcwd(),
        os.path.dirname(os.getcwd()),
        r"D:\The Last of Us",
        r"C:\Program Files (x86)\Steam\steamapps\common\The Last of Us Part I",
        r"D:\SteamLibrary\steamapps\common\The Last of Us Part I",
        r"E:\SteamLibrary\steamapps\common\The Last of Us Part I",
        r"F:\SteamLibrary\steamapps\common\The Last of Us Part I",
        r"C:\Program Files\Epic Games\TheLastOfUsPartI",
        r"D:\Epic Games\TheLastOfUsPartI",
    ]

    for c in candidates:
        if not c or not os.path.exists(c):
            continue
        exe = os.path.join(c, "tlou-i.exe")
        psarc = os.path.join(c, "build", "pc", "main", "core.psarc")
        if os.path.exists(exe) and os.path.exists(psarc):
            return os.path.abspath(c)

    return None

def browse_folder_windows(title: str = "Select 'The Last of Us Part I' Game Directory") -> Optional[str]:
    # 1. Native Windows shell32 SHBrowseForFolderW
    try:
        from ctypes import wintypes
        class BROWSEINFOW(ctypes.Structure):
            _fields_ = [
                ("hwndOwner", wintypes.HWND),
                ("pidlRoot", ctypes.c_void_p),
                ("pszDisplayName", wintypes.LPWSTR),
                ("lpszTitle", wintypes.LPCWSTR),
                ("ulFlags", wintypes.UINT),
                ("lpfn", ctypes.c_void_p),
                ("lParam", wintypes.LPARAM),
                ("iImage", ctypes.c_int)
            ]

        BIF_RETURNONLYFSDIRS = 0x0001
        BIF_NEWDIALOGSTYLE   = 0x0040

        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)

        display_buf = ctypes.create_unicode_buffer(260)
        bi = BROWSEINFOW()
        bi.hwndOwner = None
        bi.pidlRoot = None
        bi.pszDisplayName = ctypes.cast(display_buf, wintypes.LPWSTR)
        bi.lpszTitle = title
        bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE
        bi.lpfn = None
        bi.lParam = 0
        bi.iImage = 0

        pidl = shell32.SHBrowseForFolderW(ctypes.byref(bi))
        if pidl:
            path_buf = ctypes.create_unicode_buffer(260)
            shell32.SHGetPathFromIDListW(pidl, path_buf)
            ole32.CoTaskMemFree(pidl)
            if path_buf.value and os.path.exists(path_buf.value):
                return path_buf.value
    except Exception:
        pass

    # 2. Native PowerShell FolderBrowserDialog fallback
    try:
        import subprocess
        ps_cmd = [
            "powershell", "-NoProfile", "-Command",
            "[System.Reflection.Assembly]::LoadWithPartialName('System.windows.forms') | Out-Null; "
            "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$f.Description = 'Select The Last of Us Part I Game Directory'; "
            "$f.ShowNewFolderButton = $false; "
            "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.SelectedPath }"
        ]
        res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=60)
        p = res.stdout.strip()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass

    return None

def prompt_game_directory() -> str:
    print("[-] Game directory was not detected automatically.")
    print("    Opening folder browser window to select your game directory...")

    chosen = browse_folder_windows("Please select your 'The Last of Us Part I' game folder:")
    if chosen:
        exe = os.path.join(chosen, "tlou-i.exe")
        psarc = os.path.join(chosen, "build", "pc", "main", "core.psarc")
        if os.path.exists(exe) and os.path.exists(psarc):
            return os.path.abspath(chosen)
        else:
            print(f"[!] Selected folder does not contain 'tlou-i.exe' and 'core.psarc':\n    {chosen}\n")

    while True:
        path = input("Enter the full path to your 'The Last of Us Part I' folder:\n> ").strip().strip('"')
        if not path:
            continue
        exe = os.path.join(path, "tlou-i.exe")
        psarc = os.path.join(path, "build", "pc", "main", "core.psarc")
        if os.path.exists(exe) and os.path.exists(psarc):
            return os.path.abspath(path)
        print(f"[!] Could not find 'tlou-i.exe' and 'build/pc/main/core.psarc' in:\n    {path}")
        print("    Please check the directory and try again.\n")

# ==============================================================================
# PSARC PARSER & INJECTOR (Using game's oo2core_9_win64.dll)
# ==============================================================================

_oodle = None

def init_oodle(oodle_path: str):
    global _oodle
    if _oodle is None:
        if not os.path.exists(oodle_path):
            raise FileNotFoundError(f"Oodle decompression library not found: {oodle_path}")
        dll = ctypes.cdll.LoadLibrary(oodle_path)
        dll.OodleLZ_Decompress.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_int
        ]
        dll.OodleLZ_Decompress.restype = ctypes.c_int

        dll.OodleLZ_Compress.argtypes = [
            ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_size_t
        ]
        dll.OodleLZ_Compress.restype = ctypes.c_int
        _oodle = dll

def compress_block(raw_chunk: bytes) -> Tuple[bytes, int]:
    global _oodle
    target_sz = len(raw_chunk)
    comp_buf = ctypes.create_string_buffer(target_sz + 32768)
    res = _oodle.OodleLZ_Compress(
        8, # Kraken
        raw_chunk, target_sz,
        comp_buf, 4, # normal
        None, None, None, None, 0
    )
    if 0 < res < target_sz:
        return comp_buf.raw[:res], res
    else:
        return raw_chunk, 0

class PsarcEntry:
    def __init__(self, md5_hash: bytes, z_index: int, uncomp_sz: int, offset: int, index: int):
        self.md5_hash = md5_hash
        self.z_index = z_index
        self.uncomp_sz = uncomp_sz
        self.offset = offset
        self.index = index
        self.name: Optional[str] = None

class PsarcArchive:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.fp = open(filepath, "rb")
        self.entries: List[PsarcEntry] = []
        self.hash_to_entry: Dict[bytes, PsarcEntry] = {}
        self.z_sizes: List[int] = []
        self.block_sz = 65536
        self._read_header()

    def close(self):
        if self.fp and not self.fp.closed:
            self.fp.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _read_header(self):
        self.fp.seek(0)
        hdr = self.fp.read(32)
        magic, ver_hi, ver_lo, comp, toc_len, entry_sz, num_entries, block_sz, flags = struct.unpack('>4sHH4sIIIII', hdr)
        if magic != b'PSAR':
            raise ValueError(f"Not a PSARC file: {self.filepath}")
        self.block_sz = block_sz
        self.num_entries = num_entries
        self.comp = comp

        for i in range(num_entries):
            raw = self.fp.read(30)
            h = raw[:16]
            z_idx = struct.unpack('>I', raw[16:20])[0]
            uncomp_sz = int.from_bytes(raw[20:25], 'big')
            off = int.from_bytes(raw[25:30], 'big')
            entry = PsarcEntry(h, z_idx, uncomp_sz, off, i)
            self.entries.append(entry)
            self.hash_to_entry[h] = entry

        z_table_len = toc_len - 32 - num_entries * 30
        if z_table_len > 0:
            z_table_raw = self.fp.read(z_table_len)
            self.z_sizes = [struct.unpack('>H', z_table_raw[i:i+2])[0] for i in range(0, z_table_len, 2)]

def inject_files_into_psarc(src_psarc_path: str, dst_psarc_path: str, replacements: Dict[str, bytes]):
    with PsarcArchive(src_psarc_path) as arc:
        num_entries = len(arc.entries)
        block_sz = arc.block_sz
        comp = arc.comp

        # Map replacements by MD5
        repl_by_hash = {}
        for rel_path, data in replacements.items():
            h = hashlib.md5(rel_path.encode('utf-8')).digest()
            repl_by_hash[h] = (rel_path, data)

        print(f"  Injecting {len(replacements)} localization files into core.psarc...")

        with open(dst_psarc_path, "wb") as out_fp:
            # Calculate preliminary TOC sizes
            entry_num_blocks = []
            for entry in arc.entries:
                if entry.md5_hash in repl_by_hash:
                    new_sz = len(repl_by_hash[entry.md5_hash][1])
                    num_b = (new_sz + block_sz - 1) // block_sz if new_sz > 0 else 0
                else:
                    new_sz = entry.uncomp_sz
                    num_b = (new_sz + block_sz - 1) // block_sz if new_sz > 0 else 0
                entry_num_blocks.append(num_b)

            total_z_entries = sum(entry_num_blocks)
            toc_len = 32 + num_entries * 30 + total_z_entries * 2

            # Reserve space for header and TOC
            out_fp.write(b'\x00' * toc_len)

            # Write entry data blocks
            new_entries = []
            new_z_sizes = []
            current_z_idx = 0

            for i, entry in enumerate(arc.entries):
                new_off = out_fp.tell()
                if entry.md5_hash in repl_by_hash:
                    rel_name, new_data = repl_by_hash[entry.md5_hash]
                    print(f"    -> Replacing {rel_name} ({len(new_data):,} bytes)")
                    new_uncomp_sz = len(new_data)
                    num_b = entry_num_blocks[i]
                    for b in range(num_b):
                        chunk = new_data[b * block_sz : (b + 1) * block_sz]
                        c_bytes, z_sz = compress_block(chunk)
                        out_fp.write(c_bytes)
                        new_z_sizes.append(z_sz)
                    new_entries.append((entry.md5_hash, current_z_idx, new_uncomp_sz, new_off))
                    current_z_idx += num_b
                else:
                    new_uncomp_sz = entry.uncomp_sz
                    num_b = entry_num_blocks[i]
                    if num_b > 0:
                        arc.fp.seek(entry.offset)
                        total_entry_bytes = 0
                        for b in range(num_b):
                            z_sz = arc.z_sizes[entry.z_index + b]
                            chunk_sz = z_sz if z_sz > 0 else min(block_sz, new_uncomp_sz - b * block_sz)
                            total_entry_bytes += chunk_sz
                            new_z_sizes.append(z_sz)
                        raw_data = arc.fp.read(total_entry_bytes)
                        out_fp.write(raw_data)
                    new_entries.append((entry.md5_hash, current_z_idx, new_uncomp_sz, new_off))
                    current_z_idx += num_b

            # Rewind and write header and TOC
            out_fp.seek(0)
            flags = 12 # archive_flags
            hdr = struct.pack('>4sHH4sIIIII', b'PSAR', 1, 4, comp, toc_len, 30, num_entries, block_sz, flags)
            out_fp.write(hdr)

            # Entries table (30 bytes per entry)
            for md5_h, z_idx, uncomp_sz, off in new_entries:
                uncomp_bytes = uncomp_sz.to_bytes(5, 'big')
                off_bytes = off.to_bytes(5, 'big')
                rec = md5_h + struct.pack('>I', z_idx) + uncomp_bytes + off_bytes
                out_fp.write(rec)

            # Z_sizes table
            z_table_bytes = bytearray()
            for z_sz in new_z_sizes:
                z_table_bytes.extend(struct.pack('>H', z_sz))
            out_fp.write(z_table_bytes)

            assert out_fp.tell() == toc_len, f"TOC write mismatch: {out_fp.tell()} != {toc_len}"

# ==============================================================================
# EXECUTABLE PATCHER
# ==============================================================================

def patch_game_executable(exe_path: str, backup_path: str, hook_bytes: bytes):
    print("  Patching tlou-i.exe...")
    if not os.path.exists(backup_path):
        print(f"  Creating backup of tlou-i.exe -> {backup_path}")
        shutil.copy2(exe_path, backup_path)

    with open(backup_path, "rb") as f:
        data = bytearray(f.read())

    # 1. Format strings in .rdata
    fmt1_pat = b'<font color="#%08X">%s:</font>'
    off_fmt1 = data.find(fmt1_pat)
    if off_fmt1 != -1:
        new_fmt1 = b' <font color="#%08X">:%s</font>\x00'
        data[off_fmt1:off_fmt1+len(new_fmt1)] = new_fmt1
        off_fmt2 = off_fmt1 + 32
        new_fmt2 = b' :%s\x00\x00\x00\x00'
        data[off_fmt2:off_fmt2+len(new_fmt2)] = new_fmt2
        print("    -> Patched subtitle speaker layout format strings")

    # 2. Outline check 1 (disable per-glyph outline border)
    m1 = list(re.finditer(b'\x83\xf9\x01\x75[\x00-\xff]\x80\x3d[\x00-\xff]{5}\x75\x17\xc7\x43\x30\x1f', data))
    if m1:
        off1 = m1[0].start() + 12
        assert data[off1:off1+2] == b'\x75\x17'
        data[off1] = 0xeb
        print("    -> Patched outline check 1 (seamless cursive text enabled)")

    # 3. Outline check 2
    m2 = list(re.finditer(b'\x80\x3d[\x00-\xff]{5}\x75\x09\xc7\x43\x30\x1f', data))
    if m2:
        off2 = m2[0].start() + 7
        assert data[off2:off2+2] == b'\x75\x09'
        data[off2] = 0xeb
        print("    -> Patched outline check 2 (seamless cursive text enabled)")

    # 4. Function hook for RTL dialogue formatting
    prologue = b'\x48\x89\x5c\x24\x08\x48\x89\x6c\x24\x18\x56\x57\x41\x54\x41\x56\x41\x57\x48\x81\xec\x50\x02\x00\x00'
    idx_func = data.find(prologue)
    if idx_func != -1:
        assert len(hook_bytes) == 465
        data[idx_func:idx_func+len(hook_bytes)] = hook_bytes
        print(f"    -> Injected RTL subtitle layout hook (465 bytes at offset 0x{idx_func:x})")

    with open(exe_path, "wb") as f:
        f.write(data)
    print("  Successfully updated tlou-i.exe!")

# ==============================================================================
# INSTALL & UNINSTALL WORKFLOWS
# ==============================================================================

def run_install(game_dir: str):
    exe_path = os.path.join(game_dir, "tlou-i.exe")
    exe_bak = os.path.join(game_dir, "tlou-i.exe.orig_bak")
    psarc_path = os.path.join(game_dir, "build", "pc", "main", "core.psarc")
    psarc_bak = os.path.join(game_dir, "build", "pc", "main", "core.psarc.orig_bak")
    oodle_path = os.path.join(game_dir, "oo2core_9_win64.dll")

    init_oodle(oodle_path)

    # 1. Backups
    print("\n[Step 1/3] Checking Backups...")
    if not os.path.exists(exe_bak):
        print(f"  Creating original backup: {os.path.basename(exe_bak)}...")
        shutil.copy2(exe_path, exe_bak)
    else:
        print(f"  Backup already exists: {os.path.basename(exe_bak)}")

    if not os.path.exists(psarc_bak):
        print(f"  Creating original backup: {os.path.basename(psarc_bak)} (~6.3 GB, may take ~20-30s)...")
        t0 = time.time()
        shutil.copy2(psarc_path, psarc_bak)
        print(f"  Backup created in {time.time()-t0:.1f}s.")
    else:
        print(f"  Backup already exists: {os.path.basename(psarc_bak)}")

    # 2. Patch Executable
    print("\n[Step 2/3] Patching Game Executable...")
    hook_bytes = load_mod_asset("func_hook.bin")
    patch_game_executable(exe_path, exe_bak, hook_bytes)

    # 3. Patch PSARC
    print("\n[Step 3/3] Injecting Arabic Localization Assets into core.psarc...")
    fre_common_data = load_mod_asset("text2/fre.common")
    fre_sub_data = load_mod_asset("text2/fre.subtitles")
    fre_sys_data = load_mod_asset("text2/fre.subtitles-systemic")
    din_reg_data = load_mod_asset("fonts/DINPro-Regular.otf")
    din_med_data = load_mod_asset("fonts/DINPro-Medium.otf")

    replacements = {
        # French slot
        "text2/fre.common": fre_common_data,
        "text2/fre.subtitles": fre_sub_data,
        "text2/fre.subtitles-systemic": fre_sys_data,
        # English slot (default game boot language - prevents resetting on restart)
        "text2/eng.common": fre_common_data,
        "text2/eng.subtitles": fre_sub_data,
        "text2/eng.subtitles-systemic": fre_sys_data,
        # Fonts
        "fonts/DINPro-Regular.otf": din_reg_data,
        "fonts/DINPro-Medium.otf": din_med_data,
    }

    temp_psarc = psarc_path + ".tmp_mod"
    t0 = time.time()
    inject_files_into_psarc(psarc_bak, temp_psarc, replacements)
    print(f"  PSARC successfully patched in {time.time()-t0:.1f}s.")

    # Swap into place
    if os.path.exists(psarc_path):
        os.remove(psarc_path)
    os.rename(temp_psarc, psarc_path)
    print(f"  Deployed modified core.psarc to {psarc_path}!")

    print("\n" + "=" * 72)
    print("   ARABIC LOCALIZATION MOD SUCCESSFULLY INSTALLED!")
    print(f"   Created by {AUTHOR}")
    print("=" * 72)
    print("""
HOW TO USE IN-GAME:
- The mod is active immediately!
- Both English (US) and French slots now display clean Arabic subtitles
  and Arabic Document reading with English menus.
- When you restart the game, your subtitles will STAY in Arabic automatically!
- Simply launch 'The Last of Us Part I' and enjoy playing!
""")

def run_uninstall(game_dir: str):
    exe_path = os.path.join(game_dir, "tlou-i.exe")
    exe_bak = os.path.join(game_dir, "tlou-i.exe.orig_bak")
    psarc_path = os.path.join(game_dir, "build", "pc", "main", "core.psarc")
    psarc_bak = os.path.join(game_dir, "build", "pc", "main", "core.psarc.orig_bak")

    print("\n" + "=" * 72)
    print("   UNINSTALLING ARABIC LOCALIZATION MOD")
    print("=" * 72)

    restored = 0
    if os.path.exists(exe_bak):
        print(f"  Restoring original {os.path.basename(exe_path)} from backup...")
        shutil.copy2(exe_bak, exe_path)
        restored += 1
    else:
        print(f"  [!] No backup found for {os.path.basename(exe_path)}.")

    if os.path.exists(psarc_bak):
        print(f"  Restoring original {os.path.basename(psarc_path)} from backup...")
        shutil.copy2(psarc_bak, psarc_path)
        restored += 1
    else:
        print(f"  [!] No backup found for {os.path.basename(psarc_path)}.")

    if restored == 2:
        print("\n[SUCCESS] The game has been completely restored to pristine original condition!")
    elif restored > 0:
        print("\n[WARNING] Partial restore completed. Check missing backup files above.")
    else:
        print("\n[ERROR] No backup files found to restore.")

def main():
    print_banner()
    game_dir = find_game_directory()
    if game_dir:
        print(f"[+] Detected game installation:\n    {game_dir}\n")
    else:
        game_dir = prompt_game_directory()
        print(f"[+] Using game directory:\n    {game_dir}\n")

    while True:
        print("Please choose an option:")
        print("  [1] Install Arabic Localization Mod (Automatic Backup & Patch)")
        print("  [2] Restore Original Game (Uninstall Mod)")
        print("  [3] Exit")
        choice = input("\nEnter choice [1-3]: ").strip()

        if choice == "1":
            try:
                run_install(game_dir)
            except Exception as e:
                print(f"\n[ERROR] Installation failed: {e}")
                import traceback
                traceback.print_exc()
            break
        elif choice == "2":
            try:
                run_uninstall(game_dir)
            except Exception as e:
                print(f"\n[ERROR] Uninstallation failed: {e}")
            break
        elif choice == "3":
            print("Exiting...")
            return
        else:
            print("Invalid choice, please enter 1, 2, or 3.\n")

    if sys.stdin.isatty():
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
