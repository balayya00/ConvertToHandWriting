#!/bin/bash
# Install system dependencies
apt-get update
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    --no-install-recommends

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Download fonts
python -c "
from utils.font_manager import FontManager
from pathlib import Path
fm = FontManager(Path('static/fonts'))
count = fm.ensure_fonts_downloaded()
print(f'Downloaded {count} fonts')
"

echo "Build complete!"
