import logging
import re
from pathlib import Path
from typing import Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)

class OCRExtractor:
    """Extract text from images using OCR"""
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract text from image file"""
        try:
            # Try pytesseract first
            return self._extract_with_tesseract(file_path)
        except Exception as e:
            logger.warning(f"Tesseract OCR failed: {e}")
            return {
                'full_text': f'[OCR extraction failed. Please install Tesseract OCR or use direct text input.]\n\nError: {str(e)}',
                'pages': [f'OCR Error: {str(e)}'],
                'page_count': 1,
                'layout_data': None
            }
    
    def _extract_with_tesseract(self, file_path: str) -> Dict[str, Any]:
        """Use pytesseract for OCR"""
        import pytesseract
        
        # Set tesseract path for different OS
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]
        
        import shutil
        if shutil.which('tesseract'):
            pass  # Use from PATH
        else:
            for path in tesseract_paths:
                import os
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        # Open and preprocess image
        img = Image.open(file_path)
        
        # Convert to RGB if needed
        if img.mode not in ['RGB', 'L']:
            img = img.convert('RGB')
        
        # Upscale small images for better OCR
        width, height = img.size
        if width < 1000:
            scale = 1000 / width
            img = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
        
        # Run OCR
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, config=config)
        
        # Clean up text
        text = self._clean_text(text)
        
        return {
            'full_text': text,
            'pages': [text],
            'page_count': 1,
            'layout_data': None
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.rstrip()
            cleaned_lines.append(line)
        
        # Remove excessive blank lines (max 2 consecutive)
        result = []
        blank_count = 0
        for line in cleaned_lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        
        return '\n'.join(result).strip()
