#!/bin/bash
set -e
echo "=== Build Start ==="
python --version

echo ">>> Installing system packages..."
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq \
    tesseract-ocr tesseract-ocr-eng \
    libgl1-mesa-glx libglib2.0-0 \
    2>/dev/null || echo "(apt skipped)"

echo ">>> Installing Python packages..."
pip install --upgrade pip wheel setuptools --quiet
pip install -r requirements.txt --quiet

echo ">>> Verifying imports..."
python - <<'EOF'
import sys
tests = [
    ("fitz",         "PyMuPDF"),
    ("PIL",          "Pillow"),
    ("reportlab",    "ReportLab"),
    ("pytesseract",  "pytesseract"),
    ("flask",        "Flask"),
    ("requests",     "requests"),
]
ok = True
for mod, name in tests:
    try:
        __import__(mod)
        print(f"  ✅ {name}")
    except ImportError as e:
        print(f"  ❌ {name}: {e}")
        ok = False
sys.exit(0 if ok else 1)
EOF

echo ">>> Pre-downloading priority fonts (fast ones only, background gets the rest)..."
python - <<'EOF'
import sys, time, requests
from pathlib import Path

FONTS_DIR = Path("static/fonts")
FONTS_DIR.mkdir(parents=True, exist_ok=True)

# Only download the 5 most-used fonts synchronously during build
PRIORITY = {
    "Kalam-Regular.ttf":
        "https://fonts.gstatic.com/s/kalam/v16/YA9dr0Wd4kDdMuhWMibDszkB.ttf",
    "Caveat-Regular.ttf":
        "https://fonts.gstatic.com/s/caveat/v18/WnznHAc5bAfYB2QRah7pcpNvOx-pjcJ9SIKjYBxPigs.ttf",
    "PatrickHand-Regular.ttf":
        "https://fonts.gstatic.com/s/patrickhand/v20/LDI1apSQOAYtSuYWp8ZweqbHoxIB.ttf",
    "DancingScript-Regular.ttf":
        "https://fonts.gstatic.com/s/dancingscript/v25/If2cXTr6YS-zF4S-kcSWSVi_sxjsohD9F50Ruu7BMSo3ROp6.ttf",
    "Pacifico-Regular.ttf":
        "https://fonts.gstatic.com/s/pacifico/v22/FwZY7-Qmy14u9lezJ96A4sijpFu_.ttf",
    "GloriaHallelujah.ttf":
        "https://fonts.gstatic.com/s/gloriahallelujah/v17/LYjYdHv3kUk9BMV96EIswT9DIbW-MLSy3TKEvkCF.ttf",
    "Sacramento-Regular.ttf":
        "https://fonts.gstatic.com/s/sacramento/v15/buEzpo6gcdjy0EiZMBUG4C0f-w.ttf",
    "GreatVibes-Regular.ttf":
        "https://fonts.gstatic.com/s/greatvibes/v19/RWmMoKWR9v4ksMfaWd_JN9XFiaQ.ttf",
}

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Referer": "https://fonts.google.com/",
}

ok = 0
for fname, url in PRIORITY.items():
    dest = FONTS_DIR / fname
    if dest.exists():
        print(f"  ✅ {fname} (cached)")
        ok += 1
        continue
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 4096:
            dest.write_bytes(r.content)
            print(f"  ✅ {fname} ({len(r.content)//1024} KB)")
            ok += 1
        else:
            print(f"  ⚠  {fname}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  ⚠  {fname}: {e}")
    time.sleep(0.2)

print(f"Priority fonts ready: {ok}/{len(PRIORITY)}")
EOF

echo "=== Build Complete ==="
