import os
import shutil
import time

GAME_CORE_PSARC = r"D:\The Last of Us\build\pc\main\core.psarc"
BACKUP_CORE_PSARC = r"c:\Users\SlouMa\Desktop\tlou1\backup\core.psarc"

GAME_EXE = r"D:\The Last of Us\tlou-i.exe"
BACKUP_EXE = r"c:\Users\SlouMa\Desktop\tlou1\backup\tlou-i.exe"

def uninstall():
    print("=" * 60)
    print("THE LAST OF US PART 1 - UNINSTALL / RESTORE ORIGINAL")
    print("=" * 60)

    if os.path.exists(BACKUP_CORE_PSARC):
        print(f"Restoring original core.psarc from {BACKUP_CORE_PSARC} to {GAME_CORE_PSARC}...")
        t0 = time.time()
        shutil.copy2(BACKUP_CORE_PSARC, GAME_CORE_PSARC)
        print(f"Restored core.psarc in {time.time()-t0:.1f}s!")
    else:
        print(f"WARNING: Backup core.psarc not found at {BACKUP_CORE_PSARC}")

    if os.path.exists(BACKUP_EXE):
        print(f"Restoring original tlou-i.exe from {BACKUP_EXE} to {GAME_EXE}...")
        t0 = time.time()
        shutil.copy2(BACKUP_EXE, GAME_EXE)
        print(f"Restored tlou-i.exe in {time.time()-t0:.1f}s!")
    else:
        print(f"Notice: No backup tlou-i.exe found at {BACKUP_EXE}")

    print("=" * 60)
    print("Restore complete!")

if __name__ == "__main__":
    uninstall()
