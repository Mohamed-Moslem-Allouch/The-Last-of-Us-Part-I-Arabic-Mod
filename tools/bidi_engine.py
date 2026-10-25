import re
import arabic_reshaper
from bidi.algorithm import get_display

# Custom configuration for arabic_reshaper to support all presentation forms
_RESHAPER_CONFIG = {
    'delete_harakat': False,
    'support_ligatures': True,
    'RIAL': True,
    'shift_harakat_position': False
}

_reshaper = arabic_reshaper.ArabicReshaper(configuration=_RESHAPER_CONFIG)

def has_arabic(text: str) -> bool:
    return any('\u0600' <= c <= '\u06ff' or '\ufe70' <= c <= '\ufefc' for c in text)

def reshape_line(line: str) -> str:
    if not has_arabic(line):
        return line

    # Protect in-game tokens and XML tags
    # Examples: |gen:crouch|, |icon:...|, {0}, <break/>, <br>
    tokens = []
    def repl(m):
        tokens.append(m.group(0))
        return f"__TOK{len(tokens)-1}__"

    token_pattern = re.compile(r'(\|[^|]+\||<[^>]+>|\{[0-9]+\}|\[[A-Za-z0-9_]+\])')
    protected = token_pattern.sub(repl, line)

    # Reshape Arabic characters to presentation forms
    reshaped = _reshaper.reshape(protected)

    # Apply Unicode bidirectional algorithm
    bidi_str = get_display(reshaped)

    # Restore tokens (accounting for possible bidi inverted characters in placeholder)
    for i, tok in enumerate(tokens):
        # Normal placeholder
        p1 = f"__TOK{i}__"
        p2 = f"__{i}KOT__"
        if p1 in bidi_str:
            bidi_str = bidi_str.replace(p1, tok)
        elif p2 in bidi_str:
            bidi_str = bidi_str.replace(p2, tok)
        else:
            # Fallback regex search
            bidi_str = re.sub(r'__\s*TOK' + str(i) + r'\s*__', tok, bidi_str)
            bidi_str = re.sub(r'__\s*' + str(i) + r'\s*KOT__', tok, bidi_str)

    return bidi_str

def reshape_text(text: str) -> str:
    """
    Reshapes Arabic text, preserving newlines, <br>, and \\ linebreaks.
    """
    if not text or not has_arabic(text):
        return text

    # Split by common newline delimiters
    segments = re.split(r'(<br>|<break/>|\r?\n|\\\\)', text)
    result = []
    for seg in segments:
        if seg in ('<br>', '<break/>', '\n', '\r\n', '\\\\'):
            result.append(seg)
        else:
            result.append(reshape_line(seg))

    return ''.join(result)

def wrap_and_reshape_doc(text: str, max_chars: int = 46) -> str:
    """
    Wraps long document paragraphs into lines of max_chars at word boundaries,
    and applies BiDi reshaping per-line, preserving <br> breaks so that the LTR
    game engine displays the document naturally from top to bottom.
    """
    if not text or not has_arabic(text):
        return text

    import textwrap
    segments = re.split(r'(<br\s*/?>|<break/>|\r?\n|\\\\)', text)
    result = []
    for seg in segments:
        if re.match(r'(<br\s*/?>|<break/>|\r?\n|\\\\)', seg):
            result.append('<br>')
        else:
            seg = seg.strip()
            if not seg:
                continue
            lines = textwrap.wrap(seg, width=max_chars)
            for i, line in enumerate(lines):
                result.append(reshape_line(line))
                if i < len(lines) - 1:
                    result.append('<br>')

    return ''.join(result)
