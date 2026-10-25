import ctypes, io
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen

ft = ctypes.CDLL(r'C:\Program Files\Java\jdk-17\bin\freetype.dll')
ft_lib = ctypes.c_void_p()
ft.FT_Init_FreeType(ctypes.byref(ft_lib))

def test_font_program(manual_sub):
    din = TTFont('c:/Users/SlouMa/Desktop/tlou1/orig_fonts/DINPro-Regular.otf')
    hmtx = din['hmtx']
    cff = din['CFF '].cff
    top_dict = cff.topDictIndex[0]
    private = top_dict.Private
    nominalWidthX = private.nominalWidthX
    cs = top_dict.CharStrings

    pen1 = T2CharStringPen(width=269, glyphSet=None)
    pen1.moveTo((0, 0))
    pen1.lineTo((100, 100))
    pen1.endPath()
    cs1 = pen1.getCharString()
    cs1.private = private
    if manual_sub:
        cs1.program[0] = 269 - nominalWidthX

    idx = len(cs.charStringsIndex)
    cs.charStringsIndex.append(cs1)
    cs.charStrings['test1'] = idx
    top_dict.charset.append('test1')
    glyph_order = list(din.getGlyphOrder())
    glyph_order.append('test1')
    din.setGlyphOrder(glyph_order)
    din['maxp'].numGlyphs = len(glyph_order)
    hmtx['test1'] = (269, 0)
    for t in din['cmap'].tables:
        if t.isUnicode():
            t.cmap[0x0600] = 'test1'

    buf = io.BytesIO()
    din.save(buf)
    data = buf.getvalue()

    face = ctypes.c_void_p()
    c_data = (ctypes.c_char * len(data)).from_buffer_copy(data)
    ft.FT_New_Memory_Face(ft_lib, c_data, len(data), 0, ctypes.byref(face))
    ft.FT_Set_Pixel_Sizes(face, 0, 1000)
    gindex = ft.FT_Get_Char_Index(face, 0x0600)
    ft.FT_Load_Glyph(face, gindex, 0)
    
    # Read glyph metrics: advance.x
    glyph_slot = ctypes.c_void_p.from_address(face.value + 152).value
    advance_x = ctypes.c_long.from_address(glyph_slot + 72).value >> 6
    print(f'Manual Subtraction={manual_sub}: FreeType reported advance_x = {advance_x} (Expected: 269)')

test_font_program(False)
test_font_program(True)
