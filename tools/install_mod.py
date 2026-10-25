import os
import sys
import shutil
import time
from psarc import PsarcArchive
from build_mod_files import create_all_mod_files
from psarc_injector import patch_psarc
from patch_exe import patch_tlou_exe

GAME_EXE = r"D:\The Last of Us\tlou-i.exe"
BACKUP_EXE = r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe"

GAME_CORE_PSARC = r"D:\The Last of Us\build\pc\main\core.psarc"
BACKUP_DIR = r"c:\Users\SlouMa\Desktop\tlou1\backup"
BACKUP_CORE_PSARC = os.path.join(BACKUP_DIR, "core.psarc")
BUILD_DIR = r"c:\Users\SlouMa\Desktop\tlou1\build"
BUILD_CORE_PSARC = os.path.join(BUILD_DIR, "core.psarc")

def make_backup():
    if not os.path.exists(GAME_CORE_PSARC):
        raise FileNotFoundError(f"Game file not found: {GAME_CORE_PSARC}")

    if os.path.exists(BACKUP_CORE_PSARC):
        print(f"Backup already exists at: {BACKUP_CORE_PSARC} ({os.path.getsize(BACKUP_CORE_PSARC):,} bytes)")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"Creating backup of original core.psarc to: {BACKUP_CORE_PSARC}...")
    t0 = time.time()
    shutil.copy2(GAME_CORE_PSARC, BACKUP_CORE_PSARC)
    print(f"Backup created in {time.time()-t0:.1f}s ({os.path.getsize(BACKUP_CORE_PSARC):,} bytes).")

def verify_psarc(psarc_path: str):
    print(f"Verifying patched PSARC at {psarc_path}...")
    with PsarcArchive(psarc_path) as arc:
        print(f"Total entries: {len(arc.entries)}")
        eng_data = arc.extract_by_name("text2/eng.common")
        assert len(eng_data) == 1028770, f"Error: eng.common size changed ({len(eng_data)})! Must remain pristine original!"
        print(f"  Verified text2/eng.common: {len(eng_data):,} bytes (100% PRISTINE ORIGINAL).")

        for target in ["text2/fre.common", "text2/fre.subtitles", "text2/fre.subtitles-systemic", "fonts/DINPro-Regular.otf", "fonts/DINPro-Medium.otf"]:
            data = arc.extract_by_name(target)
            print(f"  Verified {target}: {len(data):,} bytes decompressed successfully.")
    print("Verification passed! All files intact and readable.")

def install():
    print("=" * 60)
    print("THE LAST OF US PART 1 - ARABIC MOD INSTALLER")
    print("=" * 60)

    # 1. Backup
    make_backup()

    # 2. Patch Executable (for RTL subtitle layout & speaker names on right)
    print("\nPatching game executable for RTL subtitles and English speaker layout...")
    patch_tlou_exe(GAME_EXE, BACKUP_EXE)

    # 3. Build mod files
    print("\nPreparing mod replacements...")
    replacements = create_all_mod_files()

    # 4. Patch PSARC
    os.makedirs(BUILD_DIR, exist_ok=True)
    print(f"\nBuilding modified core.psarc -> {BUILD_CORE_PSARC}...")
    t0 = time.time()
    # We patch from the backup to guarantee clean baseline
    src_path = BACKUP_CORE_PSARC if os.path.exists(BACKUP_CORE_PSARC) else GAME_CORE_PSARC
    patch_psarc(src_path, BUILD_CORE_PSARC, replacements)
    print(f"PSARC built in {time.time()-t0:.1f}s ({os.path.getsize(BUILD_CORE_PSARC):,} bytes).")

    # 5. Verify before deployment
    print("\nVerifying build integrity...")
    verify_psarc(BUILD_CORE_PSARC)

    # 6. Deploy to game
    print(f"\nDeploying modified core.psarc to game: {GAME_CORE_PSARC}...")
    t0 = time.time()
    # Copy directly over existing file (frees old file space automatically)
    shutil.copy2(BUILD_CORE_PSARC, GAME_CORE_PSARC)
    print(f"Successfully deployed to game in {time.time()-t0:.1f}s!")

    # 7. Clean up temporary build artifact on C: to save space
    if os.path.exists(BUILD_CORE_PSARC):
        os.remove(BUILD_CORE_PSARC)
        print("Cleaned up temporary core.psarc build file.")

    print("\n" + "=" * 60)
    print("MOD INSTALLATION COMPLETE!")
    print("- French language slot ('Français') has been customized:")
    print("  * Narrative subtitles: Arabic (reshaped & RTL formatted)")
    print("  * Artifact / Note / Book Reader: Arabic when pressing 'Read'")
    print("  * All other UI / menus / options / HUD: English original")
    print("  * Arabic fonts (DINPro-Regular, DINPro-Medium): Injected")
    print("=" * 60)

if __name__ == "__main__":
    install()
