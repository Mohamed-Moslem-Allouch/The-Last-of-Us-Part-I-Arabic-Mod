import os
import io
from fontTools.ttLib import TTFont

def generate_patched_font(src_font_path: str, family: str, subfamily: str, full_name: str, ps_name: str) -> bytes:
    font = TTFont(src_font_path)
    
    # Update name table
    for record in font['name'].names:
        if record.nameID == 1:
            record.string = family.encode('utf-16be' if record.platformID == 3 else 'latin1')
        elif record.nameID == 2:
            record.string = subfamily.encode('utf-16be' if record.platformID == 3 else 'latin1')
        elif record.nameID == 4:
            record.string = full_name.encode('utf-16be' if record.platformID == 3 else 'latin1')
        elif record.nameID == 6:
            record.string = ps_name.encode('utf-16be' if record.platformID == 3 else 'latin1')
            
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()

def build_all_fonts(out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    src_arabic = r"D:\gow3-windows\scripts\fonts\NotoSansArabic.ttf"
    
    fonts_to_build = [
        ("DINPro-Regular.otf", "DINPro", "Regular", "DINPro Regular", "DINPro-Regular"),
        ("DINPro-Medium.otf", "DINPro", "Medium", "DINPro Medium", "DINPro-Medium"),
        ("HelveticaNeueBold.ttf", "Helvetica Neue", "Bold", "Helvetica Neue Bold", "HelveticaNeueBold"),
    ]
    
    for filename, family, subfamily, full_name, ps_name in fonts_to_build:
        data = generate_patched_font(src_arabic, family, subfamily, full_name, ps_name)
        out_path = os.path.join(out_dir, filename)
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"Generated {filename}: {len(data)} bytes")

if __name__ == "__main__":
    build_all_fonts(r"c:\Users\SlouMa\Desktop\tlou1\extracted\fonts")
