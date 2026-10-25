import os, json, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.misc.roundTools import otRound

def get_arabic_connection_sides(codepoint: int) -> tuple[bool, bool]:
    """
    Returns (connects_left, connects_right) for Arabic Presentation Forms in visual LTR.
    - Initial forms connect on the LEFT side of the glyph in visual LTR.
    - Final forms connect on the RIGHT side of the glyph in visual LTR.
    - Medial forms connect on BOTH sides.
    """
    if codepoint == 0x0640 or (0xFE70 <= codepoint <= 0xFE7F):  # Tatweel / Tashkeel
        return True, True

    decomp = unicodedata.decomposition(chr(codepoint))
    if decomp.startswith("<initial>"):
        return True, False
    elif decomp.startswith("<medial>"):
        return True, True
    elif decomp.startswith("<final>"):
        return False, True
    return False, False

def get_baseline_y_band(donor_glyph_set, cmap: dict, scale: float) -> tuple[float, float]:
    """
    Measures U+0640 (Tatweel 'ـ') in the donor font to get the exact Y-band
    of the horizontal connecting baseline stroke.
    """
    tatweel_name = cmap.get(0x0640)
    if tatweel_name and tatweel_name in donor_glyph_set:
        bp = BoundsPen(donor_glyph_set)
        donor_glyph_set[tatweel_name].draw(TransformPen(bp, (scale, 0, 0, scale, 0, 0)))
        if bp.bounds:
            _, y_min, _, y_max = bp.bounds
            return (y_min - 35.0, y_max + 35.0)
    return (-70.0, 220.0)

class RecordingPen(BasePen):
    """Records scaled drawing operations so we can inspect baseline tail bounds before stretching."""
    def __init__(self, glyphSet=None):
        super().__init__(glyphSet)
        self.ops = []

    def _moveTo(self, pt):
        self.ops.append(("moveTo", (pt,)))

    def _lineTo(self, pt):
        self.ops.append(("lineTo", (pt,)))

    def _curveToOne(self, pt1, pt2, pt3):
        self.ops.append(("curveTo", (pt1, pt2, pt3)))

    def _closePath(self):
        self.ops.append(("closePath", ()))

    def _endPath(self):
        self.ops.append(("endPath", ()))

def build_clean_compact_fonts():
    base_dir = r"c:\Users\SlouMa\Desktop\tlou1"
    ext_dir = os.path.join(base_dir, "extracted")
    out_dir = os.path.join(ext_dir, "fonts")
    os.makedirs(out_dir, exist_ok=True)

    # Collect only characters strictly needed by the Arabic mod
    strictly_used = set()
    with open(os.path.join(ext_dir, "arabic_subtitles.json"), 'r', encoding='utf-8') as f:
        subs = json.load(f)
    for k, v in subs.items():
        for c in v.get('ar_reshaped', ''):
            strictly_used.add(ord(c))

    with open(os.path.join(ext_dir, "arabic_notes.json"), 'r', encoding='utf-8') as f:
        notes = json.load(f)
    for k, v in notes.items():
        for c in v.get('ar_reshaped', ''):
            strictly_used.add(ord(c))

    # Basic Arabic alphabet
    for cp in range(0x0621, 0x0653):
        strictly_used.add(cp)
    # Presentation Forms-B (standard Arabic reshaped forms)
    for cp in range(0xFE70, 0xFEFD):
        strictly_used.add(cp)

    def inject(
        orig_path,
        src_path,
        out_path,
        right_overhang=100,
        tail_threshold=35,
        canary_scale=None,
    ):
        font_name = os.path.basename(orig_path)
        print(f"Injecting Arabic glyphs into {font_name} (canary_scale={canary_scale})...")
        target_font = TTFont(orig_path)
        ar_font = TTFont(src_path)

        cff_table = target_font["CFF "].cff
        top_dict = cff_table.topDictIndex[0]
        private_dict = top_dict.Private
        char_strings = top_dict.CharStrings

        scale = 1000.0 / ar_font["head"].unitsPerEm
        ar_glyphset = ar_font.getGlyphSet()
        ar_cmap = ar_font.getBestCmap()

        baseline_y_band = get_baseline_y_band(ar_glyphset, ar_cmap, scale)
        y_min_band, y_max_band = baseline_y_band

        needed_codepoints = {cp: ar_cmap[cp] for cp in strictly_used if cp in ar_cmap}
        glyph_order = list(target_font.getGlyphOrder())
        unicode_tables = [t for t in target_font["cmap"].tables if t.isUnicode()]

        default_w = getattr(private_dict, "defaultWidthX", 0)
        nominal_w = getattr(private_dict, "nominalWidthX", 0)

        added = 0
        for cp, gname in needed_codepoints.items():
            if gname in char_strings.charStrings:
                continue

            donor_glyph = ar_glyphset[gname]
            orig_width = otRound(donor_glyph.width * scale)
            connects_left, connects_right = get_arabic_connection_sides(cp)

            # Canary Test: Scale initial heh U+FEEB by canary_scale
            scale_y = scale * canary_scale if (canary_scale and cp == 0xFEEB) else scale

            # Pass 1: Record scaled outline coordinates
            rec_pen = RecordingPen(glyphSet=ar_glyphset)
            donor_glyph.draw(TransformPen(rec_pen, (scale, 0, 0, scale_y, 0, 0)))

            all_x = []
            baseline_x = []
            for op, pts in rec_pen.ops:
                for x, y in pts:
                    all_x.append(x)
                    if y_min_band <= y <= y_max_band:
                        baseline_x.append(x)

            if not all_x:
                # Empty or space glyph
                cff_w = None if orig_width == default_w else (orig_width - nominal_w)
                t2_pen = T2CharStringPen(width=cff_w, glyphSet=ar_glyphset)
                char_string = t2_pen.getCharString(
                    private=private_dict,
                    globalSubrs=cff_table.GlobalSubrs,
                    optimize=True,
                )
                idx = len(char_strings.charStringsIndex)
                char_strings.charStringsIndex.append(char_string)
                char_strings.charStrings[gname] = idx
                glyph_order.append(gname)
                top_dict.charset.append(gname)
                target_font["hmtx"].metrics[gname] = (orig_width, 0)
                added += 1
                continue

            # Find the true X extremes of the connecting baseline stroke
            tail_x_min = min(baseline_x) if baseline_x else min(all_x)
            tail_x_max = max(baseline_x) if baseline_x else max(all_x)

            # 1. Left Tail: Anchor strictly at x = 0 (lsb = 0) for left-connecting glyphs
            dx = -tail_x_min if (connects_left and tail_x_min != 0) else 0
            new_width = max(0, otRound(orig_width + (dx if connects_left else 0)))

            # 2. Right Tail: Put 100% of overlap on the right tail (xMax = new_width + right_overhang)
            target_right_x = new_width + right_overhang

            def make_adjust_point(cur_dx, c_left, c_right, t_min, t_max, tgt_r, thresh, y_min, y_max):
                def adjust_point(pt):
                    x, y = pt
                    x_shifted = x + cur_dx
                    if y_min <= y <= y_max:
                        # Left baseline tail: anchor strictly at 0 + offset, NEVER negative
                        if c_left and x <= (t_min + thresh):
                            offset_from_tip = x - t_min
                            x_shifted = max(0.0, offset_from_tip)
                        # Right baseline tail: stretch out to target_right_x
                        if c_right and x >= (t_max - thresh):
                            offset_from_tip = t_max - x
                            x_shifted = max(x_shifted, tgt_r - offset_from_tip)
                    return (x_shifted, y)
                return adjust_point

            adjust_point = make_adjust_point(
                dx,
                connects_left,
                connects_right,
                tail_x_min,
                tail_x_max,
                target_right_x,
                tail_threshold,
                y_min_band,
                y_max_band,
            )

            # Pass 2: Draw adjusted outline into T2CharStringPen and BoundsPen
            cff_pen_width = None if new_width == default_w else (new_width - nominal_w)
            t2_pen = T2CharStringPen(width=cff_pen_width, glyphSet=ar_glyphset)
            bounds_pen = BoundsPen(glyphSet=ar_glyphset)

            for out_pen in (t2_pen, bounds_pen):
                for op, pts in rec_pen.ops:
                    if op == "moveTo":
                        out_pen.moveTo(adjust_point(pts[0]))
                    elif op == "lineTo":
                        out_pen.lineTo(adjust_point(pts[0]))
                    elif op == "curveTo":
                        out_pen.curveTo(
                            adjust_point(pts[0]),
                            adjust_point(pts[1]),
                            adjust_point(pts[2]),
                        )
                    elif op == "closePath":
                        out_pen.closePath()
                    elif op == "endPath":
                        out_pen.endPath()

            char_string = t2_pen.getCharString(
                private=private_dict,
                globalSubrs=cff_table.GlobalSubrs,
                optimize=True,
            )

            idx = len(char_strings.charStringsIndex)
            char_strings.charStringsIndex.append(char_string)
            char_strings.charStrings[gname] = idx
            glyph_order.append(gname)
            top_dict.charset.append(gname)

            # Left Side Bearing strictly 0 for left-connecting glyphs, never negative
            if connects_left:
                new_lsb = 0
            else:
                new_lsb = max(0, otRound(bounds_pen.bounds[0])) if bounds_pen.bounds else 0

            # 3. Sync Both CFF Width and hmtx Width
            target_font["hmtx"].metrics[gname] = (new_width, new_lsb)
            added += 1

        target_font.setGlyphOrder(glyph_order)
        target_font["maxp"].numGlyphs = len(glyph_order)

        for cp, gname in needed_codepoints.items():
            if gname in char_strings.charStrings:
                for t in unicode_tables:
                    t.cmap[cp] = gname

        target_font.save(out_path)
        cff_size = len(target_font.getTableData("CFF "))
        file_size = os.path.getsize(out_path)
        print(f"Saved {os.path.basename(out_path)}: +{added} glyphs ({len(glyph_order)} total). CFF: {cff_size:,} B (File: {file_size:,} B)")

    # Clean injection with Right-Only Overhang (no canaries, normal scale)
    inject(
        os.path.join(base_dir, "orig_fonts", "DINPro-Regular.otf"),
        os.path.join(base_dir, "NotoSansArabic-Regular.ttf"),
        os.path.join(out_dir, "DINPro-Regular.otf"),
        right_overhang=100,
        tail_threshold=35,
        canary_scale=None,
    )
    inject(
        os.path.join(base_dir, "orig_fonts", "DINPro-Medium.otf"),
        os.path.join(base_dir, "NotoSansArabic-Medium.ttf"),
        os.path.join(out_dir, "DINPro-Medium.otf"),
        right_overhang=100,
        tail_threshold=35,
        canary_scale=None,
    )

if __name__ == "__main__":
    build_clean_compact_fonts()
