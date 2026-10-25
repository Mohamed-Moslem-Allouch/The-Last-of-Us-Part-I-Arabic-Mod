import os
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen

def inject_arabic_into_cff_font(orig_cff_path: str, arabic_src_path: str, out_path: str):
    print(f"Injecting Arabic glyphs from {arabic_src_path} into {orig_cff_path}...")
    din = TTFont(orig_cff_path)
    ar_font = TTFont(arabic_src_path)

    cff = din['CFF '].cff
    top_dict = cff.topDictIndex[0]
    cs = top_dict.CharStrings

    scale = 1000.0 / ar_font['head'].unitsPerEm
    ar_glyphset = ar_font.getGlyphSet()
    ar_cmap = ar_font.getBestCmap()

    # Collect Arabic codepoints: Basic (0x0600-0x06FF), Pres-A (0xFB50-0xFDFF), Pres-B (0xFE70-0xFEFC)
    ar_codepoints = {
        cp: gname for cp, gname in ar_cmap.items()
        if (0x0600 <= cp <= 0x06FF) or (0xFB50 <= cp <= 0xFDFF) or (0xFE70 <= cp <= 0xFEFC)
    }

    unique_gnames = set(ar_codepoints.values())
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
            pen = T2CharStringPen(width=scaled_width, glyphSet=ar_glyphset)
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
            hmtx[gname] = (scaled_width, lsb)
            added_count += 1
        except Exception as e:
            pass

    din.setGlyphOrder(glyph_order)
    din['maxp'].numGlyphs = len(glyph_order)

    # Update unicode cmap tables
    for cp, gname in ar_codepoints.items():
        if gname in cs.charStrings:
            for table in unicode_tables:
                table.cmap[cp] = gname

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    din.save(out_path)
    print(f"Saved {out_path}: added {added_count} Arabic glyphs. Total glyphs: {len(glyph_order)}.")

def build_all_cff_fonts():
    orig_dir = r"c:\Users\SlouMa\Desktop\tlou1\orig_fonts"
    out_dir = r"c:\Users\SlouMa\Desktop\tlou1\extracted\fonts"

    # 1. DINPro-Regular.otf
    orig_reg = os.path.join(orig_dir, "DINPro-Regular.otf")
    out_reg = os.path.join(out_dir, "DINPro-Regular.otf")
    inject_arabic_into_cff_font(orig_reg, r"C:\Windows\Fonts\tahoma.ttf", out_reg)

    # 2. DINPro-Medium.otf
    orig_med = os.path.join(orig_dir, "DINPro-Medium.otf")
    out_med = os.path.join(out_dir, "DINPro-Medium.otf")
    tahoma_bold = r"C:\Windows\Fonts\tahomabd.ttf" if os.path.exists(r"C:\Windows\Fonts\tahomabd.ttf") else r"C:\Windows\Fonts\tahoma.ttf"
    inject_arabic_into_cff_font(orig_med, tahoma_bold, out_med)

if __name__ == "__main__":
    build_all_cff_fonts()
