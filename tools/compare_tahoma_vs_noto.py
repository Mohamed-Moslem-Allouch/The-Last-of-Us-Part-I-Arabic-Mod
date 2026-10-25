from fontTools.ttLib import TTFont

# Build a font with tahoma
from restored_560 import inject_arabic_into_cff_font

inject_arabic_into_cff_font(
    r"c:\Users\SlouMa\Desktop\tlou1\orig_fonts\DINPro-Regular.otf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"c:\Users\SlouMa\Desktop\tlou1\tools\tahoma_din.otf"
)

f_tahoma = TTFont(r"c:\Users\SlouMa\Desktop\tlou1\tools\tahoma_din.otf")
f_noto = TTFont(r"c:\Users\SlouMa/Desktop/tlou1/extracted/fonts/DINPro-Regular.otf")
f_orig = TTFont(r"c:\Users\SlouMa/Desktop/tlou1/orig_fonts/DINPro-Regular.otf")

print("Tahoma DIN numGlyphs:", f_tahoma['maxp'].numGlyphs)
print("Noto DIN numGlyphs:", f_noto['maxp'].numGlyphs)
print("Orig DIN numGlyphs:", f_orig['maxp'].numGlyphs)

# Check glyph names in tahoma vs noto
tahoma_glyphs = set(f_tahoma.getGlyphOrder())
noto_glyphs = set(f_noto.getGlyphOrder())
orig_glyphs = set(f_orig.getGlyphOrder())

print("Added in Tahoma:", len(tahoma_glyphs - orig_glyphs))
print("Added in Noto:", len(noto_glyphs - orig_glyphs))

# Check overlap with orig glyphs
print("Did Tahoma overwrite any orig glyphs?:", tahoma_glyphs.intersection(orig_glyphs) != orig_glyphs)
print("Did Noto overwrite any orig glyphs?:", noto_glyphs.intersection(orig_glyphs) != orig_glyphs)
