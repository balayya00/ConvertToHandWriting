"""
OCR extractor for JPG / PNG images using Tesseract via pytesseract.
Falls back gracefully if Tesseract is not installed.
"""
import logging
import re
import shutil
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Common Tesseract locations
_TESSERACT_PATHS = [
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


class OCRExtractor:
    """Extract text from raster images via Tesseract OCR."""

    def extract(self, file_path: str) -> Dict[str, Any]:
        try:
            return self._tesseract(file_path)
        except RuntimeError:
            raise
        except Exception as exc:
            logger.warning(f"OCR failed ({exc}); returning placeholder.")
            msg = (
                f"[OCR could not extract text from this image.]\n\n"
                f"Reason: {exc}\n\n"
                "Tip: Make sure Tesseract is installed on the server,\n"
                "or paste your text directly in the 'Direct Text' tab."
            )
            return {
                "full_text":   msg,
                "pages":       [msg],
                "page_count":  1,
                "layout_data": None,
            }

    # ── Private ──────────────────────────────────────────────────────────

    def _tesseract(self, file_path: str) -> Dict[str, Any]:
        import pytesseract
        from PIL import Image

        # Locate tesseract binary
        if shutil.which("tesseract"):
            pass  # already on PATH
        else:
            for p in _TESSERACT_PATHS:
                if Path(p).exists():
                    pytesseract.pytesseract.tesseract_cmd = p
                    break
            else:
                raise RuntimeError(
                    "Tesseract OCR binary not found. "
                    "Install with: apt-get install tesseract-ocr"
                )

        img = Image.open(file_path)

        # Normalise colour mode
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Upscale tiny images for better accuracy
        w, h = img.size
        if w < 1200:
            scale = 1200 / w
            img   = img.resize(
                (int(w * scale), int(h * scale)),
                Image.LANCZOS
            )

        # Run OCR (OEM 3 = best LSTM engine, PSM 6 = uniform text block)
        config = "--oem 3 --psm 6"
        text   = pytesseract.image_to_string(img, config=config)
        text   = self._clean(text)

        return {
            "full_text":   text,
            "pages":       [text],
            "page_count":  1,
            "layout_data": None,
        }

    @staticmethod
    def _clean(text: str) -> str:
        lines   = text.split("\n")
        result  = []
        blanks  = 0

        for line in lines:
            line = line.rstrip()
            if line == "":
                blanks += 1
                if blanks <= 2:
                    result.append(line)
            else:
                blanks = 0
                result.append(line)

        return "\n".join(result).strip()
