#!/bin/bash
set -e

echo "========================================="
echo "  PDF to Handwriting Converter - Build"
echo "========================================="

echo ">>> Python version:"
python --version

echo ">>> Installing system dependencies..."
# Install tesseract and other deps (may need sudo on some platforms)
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libffi-dev \
    wget \
    curl \
    2>/dev/null || echo "Note: apt-get may have limited permissions, continuing..."

echo ">>> Upgrading pip..."
pip install --upgrade pip wheel setuptools

echo ">>> Installing Python packages..."
pip install -r requirements.txt

echo ">>> Verifying critical imports..."
python -c "
import sys
print(f'Python: {sys.version}')

# Test PyMuPDF
try:
    import fitz
    print(f'✅ PyMuPDF: {fitz.version}')
except Exception as e:
    print(f'⚠️  PyMuPDF: {e}')

# Test Pillow
try:
    from PIL import Image
    print(f'✅ Pillow: OK')
except Exception as e:
    print(f'⚠️  Pillow: {e}')

# Test ReportLab
try:
    import reportlab
    print(f'✅ ReportLab: {reportlab.Version}')
except Exception as e:
    print(f'⚠️  ReportLab: {e}')

# Test pytesseract
try:
    import pytesseract
    print(f'✅ pytesseract: OK')
except Exception as e:
    print(f'⚠️  pytesseract: {e}')

print('Import check complete.')
"

echo ">>> Downloading handwriting fonts..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from utils.font_manager import FontManager
    from pathlib import Path
    fm = FontManager(Path('static/fonts'))
    count = fm.ensure_fonts_downloaded()
    print(f'✅ Fonts ready: {count} available')
except Exception as e:
    print(f'⚠️  Font download warning: {e}')
    print('Fonts will be downloaded on first request.')
"

echo ">>> Creating required directories..."
mkdir -p static/fonts
mkdir -p static/css
mkdir -p static/js
mkdir -p templates
mkdir -p utils

echo "========================================="
echo "  Build Complete! ✅"
echo "========================================="
