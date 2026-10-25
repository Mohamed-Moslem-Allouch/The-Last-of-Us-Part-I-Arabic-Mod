import os
import sys
import json
import struct
from bidi_engine import wrap_and_reshape_doc, reshape_text

LANGUAGE_FRENCH_SID = 0xade282955d723c6c

ALL_SPEAKER_SIDS = set([
    0x150671bb41de82, 0x30948c1febed6fe, 0x33bc9632fcd20a2, 0x62ecddd29aa6db0,
    0x140b5adf4aaa1003, 0x15e37817c6ab5195, 0x194d6b3c1ef8e38d, 0x1f4d31c27841faa5,
    0x22d65251f7766ef0, 0x237ca314da0ceb38, 0x241d1f330b172f26, 0x263e30c6c495e0c9,
    0x2715c18fabe0ae34, 0x27749eb110a434de, 0x2926b22772434104, 0x296e44ba07857935,
    0x297b106e608a9bc0, 0x2e535f9d5a1d7d34, 0x2f7d58741b8f6c48, 0x32b30ef4000829f0,
    0x33b2143fb174e0f0, 0x3751cc9e0c21c258, 0x380db7563dbab8cf, 0x38591b489a6a19d5,
    0x3d6a860b2edb7666, 0x3f06e94ceafdf860, 0x401af5f56bcd2acc, 0x405bf87db319cc4b,
    0x41dd897d4e189a30, 0x432e5d408df58a84, 0x44b90efd9d5219eb, 0x479ca035d92a4629,
    0x4a8c812dfb7ae846, 0x4aa652210ec85fd1, 0x4d798bb951e2d618, 0x4dd5069dc94a2e30,
    0x5086a8ae1b5f3502, 0x52236c4ef70aca4d, 0x56e34e55998c0a21, 0x58a32bce545413b2,
    0x667165d091c65826, 0x6bb050296ca8bc3c, 0x6c9b752e3689bc1e, 0x6cc15e4c018b03d7,
    0x6e50ccccfe0972ba, 0x71564ccbdf4af73e, 0x72be6056b96b4b20, 0x75ce622e13f7738f,
    0x7979e3da69730cef, 0x79d85b6ddd3816be, 0x7d8935dd9e12dacd, 0x7dc8483f74c4ebd0,
    0x7dea4a1298f7cee5, 0x7f899e4bd6ee9bcb, 0x811cb49e32ba7926, 0x82f20518eaf8f900,
    0x8b77da00b6a2ee19, 0x8b9231639cfa78e6, 0x8bd6b6f74f4a98a4, 0x8c8ec92df47742af,
    0x8e8b242377ddf7cd, 0x989b52217d41d7cc, 0x99c883fb316e6e86, 0x9a5db806377b6597,
    0x9d4bbc7e1e848dc3, 0x9ea9250cb1a3667d, 0x9eca400317fad1e5, 0xab96e1086e873922,
    0xabae344a82d8aba1, 0xad138810056ef6d0, 0xad174c23c48b4b5c, 0xaf079722f9bf9572,
    0xb2562982a4ced337, 0xb27f1b20eaaa03a6, 0xb3aea88e6d697bcc, 0xb5836010a1bbe8f6,
    0xb76abc07c3b109ff, 0xbda419d50fe61598, 0xbe8be323020615b2, 0xc0a5edd9b0ceeb10,
    0xc2c8201cb27e173e, 0xc652b3f90ebb66c4, 0xc98dccb7241e9517, 0xca14a3b35d84ee61,
    0xce84ec83d03c251c, 0xd1c0e5ef4e8a54ce, 0xd4078155ac5224c4, 0xd618155bdf1f5726,
    0xd7c0d1c3d8264abb, 0xd922d7eae5df7806, 0xddaa99ad372f16b9, 0xe085ac8252172077,
    0xe5f3facd4d217a27, 0xe96eb08dfc5ec3e6, 0xe9c9e17db706cb9e, 0xebad57158a68aeae,
    0xef04c5d6a3713b1c, 0xf29ee0ff8fad14f4, 0xf40a9525675bea7f, 0xf70bb254b0f63741,
    0xfb651323248d0258, 0xfba2811203350152, 0xfd2e7b17737c2949, 0xfe87edd44e0ff25b,
    0xff6bd7172d25e4fe,
])

CUSTOM_DOC_TRANSLATIONS = {
    # GAM_MES_HOM_BUY_DINNER_NOTE_TEXT (Joel's fridge note to Sarah)
    0xfc508c5ef695572c: "سأتأخر الليلة في العمل.<br>اطلبي عشاءً لكِ ولا تنتظريني.<br>أراكِ في الصباح.<br><br>بابا",
    # GAM_MES_HOM_BIRTHDAY_CARD_TEXT (Sarah's birthday card to Joel)
    0x8f25d0bdd854d642: "لستَ عجوزاً بعد! (ليس تماماً)<br>(عيد ميلاد سعيد)<br>أبي العزيز،<br>لنرى... أنت بالكاد تتواجد في البيت،<br>وتكره الموسيقى التي أستمع إليها،<br>ولا تطيق الأفلام التي أحبها...<br>ومع كل هذا، تنجح كل سنة في أن تكون أفضل أب في العالم.<br>كيف تفعل ذلك بحق السماء؟<br>عيد ميلاد سعيد يا أفضل أب!<br>مع كل حبي، سارة"
}

def is_speaker_name(sid: int, text: str) -> bool:
    if sid in ALL_SPEAKER_SIDS:
        return True
    t = text.strip()
    if len(t.split()) <= 2 and t.isalpha() and len(t) <= 15:
        if t.lower() not in ('yeah', 'no', 'ok', 'yes', 'none', 'man'):
            return True
    return False

def patch_binary_text_file(orig_path: str, replacements_by_sid: dict) -> bytes:
    """
    Takes an original Naughty Dog binary text file (.common, .subtitles, .subtitles-systemic),
    preserves the EXACT original string block (including UNKNOWN STRING!!! at offset 0),
    preserves ALL untouched entries at their EXACT original offsets,
    and for modified SIDs, appends the new text to the end of the string block and updates the offset in the table.
    """
    with open(orig_path, 'rb') as f:
        data = bytearray(f.read())

    count = struct.unpack('<I', data[:4])[0]
    base = 4 + count * 16

    str_block = bytearray(data[base:])
    replaced_count = 0

    for i in range(count):
        sid, off = struct.unpack('<QQ', data[4+i*16 : 20+i*16])
        if sid in replacements_by_sid:
            new_text = replacements_by_sid[sid]
            if isinstance(new_text, str):
                raw = new_text.encode('utf-8')
            else:
                raw = new_text
            new_off = len(str_block)
            str_block.extend(raw + b'\x00')
            data[4+i*16+8 : 20+i*16] = struct.pack('<Q', new_off)
            replaced_count += 1

    result = bytes(data[:base]) + bytes(str_block)
    print(f"Patched {os.path.basename(orig_path)}: updated {replaced_count}/{count} entries. Orig size: {len(data)}, New size: {len(result)}")
    return result

def read_text_entries(orig_path: str):
    """
    Reads (sid, text) from original binary file without modifying it.
    """
    entries = []
    with open(orig_path, 'rb') as f:
        data = f.read()
    count = struct.unpack('<I', data[:4])[0]
    base = 4 + count * 16
    for i in range(count):
        sid, off = struct.unpack('<QQ', data[4+i*16 : 20+i*16])
        end = data.find(b'\x00', base + off)
        text = data[base+off:end].decode('utf-8', errors='replace')
        entries.append((sid, text))
    return entries

def build_fre_common(orig_eng_path: str, notes_json_path: str, out_path: str) -> bytes:
    print("Building text2/fre.common (100% English UI + Arabic Document Reader)...")
    with open(notes_json_path, 'r', encoding='utf-8') as f:
        notes_dict = json.load(f)

    replacements = {}
    # French slot label displays "Arabic"
    replacements[LANGUAGE_FRENCH_SID] = "Arabic"

    # Author signature beside EXTRAS in main & pause menus
    replacements[0x8b09f4410a6ce170] = "EXTRAS (Mohamed Moslem Allouch)"
    replacements[0x2ba0e9f19451ca0e] = "Extras (Mohamed Moslem Allouch)"
    replacements[0x71971f150b00bfef] = "Extras (Mohamed Moslem Allouch)"
    replacements[0xa83d9e65a9554011] = "Extras (Mohamed Moslem Allouch)"

    for k, v in notes_dict.items():
        sid = int(k)
        if sid in CUSTOM_DOC_TRANSLATIONS:
            raw_ar = CUSTOM_DOC_TRANSLATIONS[sid]
            replacements[sid] = wrap_and_reshape_doc(raw_ar, max_chars=46)
        elif v.get('ar'):
            replacements[sid] = wrap_and_reshape_doc(v['ar'], max_chars=46)
        elif v.get('ar_reshaped'):
            replacements[sid] = v['ar_reshaped']

    packed = patch_binary_text_file(orig_eng_path, replacements)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(packed)
    return packed

def build_fre_subtitles(orig_eng_sub_path: str, subtitles_json_path: str, out_path: str) -> bytes:
    print("Building text2/fre.subtitles (Arabic Dialogue + English Speaker Names)...")
    orig_entries = read_text_entries(orig_eng_sub_path)
    sub_dict = {}
    if os.path.exists(subtitles_json_path):
        with open(subtitles_json_path, 'r', encoding='utf-8') as f:
            sub_dict = json.load(f)

    replacements = {}
    for sid, text in orig_entries:
        stripped = text.strip()
        # Keep speaker names 100% in English
        if is_speaker_name(sid, stripped):
            continue
        elif stripped in sub_dict and sub_dict[stripped].get('ar_reshaped'):
            replacements[sid] = sub_dict[stripped]['ar_reshaped']

    packed = patch_binary_text_file(orig_eng_sub_path, replacements)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(packed)
    return packed

def build_fre_subtitles_systemic(orig_eng_sys_path: str, subtitles_json_path: str, out_path: str) -> bytes:
    print("Building text2/fre.subtitles-systemic (Barks & Ambient Dialogue)...")
    orig_entries = read_text_entries(orig_eng_sys_path)
    sub_dict = {}
    if os.path.exists(subtitles_json_path):
        with open(subtitles_json_path, 'r', encoding='utf-8') as f:
            sub_dict = json.load(f)

    replacements = {}
    for sid, text in orig_entries:
        stripped = text.strip()
        if is_speaker_name(sid, stripped):
            continue
        elif stripped in sub_dict and sub_dict[stripped].get('ar_reshaped'):
            replacements[sid] = sub_dict[stripped]['ar_reshaped']

    packed = patch_binary_text_file(orig_eng_sys_path, replacements)
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

    fre_common_out = os.path.join(mod_dir, "text2", "fre.common")
    fre_sub_out = os.path.join(mod_dir, "text2", "fre.subtitles")
    fre_sys_out = os.path.join(mod_dir, "text2", "fre.subtitles-systemic")

    fre_common_bytes = build_fre_common(eng_common_orig, notes_json, fre_common_out)
    fre_sub_bytes = build_fre_subtitles(eng_sub_orig, sub_json, fre_sub_out)
    fre_sys_bytes = build_fre_subtitles_systemic(eng_sys_orig, sub_json, fre_sys_out)

    # Clean compact fonts with 100% original Latin + clean Google Noto Sans Arabic (strictly used glyphs)
    from patch_fonts_clean import build_clean_compact_fonts
    build_clean_compact_fonts()
    fonts_dir = os.path.join(ext_dir, "fonts")
    din_reg = open(os.path.join(fonts_dir, "DINPro-Regular.otf"), "rb").read()
    din_med = open(os.path.join(fonts_dir, "DINPro-Medium.otf"), "rb").read()

    # CRITICAL:
    # 1. DO NOT TOUCH text2/eng.common (keep 100% original from backup core.psarc)!
    # 2. DO NOT TOUCH fonts/files.json!
    # 3. DO NOT TOUCH fonts/HelveticaNeueBold.ttf!
    replacements = {
        "text2/fre.common": fre_common_bytes,
        "text2/fre.subtitles": fre_sub_bytes,
        "text2/fre.subtitles-systemic": fre_sys_bytes,
        "text2/eng.common": fre_common_bytes,
        "text2/eng.subtitles": fre_sub_bytes,
        "text2/eng.subtitles-systemic": fre_sys_bytes,
        "fonts/DINPro-Regular.otf": din_reg,
        "fonts/DINPro-Medium.otf": din_med,
    }

    return replacements

if __name__ == "__main__":
    create_all_mod_files()
