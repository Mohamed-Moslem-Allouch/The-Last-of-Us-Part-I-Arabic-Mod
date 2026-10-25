import os
import sys
import json
from text_packer import parse_text_file, pack_text_file

LANGUAGE_FRENCH_SID = 0xade282955d723c6c

def build_eng_common(orig_eng_path: str, out_path: str) -> bytes:
    """
    Takes original eng.common and only changes LANGUAGE_FRENCH to 'Arabic'
    so that in the Options menu the French slot displays 'Arabic'!
    """
    print("Building text2/eng.common with slot name 'Arabic'...")
    eng_entries = parse_text_file(orig_eng_path)
    modified = []
    for sid, text in eng_entries:
        if sid == LANGUAGE_FRENCH_SID:
            modified.append((sid, "Arabic"))
        else:
            modified.append((sid, text))
    packed = pack_text_file(modified)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(packed)
    return packed

def build_fre_common(orig_eng_path: str, notes_json_path: str, out_path: str) -> bytes:
    """
    Takes original eng.common, sets LANGUAGE_FRENCH to 'Arabic',
    replaces only the 415 note/paper/book reader texts with reshaped Arabic,
    and keeps all other 16,500+ strings 100% original English.
    """
    print("Building text2/fre.common (English UI + Arabic Note/Book Reader)...")
    eng_entries = parse_text_file(orig_eng_path)

    with open(notes_json_path, 'r', encoding='utf-8') as f:
        notes_dict = json.load(f)

    notes_by_sid = {int(k): v['ar_reshaped'] for k, v in notes_dict.items() if v.get('ar_reshaped')}
    print(f"Loaded {len(notes_by_sid)} Arabic reader note texts to inject into fre.common.")

    modified_entries = []
    replaced_count = 0
    for sid, text in eng_entries:
        if sid == LANGUAGE_FRENCH_SID:
            modified_entries.append((sid, "Arabic"))
        elif sid in notes_by_sid:
            ar_text = notes_by_sid[sid]
            modified_entries.append((sid, ar_text))
            replaced_count += 1
        else:
            # 100% original English text for UI, menus, settings, HUD!
            modified_entries.append((sid, text))

    print(f"Replaced {replaced_count} note reader texts in fre.common. Keeping remaining {len(modified_entries)-replaced_count} UI strings in pure English.")
    packed = pack_text_file(modified_entries)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(packed)
    return packed

def build_fre_subtitles(orig_eng_sub_path: str, subtitles_json_path: str, out_path: str) -> bytes:
    print("Building text2/fre.subtitles (Arabic Narrative Dialogue)...")
    eng_entries = parse_text_file(orig_eng_sub_path)

    sub_dict = {}
    if os.path.exists(subtitles_json_path):
        with open(subtitles_json_path, 'r', encoding='utf-8') as f:
            sub_dict = json.load(f)

    modified_entries = []
    translated_count = 0
    for sid, text in eng_entries:
        stripped = text.strip()
        if stripped in sub_dict and sub_dict[stripped].get('ar_reshaped'):
            ar_text = sub_dict[stripped]['ar_reshaped']
            modified_entries.append((sid, ar_text))
            translated_count += 1
        else:
            modified_entries.append((sid, text))

    print(f"Translated {translated_count} / {len(modified_entries)} dialogue subtitle lines into Arabic.")
    packed = pack_text_file(modified_entries)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(packed)
    return packed

def build_fre_subtitles_systemic(orig_eng_sys_path: str, subtitles_json_path: str, out_path: str) -> bytes:
    print("Building text2/fre.subtitles-systemic (Barks & Ambient Dialogue)...")
    eng_entries = parse_text_file(orig_eng_sys_path)

    sub_dict = {}
    if os.path.exists(subtitles_json_path):
        with open(subtitles_json_path, 'r', encoding='utf-8') as f:
            sub_dict = json.load(f)

    modified_entries = []
    translated_count = 0
    for sid, text in eng_entries:
        stripped = text.strip()
        if stripped in sub_dict and sub_dict[stripped].get('ar_reshaped'):
            ar_text = sub_dict[stripped]['ar_reshaped']
            modified_entries.append((sid, ar_text))
            translated_count += 1
        else:
            modified_entries.append((sid, text))

    print(f"Translated {translated_count} / {len(modified_entries)} systemic subtitle lines.")
    packed = pack_text_file(modified_entries)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(packed)
    return packed

def create_all_mod_files():
    base_dir = r"c:\Users\SlouMa\Desktop\tlou1"
    ext_dir = os.path.join(base_dir, "extracted")
    mod_dir = os.path.join(base_dir, "mod_files")

    eng_common_orig = os.path.join(ext_dir, "text2", "eng.common")
    eng_sub_orig = os.path.join(ext_dir, "text2", "eng.subtitles")
    eng_sys_orig = os.path.join(ext_dir, "text2", "eng.subtitles-systemic")

    notes_json = os.path.join(ext_dir, "arabic_notes.json")
    sub_json = os.path.join(ext_dir, "arabic_subtitles.json")

    eng_common_out = os.path.join(mod_dir, "text2", "eng.common")
    fre_common_out = os.path.join(mod_dir, "text2", "fre.common")
    fre_sub_out = os.path.join(mod_dir, "text2", "fre.subtitles")
    fre_sys_out = os.path.join(mod_dir, "text2", "fre.subtitles-systemic")

    eng_common_bytes = build_eng_common(eng_common_orig, eng_common_out)
    fre_common_bytes = build_fre_common(eng_common_orig, notes_json, fre_common_out)
    fre_sub_bytes = build_fre_subtitles(eng_sub_orig, sub_json, fre_sub_out)
    fre_sys_bytes = build_fre_subtitles_systemic(eng_sys_orig, sub_json, fre_sys_out)

    # Read the native OpenType CFF fonts with 100% original English + added Arabic
    fonts_dir = os.path.join(ext_dir, "fonts")
    din_reg = open(os.path.join(fonts_dir, "DINPro-Regular.otf"), "rb").read()
    din_med = open(os.path.join(fonts_dir, "DINPro-Medium.otf"), "rb").read()

    replacements = {
        "text2/eng.common": eng_common_bytes,
        "text2/fre.common": fre_common_bytes,
        "text2/fre.subtitles": fre_sub_bytes,
        "text2/fre.subtitles-systemic": fre_sys_bytes,
        "fonts/DINPro-Regular.otf": din_reg,
        "fonts/DINPro-Medium.otf": din_med,
    }

    return replacements

if __name__ == "__main__":
    create_all_mod_files()
