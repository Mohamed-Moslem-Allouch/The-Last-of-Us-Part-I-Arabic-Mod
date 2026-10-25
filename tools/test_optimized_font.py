import os, json
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen

base_dir = r"c:\Users\SlouMa\Desktop\tlou1"
ext_dir = os.path.join(base_dir, "extracted")

# 1. Collect all characters used in notes and subtitles
used_codepoints = set()

# Basic Arabic
for cp in range(0x0600, 0x0660):
    used_codepoints.add(cp)
# Presentation Forms A & B
for cp in range(0xFB50, 0xFDFF):
    used_codepoints.add(cp)
for cp in range(0xFE70, 0xFEFD):
    used_codepoints.add(cp)

with open(os.path.join(ext_dir, "arabic_subtitles.json"), 'r', encoding='utf-8') as f:
    subs = json.load(f)
for k, v in subs.items():
    for c in v.get('ar_reshaped', ''):
        used_codepoints.add(ord(c))

with open(os.path.join(ext_dir, "arabic_notes.json"), 'r', encoding='utf-8') as f:
    notes = json.load(f)
for k, v in notes.items():
    for c in v.get('ar_reshaped', ''):
        used_codepoints.add(ord(c))

print("Total used Arabic codepoints needed by mod:", len(used_codepoints))

def inject_optimized_arabic(orig_cff_path, arabic_src_path, out_path, overlap=6):
    din = TTFont(orig_cff_path)
    ar_font = TTFont(arabic_src_path)

    cff = din['CFF '].cff
    top_dict = cff.topDictIndex[0]
    cs = top_dict.CharStrings

    scale = 1000.0 / ar_font['head'].unitsPerEm
    ar_glyphset = ar_font.getGlyphSet()
    ar_cmap = ar_font.getBestCmap()

    # Only include codepoints that are actually in used_codepoints
    needed_codepoints = {cp: ar_cmap[cp] for cp in used_codepoints if cp in ar_cmap}
    unique_gnames = set(needed_codepoints.values())

    glyph_order = list(din.getGlyphOrder())
    hmtx = din['hmtx']
    unicode_tables = [t for t in din['cmap'].tables if t.isUnicode()]

    added_count = 0
    for gname in unique_gnames:
        if gname in cs.charStrings:
            continue
        try:
            g = ar_glyphset[gname]
            scaled_width = int(round(g.width * scale))
            # Apply slight overlap to prevent outline seam split
            final_width = max(0, scaled_width - overlap)

            pen = T2CharStringPen(width=final_width, glyphSet=ar_glyphset)
            tpen = TransformPen(pen, (scale, 0, 0, scale, 0, 0))
            g.draw(tpen)
            new_cs = pen.getCharString()
            new_cs.private = top_dict.Private

            idx = len(cs.charStringsIndex)
            cs.charStringsIndex.append(new_cs)
            cs.charStrings[gname] = idx

            glyph_order.append(gname)
            top_dict.charset.append(gname)
            lsb = int(round(ar_font['hmtx'][gname][1] * scale))
            hmtx[gname] = (final_width, lsb)
            added_count += 1
        except Exception:
            pass

    din.setGlyphOrder(glyph_order)
    din['maxp'].numGlyphs = len(glyph_order)

    for cp, gname in needed_codepoints.items():
        if gname in cs.charStrings:
            for table in unicode_tables:
                table.cmap[cp] = gname

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    din.save(out_path)
    
    cff_size = len(din.getTableData('CFF '))
    print(f"Saved {out_path}: added {added_count} glyphs. Total glyphs: {len(glyph_order)}. CFF size: {cff_size:,} bytes (File size: {os.path.getsize(out_path):,} bytes)")

inject_optimized_arabic(
    os.path.join(base_dir, "orig_fonts", "DINPro-Regular.otf"),
    os.path.join(base_dir, "NotoSansArabic-Regular.ttf"),
    os.path.join(base_dir, "tools", "opt_DINPro-Regular.otf")
)
inject_optimized_arabic(
    os.path.join(base_dir, "orig_fonts", "DINPro-Medium.otf"),
    os.path.join(base_dir, "NotoSansArabic-Medium.ttf"),
    os.path.join(base_dir, "tools", "opt_DINPro-Medium.otf")
)
