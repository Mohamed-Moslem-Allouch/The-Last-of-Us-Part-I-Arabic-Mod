import sys
sys.stdout.reconfigure(encoding='utf-8')
import arabic_reshaper
from bidi.algorithm import get_display

arabic_text = "يا أبي، ما بك؟"
reshaped = arabic_reshaper.reshape(arabic_text)
visual_ar = get_display(reshaped)

speaker = "SARAH"

# Option 1: Dialogue first, then ' :' + speaker
opt1 = f"{visual_ar} :{speaker}"

# Option 2: Dialogue first, then ' ' + speaker + ':'
opt2 = f"{visual_ar} {speaker}:"

print("--- Option 1 (Colon between dialogue and name) ---")
print(opt1)

print("\n--- Option 2 (Colon on the right of name) ---")
print(opt2)
