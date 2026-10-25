from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont
import sys
sys.path.append('c:/Users/SlouMa/Desktop/tlou1/tools')
from bidi_engine import reshape_text

# Text from the screenshot
text = 'هيا، لنذهب.'
reshaped = reshape_text(text)

# We have NotoSansArabic-Regular.ttf
font_path = 'c:/Users/SlouMa/Desktop/tlou1/NotoSansArabic-Regular.ttf'
font_size = 42

def simulate_subtitle_render(overlap_units):
    # Load font with PIL
    f = ImageFont.truetype(font_path, font_size)
    tt = TTFont(font_path)
    scale = font_size / 1000.0

    # Create image
    img = Image.new('RGBA', (300, 100), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # In game: characters are placed one by one at x += advance_width
    # Each character is rendered with outline
    cur_x = 20
    cur_y = 20

    # Let's render each glyph individually to simulate character-by-character rendering
    for c in reshaped:
        cp = ord(c)
        gname = tt.getBestCmap().get(cp)
        w_orig = tt['hmtx'][gname][0] if gname else 500
        
        # Advance width in pixels:
        w_px = (w_orig - overlap_units) * scale

        # Draw glyph with outline:
        # Outline is drawn at offsets (-2, -2) to (+2, +2)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx*dx + dy*dy <= 4:
                    draw.text((cur_x + dx, cur_y + dy), c, font=f, fill=(0, 0, 0, 255))
        # Draw white fill
        draw.text((cur_x, cur_y), c, font=f, fill=(255, 255, 255, 255))

        cur_x += w_px

    return img

img6 = simulate_subtitle_render(6)
img6.save('c:/Users/SlouMa/Desktop/tlou1/tools/sim_overlap_6.png')

img40 = simulate_subtitle_render(40)
img40.save('c:/Users/SlouMa/Desktop/tlou1/tools/sim_overlap_40.png')

img60 = simulate_subtitle_render(60)
img60.save('c:/Users/SlouMa/Desktop/tlou1/tools/sim_overlap_60.png')

img80 = simulate_subtitle_render(80)
img80.save('c:/Users/SlouMa/Desktop/tlou1/tools/sim_overlap_80.png')

print("Rendered simulations!")
