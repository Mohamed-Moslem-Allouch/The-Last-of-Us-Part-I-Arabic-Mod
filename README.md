# The Last of Us Part I (PC) - Arabic Localization & Reverse Engineering Suite

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20PC-blue.svg)](https://store.steampowered.com/app/1888930/The_Last_of_Us_Part_I/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Engine](https://img.shields.io/badge/Engine-Naughty%20Dog%20Proprietary-red.svg)]()
[![Architecture](https://img.shields.io/badge/Arch-x86__64-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Mohamed%20Moslem%20Allouch-lightgrey.svg)]()

> **Created and Engineered by: Mohamed Moslem Allouch**  
> A complete, fully native Arabic localization mod and comprehensive reverse-engineering toolkit for *The Last of Us Part I* on PC.

---

## 📖 Table of Contents
1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [The Technical Deep Dive](#-the-technical-deep-dive)
   - [1. The 1-Pixel Cursive Seam Problem & Material 0x1f Bypass](#1-the-1-pixel-cursive-seam-problem--material-0x1f-bypass)
   - [2. Adobe Type 2 CFF CharString Engineering & FtAlloc Limits](#2-adobe-type-2-cff-charstring-engineering--ftalloc-limits)
   - [3. x86_64 Executable Patching & RTL Subtitle Hook](#3-x86_64-executable-patching--rtl-subtitle-hook)
   - [4. Dual-Slot Persistence Architecture (Steam API Bypass)](#4-dual-slot-persistence-architecture-steam-api-bypass)
   - [5. High-Speed PSARC Stream Injection via Oodle Kraken](#5-high-speed-psarc-stream-injection-via-oodle-kraken)
   - [6. High-Performance Standalone Installer](#6-high-performance-standalone-installer)
4. [Tool Catalog & Repository Structure](#-tool-catalog--repository-structure)
5. [Installation Guide](#-installation-guide)
   - [For Players (End Users)](#for-players-end-users)
   - [For Developers & Modders](#for-developers--modders)
6. [Building from Source](#-building-from-source)
7. [Credits & Legal](#-credits--legal)

---

## 🌟 Overview

*The Last of Us Part I* PC port uses Naughty Dog's proprietary in-house engine featuring a custom vector text rendering subsystem (**`Text2`**). The PC release ships without native Arabic text shaping, right-to-left (RTL) dialogue formatting, or Arabic glyphs in its primary font assets.

This repository provides the complete technical solution, toolchain, and assets that solve all text rendering, font memory limits, dialogue formatting, and archive injection challenges, delivering a pristine, seamless Arabic localization experience.

---

## ✨ Key Features

- **Pristine Narrative & Dialogue Subtitles**: Full cinematic and gameplay subtitles rendered in beautiful, continuous cursive Arabic script without broken letter joints or seams.
- **Systemic & Combat Subtitles**: Enemy callouts, background dialogue, ambient barks, and companion reactions fully translated.
- **In-Game Document & Letter Reader**: Notes, letters, diary entries, and paper artifacts fully translated into Arabic when pressing the in-game **Read** button.
- **English UI & Menus Preserved**: The game's main menus, HUD, options, weapon wheel, and backpack remain 100% untouched English, preventing UI clipping and layout corruption.
- **Dual-Slot Persistence**: Both English (`eng`) and French (`fre`) slots are localized, preventing the game from reverting to English US upon restart due to Steam API locale queries.
- **Author Signature**: Custom menu branding featuring `EXTRAS (Mohamed Moslem Allouch)` directly within the game's menu string tables.
- **Sub-Second Standalone Installer**: Single-file executable with native Windows folder browsing dialog, automated backups, and 30-second patch application.

---

## 🔬 The Technical Deep Dive

### 1. The 1-Pixel Cursive Seam Problem & Material 0x1f Bypass

#### The Root Cause:
In cursive scripts such as Arabic, glyphs must connect seamlessly along the horizontal baseline. Initial testing revealed a persistent 1-to-2-pixel vertical black gap between connected Arabic letters:

$$\text{Letter } i \quad \longleftarrow \text{ [1-pixel vertical cut] } \longrightarrow \quad \text{Letter } i+1$$

Decompilation of Naughty Dog's `Text2` renderer revealed that text is rendered using internal shader materials:
- **Material `0x1f`**: Outline / stroked text (generates per-glyph dilated border quads).
- **Material `0x1e`**: Solid fill text (generates clean vector geometry without borders).

Because the subtitle renderer processes glyphs sequentially, Material `0x1f` stamps a dilated black border quad around glyph $i+1$. In cursive Arabic, glyph $i+1$'s black border draws directly on top of glyph $i$'s connecting white baseline tail, cutting the connection with a 1-pixel seam.

#### The Binary Patch:
In `tlou-i.exe`, the engine checks whether to assign Material `0x1f`:
```asm
; Check 1 at offset 0x505078
83 f9 01          cmp ecx, 1
75 xx             jne skip
80 3d xx xx xx xx cmp byte ptr [rel flag], 0
75 17             jne set_material_1f      ; <-- PATCH: Change 75 17 to eb 17 (jmp)
c7 43 30 1f 00... mov dword ptr [rbx+30h], 1fh

; Check 2 at offset 0x21f5567
80 3d xx xx xx xx cmp byte ptr [rel flag], 0
75 09             jne set_material_1f      ; <-- PATCH: Change 75 09 to eb 09 (jmp)
c7 43 30 1f 00... mov dword ptr [rbx+30h], 1fh
```
By converting conditional jumps (`0x75`) to unconditional jumps (`0xeb`), the engine forces Material `0x1e` for text rendering. Overlapping baseline tails (+100 font units) blend with 100% mathematical continuity.

---

### 2. Adobe Type 2 CFF CharString Engineering & FtAlloc Limits

#### The Memory Pool Limit (`Text2::FtAlloc`):
Naughty Dog's font engine allocates fixed-size memory pools on startup. Injecting standard full-coverage Arabic TTF/OTF fonts causes `Text2::FtAlloc` heap exhaustion, crashing the game before the main menu loads:
- **Constraint**: `DINPro-Regular.otf` and `DINPro-Medium.otf` must stay under **135 KB** total file size (`CFF ` table $\le 85\text{ KB}$).
- **Constraint**: `HelveticaNeueBold.ttf` must remain completely untouched to preserve UI layouts and engine sanity.

#### Algorithmic Glyphs Injection (`patch_fonts_clean.py`):
1. **Strict Subset Generation**: Scans all 10,000+ localized dialogue strings and document entries, extracting only the exact Arabic Presentation Forms-B (`0xFE70`–`0xFEFD`) and alphabet characters actively used by the game.
2. **Type 2 CFF Curve Generation**: Converts donor glyph contours (from Google Noto Sans Arabic) into optimized Adobe Type 2 CharStrings (`T2CharStringPen`) with subroutinization.
3. **Left-Anchor Rule**: Left-connecting glyphs have their baseline tail anchored strictly at $x=0$ ($lsb = 0$). Negative left-side bearings are clamped to zero to prevent back-clipping into preceding characters.
4. **Right Baseline Overhang**: Connects glyphs by extending the right baseline tail outward by $+100$ design units ($x_{\max} = \text{width} + 100$). The extended tail slides smoothly beneath the subsequent glyph's left anchor, forming an unbroken bridge across arbitrary character kerning.

```
+-----------------------------------------------------------+
| Glyphs Subsetting & Tail Extension Pipeline               |
|                                                           |
|  [Donor Glyphs] -> [Bidi Analysis] -> [Type 2 Pen]        |
|                            |                              |
|                            v                              |
|   lsb = 0  <------- [Glyph Body] -------> +100 units      |
|  (Left Anchor)                         (Right Overhang)   |
+-----------------------------------------------------------+
```

---

### 3. x86_64 Executable Patching & RTL Subtitle Hook

#### Subtitle Speaker Order Inversion:
In English, subtitles follow the layout:
$$\texttt{<Speaker>: <Dialogue>}$$
In an RTL language, this must read:
$$\texttt{<Dialogue> :<Speaker>}$$

We implement this at two levels:

1. **Format String Modification (`.rdata`)**:
   - `0x2e35760`: `<font color="#%08X">%s:</font>` $\longrightarrow$ ` <font color="#%08X">:%s</font>`
   - `0x2e35780`: `%s:` $\longrightarrow$ ` :%s`

2. **Custom Assembly Subtitle Hook (`func_hook.bin`)**:
   At function `0x141fe69e4` (file offset `0x1fe5de4`, 465 bytes), the engine formats subtitle text before rendering. We assembled a custom x86_64 hook that:
   - Preserves register conventions and stack alignment (`sub rsp, 0x250`).
   - Copies dialogue tokens first to the output buffer.
   - Appends the speaker tag and color tags (`#%08X`) to the right of the string.
   - Preserves null termination and calls the engine's line wrap check (`0x141fe81dc`).

---

### 4. Dual-Slot Persistence Architecture (Steam API Bypass)

#### The Problem:
When launching *The Last of Us Part I*, the game engine calls Steamworks API:
```cpp
SteamApps()->GetCurrentGameLanguage();
```
If Steam is set to English, the game automatically resets the internal text language slot to English (`text2/eng.*`), ignoring user settings saved in previous sessions.

#### The Dual-Slot Solution:
Instead of only patching the French slot (`fre`), the build pipeline deploys the exact same Arabic localization payload to **both** language slots:
- `text2/fre.common` + `text2/eng.common`
- `text2/fre.subtitles` + `text2/eng.subtitles`
- `text2/fre.subtitles-systemic` + `text2/eng.subtitles-systemic`

Result: Regardless of whether Steam forces English or the player selects Arabic/French, subtitles and notes are permanently rendered in Arabic on boot without touching any menus.

---

### 5. High-Speed PSARC Stream Injection via Oodle Kraken

Naughty Dog games pack all runtime data into monolithic Sony PSARC archives (`core.psarc` $\approx 6.3\text{ GB}$). Full archive unpacking and repacking requires 10+ minutes and over 15 GB of temporary disk space.

We engineered `psarc_injector.py`, an in-place stream injection tool:
1. **TOC Computation**: Parses the existing Table of Contents (TOC) and calculates exact block counts for new replacement files.
2. **Oodle Kraken Compression**: Compresses modified files using the game's native `oo2core_9_win64.dll` (`OodleLZ_Compress`, Compressor 8, Level Normal).
3. **Zero-Decompression Stream Pass**: Reads untouched entry blocks from the source archive and streams them directly into the destination file without decompressing or recompressing them.
4. **Header Rewind**: Rewinds to file offset `0x0` and writes the finalized 32-byte header and updated TOC.

> ⚡ **Performance**: Full injection of modified text tables and fonts into a 6.3 GB archive completes in **under 30 seconds**.

---

### 6. High-Performance Standalone Installer

The end-user installer (`nexus_installer_main.py` $\to$ `TLOU_Arabic_Mod_Installer.exe`):
- **Sub-Second Startup**: Assets are pre-packaged into an embedded `mod_data.zip` (1.5 MB) read entirely in memory.
- **Native Folder Browser**: If the game isn't automatically found in default Steam / Epic Games directories, it triggers the native Windows `SHBrowseForFolderW` / PowerShell dialog modal.
- **Automated Backup & Restore**: Creates `.orig_bak` copies of `tlou-i.exe` and `core.psarc` before modification. One-click uninstall cleanly restores the game to vanilla state.

---

## 🛠 Tool Catalog & Repository Structure

```
tlou1-arabic-mod/
│
├── .gitignore                          # Excludes multi-GB archives, binaries, and temporary caches
├── LICENSE                             # MIT License
├── README.md                           # Comprehensive documentation & technical architecture
├── requirements.txt                    # Python dependencies
│
├── nexus_package/
│   ├── README.txt                      # Mod release notes & installation guide (English & Arabic)
│   └── NEXUS_MOD_DESCRIPTION.bbcode    # BBCode description for Nexus Mods release
│
├── NotoSansArabic-Regular.ttf          # Open-source Google Noto Sans Arabic donor fonts
├── NotoSansArabic-Medium.ttf
├── NotoSansArabic-Bold.ttf
│
├── mod_files/                          # Compiled mod binary assets
│   └── text2/
│       ├── eng.common                  # English slot menu strings & 'EXTRAS (Mohamed Moslem Allouch)'
│       ├── fre.common                  # Arabic notes, documents, and 'Arabic' slot label
│       ├── fre.subtitles               # Localized narrative dialogue subtitles
│       └── fre.subtitles-systemic      # Localized combat and ambient speech subtitles
│
├── extracted/                          # Source text data and string tables
│   ├── arabic_notes.json               # Arabic translations for all in-game letters and artifacts
│   ├── arabic_subtitles.json           # Arabic translations for narrative & systemic subtitles
│   └── reader_notes_en.json            # English source strings for documents
│
├── orig_fonts/                         # Original game font templates
│   ├── DINPro-Regular.otf              # Naughty Dog DINPro Regular (PostScript CFF)
│   ├── DINPro-Medium.otf               # Naughty Dog DINPro Medium (PostScript CFF)
│   ├── HelveticaNeueBold.ttf           # Untouched UI font
│   └── SSTThai-Light-PUA.otf
│
└── tools/                              # Reverse engineering and build toolchain
    ├── mod_data/                       # Payload directory for packaging
    ├── mod_data.zip                    # Pre-compressed 1.5MB mod payload
    ├── nexus_installer_main.py         # Source for the standalone installer (CLI + Win32 Dialog)
    ├── patch_exe.py                    # Complete dynamic x86_64 executable patcher
    ├── psarc.py                        # PSARC archive reader and unpacker
    ├── psarc_injector.py               # Fast in-place PSARC stream injector using Oodle Kraken
    ├── patch_fonts_clean.py            # Type 2 CFF CharString manipulator & baseline overhang stretcher
    ├── bidi_engine.py                  # Arabic BiDi reshaping with XML token protection
    ├── build_mod_files.py              # Full pipeline compiler for text2 binary string tables
    ├── text_packer.py                  # Low-level Naughty Dog Text2 string table serializer
    ├── translate_subtitles.py          # Subtitle translation parser and builder
    ├── translate_notes.py              # Document note translation parser and builder
    ├── install_mod.py                  # Direct installation script for developers
    ├── uninstall_mod.py                # Direct uninstall script for developers
    └── assemble_patch.py               # x86_64 assembly hook assembler
```

---

## 🚀 Installation Guide

### For Players (End Users)

1. Download the release package (`The_Last_of_Us_Part_I_Arabic_Mod_v1.0.zip`) from [Releases](../../releases) or Nexus Mods.
2. Extract the file or copy `TLOU_Arabic_Mod_Installer.exe` into your *The Last of Us Part I* game folder (where `tlou-i.exe` is located).
3. Run `TLOU_Arabic_Mod_Installer.exe`.
4. Choose **`[1] Install Arabic Localization Mod`**.
5. The installer will back up original files, patch the executable, and inject Arabic assets into `core.psarc` in ~30 seconds.
6. Launch the game—subtitles and notes are active in Arabic immediately!

---

### For Developers & Modders

#### 1. Environment Setup
```powershell
# Clone the repository
git clone https://github.com/your-username/tlou1-arabic-mod.git
cd tlou1-arabic-mod

# Install Python requirements
pip install -r requirements.txt
```

#### 2. Rebuilding Arabic Font Assets
To regenerate the compact, strictly subsetted CFF fonts with right-baseline overhang:
```powershell
python tools/patch_fonts_clean.py
```

#### 3. Rebuilding Text Tables
To reshape and compile Arabic dialogue and document JSONs into Naughty Dog binary string tables:
```powershell
python tools/build_mod_files.py
```

#### 4. Applying the Executable Patch Directly
To patch `tlou-i.exe` for seamless cursive joins, speaker formatting, and RTL layout:
```powershell
python tools/patch_exe.py
```

#### 5. Compiling the Standalone Installer
To recompile the sub-second PyInstaller executable:
```powershell
pyinstaller --onefile --console --clean --name TLOU_Arabic_Mod_Installer tools/nexus_installer_main.py
```

---

## 📜 Credits & Legal

- **Mod Creation & Reverse Engineering**: **Mohamed Moslem Allouch**
- **Original Game & Engine**: Naughty Dog / PlayStation Publishing LLC.
- **Font Assets**: Google Noto Sans Arabic (SIL Open Font License).
- **Compression**: Epic Games Tools (RAD Game Tools) Oodle SDK.

*This project is an open-source educational research and localization modification. All original game intellectual property belongs to Sony Interactive Entertainment and Naughty Dog.*
