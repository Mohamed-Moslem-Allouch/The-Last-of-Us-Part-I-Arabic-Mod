import os
import sys
import json
import time
import re
import threading
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    # Protect line breaks and tags so we can translate in a single request
    # Tokens to protect: <br>, <break/>, \n, \\, |...|
    tokens = []
    def repl_token(m):
        tokens.append(m.group(0))
        return f"__TOK{len(tokens)-1}__"

    token_pat = re.compile(r'(<br>|<break/>|\r?\n|\\\\|\|[^|]+\||\[[A-Za-z0-9_]+\])')
    protected = token_pat.sub(repl_token, cleaned)

    session = get_session()
    url = 'https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=' + sl + '&tl=ar&q=' + urllib.parse.quote(protected)
    try:
        r = session.get(url, timeout=10)
        res = r.json()
        if isinstance(res, list) and res:
            translated = res[0]
            # Restore tokens
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
    return text # fallback

def build_notes_translations(notes_en_path: str, cache_path: str):
    with open(notes_en_path, 'r', encoding='utf-8') as f:
        notes_en = json.load(f)

    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} existing cached note translations.", flush=True)
        except Exception:
            cache = {}

    to_translate = {k: v for k, v in notes_en.items() if k not in cache or not cache[k].get('ar')}
    print(f"Notes needing translation: {len(to_translate)} / {len(notes_en)}", flush=True)

    if to_translate:
        with ThreadPoolExecutor(max_workers=30) as executor:
            future_to_key = {
                executor.submit(translate_fast, v['en']): k
                for k, v in to_translate.items()
            }
            done_count = 0
            for future in as_completed(future_to_key):
                k = future_to_key[future]
                en_obj = to_translate[k]
                try:
                    ar_trans = future.result()
                    if not ar_trans:
                        ar_trans = en_obj['en']
                    reshaped_ar = reshape_text(ar_trans)
                    cache[k] = {
                        'name': en_obj['name'],
                        'en': en_obj['en'],
                        'ar': ar_trans,
                        'ar_reshaped': reshaped_ar
                    }
                except Exception as e:
                    print(f"Failed key {k}: {e}", flush=True)
                done_count += 1
                if done_count % 50 == 0 or done_count == len(to_translate):
                    print(f"Translated {done_count} / {len(to_translate)} notes...", flush=True)
                    # Periodic save
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(cache, f, ensure_ascii=False, indent=2)

        print(f"Saved all {len(cache)} note translations to {cache_path}", flush=True)

    return cache

if __name__ == '__main__':
    en_file = r'c:\Users\SlouMa\Desktop\tlou1\extracted\reader_notes_en.json'
    cache_file = r'c:\Users\SlouMa\Desktop\tlou1\extracted\arabic_notes.json'
    build_notes_translations(en_file, cache_file)
