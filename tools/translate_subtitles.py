import os
import sys
import json
import time
import re
import threading
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from text_packer import parse_text_file
from bidi_engine import reshape_text

_thread_local = threading.local()

def get_session():
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        _thread_local.session = s
    return _thread_local.session

def translate_fast(text: str, sl: str = 'en') -> str:
    cleaned = text.strip()
    if not cleaned:
        return ''
    # Protect line breaks and tags
    tokens = []
    def repl_token(m):
        tokens.append(m.group(0))
        return f"__TOK{len(tokens)-1}__"

    token_pat = re.compile(r'(<br>|<break/>|\r?\n|\\\\|\|[^|]+\||\[[A-Za-z0-9_]+\])')
    protected = token_pat.sub(repl_token, cleaned)

    session = get_session()
    url = 'https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=' + sl + '&tl=ar&q=' + urllib.parse.quote(protected)
    try:
        r = session.get(url, timeout=8)
        res = r.json()
        if isinstance(res, list) and res:
            translated = res[0]
            for i, tok in enumerate(tokens):
                t1 = f"__TOK{i}__"
                t2 = f"__{i}KOT__"
                if t1 in translated:
                    translated = translated.replace(t1, tok)
                elif t2 in translated:
                    translated = translated.replace(t2, tok)
                else:
                    translated = re.sub(r'__\s*TOK' + str(i) + r'\s*__', tok, translated)
                    translated = re.sub(r'__\s*' + str(i) + r'\s*KOT__', tok, translated)
            return translated.strip()
    except Exception:
        pass
    return text

def build_subtitles_translations(eng_sub_path: str, cache_path: str):
    sub_entries = parse_text_file(eng_sub_path)
    print(f"Total subtitle entries in file: {len(sub_entries)}", flush=True)

    # Collect unique non-empty strings
    unique_texts = set(text.strip() for sid, text in sub_entries if text.strip())
    print(f"Total unique subtitle lines: {len(unique_texts)}", flush=True)

    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} existing cached subtitle translations.", flush=True)
        except Exception:
            cache = {}

    to_translate = [t for t in unique_texts if t not in cache or not cache[t].get('ar')]
    print(f"Subtitle lines needing translation: {len(to_translate)} / {len(unique_texts)}", flush=True)

    if to_translate:
        with ThreadPoolExecutor(max_workers=35) as executor:
            future_to_text = {
                executor.submit(translate_fast, text): text
                for text in to_translate
            }
            done_count = 0
            for future in as_completed(future_to_text):
                t_en = future_to_text[future]
                try:
                    ar_trans = future.result()
                    if not ar_trans:
                        ar_trans = t_en
                    reshaped_ar = reshape_text(ar_trans)
                    cache[t_en] = {
                        'ar': ar_trans,
                        'ar_reshaped': reshaped_ar
                    }
                except Exception as e:
                    print(f"Failed translation for '{t_en[:30]}': {e}", flush=True)
                done_count += 1
                if done_count % 500 == 0 or done_count == len(to_translate):
                    print(f"Translated {done_count} / {len(to_translate)} subtitles...", flush=True)
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(cache, f, ensure_ascii=False, indent=2)

        print(f"Saved all {len(cache)} subtitle translations to {cache_path}", flush=True)

    return cache

if __name__ == '__main__':
    eng_sub = r'c:\Users\SlouMa\Desktop\tlou1\extracted\text2\eng.subtitles'
    cache_file = r'c:\Users\SlouMa\Desktop\tlou1\extracted\arabic_subtitles.json'
    build_subtitles_translations(eng_sub, cache_file)
