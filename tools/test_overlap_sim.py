from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import sys, os, unicodedata
sys.path.append('c:/Users/SlouMa/Desktop/tlou1/tools')
from bidi_engine import reshape_text

font_path = 'c:/Users/SlouMa/Desktop/tlou1/NotoSansArabic-Regular.ttf'
font_size = 42
text = 'هيا، لنذهب.'
reshaped = reshape_text(text)

def render_with_overlap(overlap_amount):
    f = ImageFont.truetype(font_path, font_size)
    tt = TTFont(font_path)
    scale = font_size / 1000.0

    img = Image.new('RGB', (350, 80), (30, 25, 20))
    draw = ImageDraw.Draw(img)

    cur_x = 30
    cur_y = 20

    for c in reshaped:
        cp = ord(c)
        gname = tt.getBestCmap().get(cp)
        w_orig = tt['hmtx'][gname][0] if gname else 500
        
        name = unicodedata.name(c, '')
        is_connecting = ('FINAL' in name or 'MEDIAL' in name)
        
        ov = overlap_amount if is_connecting else 0
        w_px = (w_orig - ov) * scale

        # Draw with outline
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx*dx + dy*dy <= 4:
                    draw.text((cur_x + dx, cur_y + dy), c, font=f, fill=(0, 0, 0))
        draw.text((cur_x, cur_y), c, font=f, fill=(255, 255, 255))

        cur_x += w_px

    img.save(f'c:/Users/SlouMa/Desktop/tlou1/tools/render_ov_{overlap_amount}.png')
    print(f'Saved render_ov_{overlap_amount}.png')

for ov in [0, 50, 75, 90, 100]:
    render_with_overlap(ov)
