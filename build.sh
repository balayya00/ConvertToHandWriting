#!/bin/bash
set -e
echo "========================================="
echo "  PDF to Handwriting – Build v6.0"
echo "========================================="

python --version

echo ">>> System packages..."
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq \
    tesseract-ocr tesseract-ocr-eng \
    libgl1-mesa-glx libglib2.0-0 libgomp1 \
    2>/dev/null || echo "(apt limited)"

echo ">>> Python packages..."
pip install --upgrade pip wheel setuptools -q
pip install -r requirements.txt -q

echo ">>> Checking imports..."
python -c "
import fitz, PIL, reportlab, flask, requests
print('✅ All imports OK')
print(f'   PyMuPDF: {fitz.version}')
"

echo ">>> Pre-downloading fonts via GitHub raw..."
python - << 'PYEOF'
import time
import requests
from pathlib import Path

FONTS_DIR = Path("static/fonts")
FONTS_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://raw.githubusercontent.com/google/fonts/main"

# All fonts from font_manager.py FONTS dict
DOWNLOAD_LIST = [
    ("Kalam-Regular.ttf",           "ofl/kalam/Kalam-Regular.ttf"),
    ("Caveat-Regular.ttf",          "ofl/caveat/static/Caveat-Regular.ttf"),
    ("IndieFlower.ttf",             "ofl/indieflower/IndieFlower.ttf"),
    ("GloriaHallelujah.ttf",        "ofl/gloriahallelujah/GloriaHallelujah.ttf"),
    ("ShadowsIntoLight.ttf",        "ofl/shadowsintolight/ShadowsIntoLight.ttf"),
    ("NothingYouCouldDo.ttf",       "ofl/nothingyoucoulddo/NothingYouCouldDo.ttf"),
    ("CoveredByYourGrace.ttf",      "ofl/coveredbyyourgrace/CoveredByYourGrace.ttf"),
    ("GochiHand-Regular.ttf",       "ofl/gochihand/GochiHand-Regular.ttf"),
    ("Handlee-Regular.ttf",         "ofl/handlee/Handlee-Regular.ttf"),
    ("PatrickHand-Regular.ttf",     "ofl/patrickhand/PatrickHand-Regular.ttf"),
    ("ArchitectsDaughter.ttf",      "ofl/architectsdaughter/ArchitectsDaughter.ttf"),
    ("AmaticSC-Regular.ttf",        "ofl/amaticsc/AmaticSC-Regular.ttf"),
    ("ReenieBeanie-Regular.ttf",    "ofl/reeniebeanie/ReenieBeanie-Regular.ttf"),
    ("DancingScript-Regular.ttf",   "ofl/dancingscript/static/DancingScript-Regular.ttf"),
    ("Satisfy-Regular.ttf",         "ofl/satisfy/Satisfy-Regular.ttf"),
    ("Yellowtail-Regular.ttf",      "apache/yellowtail/Yellowtail-Regular.ttf"),
    ("Damion-Regular.ttf",          "ofl/damion/Damion-Regular.ttf"),
    ("Norican-Regular.ttf",         "ofl/norican/Norican-Regular.ttf"),
    ("MarckScript-Regular.ttf",     "ofl/marckscript/MarckScript-Regular.ttf"),
    ("HomemadeApple-Regular.ttf",   "apache/homemadeapple/HomemadeApple-Regular.ttf"),
    ("GreatVibes-Regular.ttf",      "ofl/greatvibes/GreatVibes-Regular.ttf"),
    ("Allura-Regular.ttf",          "ofl/allura/Allura-Regular.ttf"),
    ("Sacramento-Regular.ttf",      "ofl/sacramento/Sacramento-Regular.ttf"),
    ("Parisienne-Regular.ttf",      "ofl/parisienne/Parisienne-Regular.ttf"),
    ("PinyonScript-Regular.ttf",    "ofl/pinyonscript/PinyonScript-Regular.ttf"),
    ("Tangerine-Regular.ttf",       "ofl/tangerine/Tangerine-Regular.ttf"),
    ("AlexBrush-Regular.ttf",       "ofl/alexbrush/AlexBrush-Regular.ttf"),
    ("Engagement-Regular.ttf",      "ofl/engagement/Engagement-Regular.ttf"),
    ("EuphoriaScript-Regular.ttf",  "ofl/euphoriascript/EuphoriaScript-Regular.ttf"),
    ("PermanentMarker-Regular.ttf", "apache/permanentmarker/PermanentMarker-Regular.ttf"),
    ("RockSalt-Regular.ttf",        "apache/rocksalt/RockSalt-Regular.ttf"),
    ("Pacifico-Regular.ttf",        "ofl/pacifico/Pacifico-Regular.ttf"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
}

ok = 0
fail = 0
for fname, path in DOWNLOAD_LIST:
    dest = FONTS_DIR / fname
    if dest.exists() and dest.stat().st_size > 4096:
        print(f"  ✅ {fname} (cached)")
        ok += 1
        continue
    url = f"{BASE}/{path}"
    try:
        r = requests.get(url, headers=headers, timeout=25)
        if r.status_code == 200 and len(r.content) > 4096:
            dest.write_bytes(r.content)
            print(f"  ✅ {fname} ({len(r.content)//1024} KB)")
            ok += 1
        else:
            print(f"  ❌ {fname}: HTTP {r.status_code}")
            fail += 1
    except Exception as e:
        print(f"  ❌ {fname}: {e}")
        fail += 1
    time.sleep(0.1)

print(f"\nFonts: {ok} OK, {fail} failed out of {len(DOWNLOAD_LIST)}")
if ok == 0:
    print("WARNING: No fonts downloaded!")
    import sys; sys.exit(1)
PYEOF

echo "========================================="
echo "  Build Complete ✅"
echo "  Fonts in static/fonts/:"
ls -la static/fonts/ | tail -20
echo "========================================="
