"""
Handwriting Generator
Renders text as realistic handwritten images using PIL/Pillow,
then assembles them into PDF via PyMuPDF.
"""
import io
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger(__name__)

# ─── Colour palettes ────────────────────────────────────────────────────────
INK = {
    "blue":      (10,  10,  200),
    "dark_blue": (0,   0,   139),
    "black":     (15,  15,  15),
    "pencil":    (80,  80,  80),
    "red":       (180, 10,  10),
    "green":     (0,   120, 30),
}

PAPER_BG = {
    "plain":  (255, 255, 255),
    "ruled":  (255, 255, 252),
    "cream":  (255, 253, 240),
    "exam":   (250, 250, 248),
    "graph":  (252, 252, 255),
    "yellow": (255, 255, 215),
}


# ─── Main Generator ─────────────────────────────────────────────────────────
class HandwritingGenerator:

    def __init__(self, fonts_dir: Path, output_dir: Path):
        self.fonts_dir  = Path(fonts_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public ───────────────────────────────────────────────────────────

    def generate_jpg(self, pages: List[str],
                     settings: Dict, sid: str) -> List[str]:
        """Render every page as a JPG; return list of saved paths."""
        paths: List[str] = []
        pg_idx = 0

        for text in pages:
            if not text.strip():
                continue
            for img in self._render_text(text, settings):
                dst = self.output_dir / f"{sid}_page_{pg_idx}.jpg"
                img.save(str(dst), "JPEG", quality=95, dpi=(150, 150))
                paths.append(str(dst))
                pg_idx += 1

        return paths

    def generate_pdf(self, pages: List[str],
                     settings: Dict, sid: str) -> str:
        """Render pages and combine into a single PDF."""
        images: List[Image.Image] = []
        for text in pages:
            if not text.strip():
                continue
            images.extend(self._render_text(text, settings))

        if not images:
            images = self._render_text("(empty)", settings)

        dst = self.output_dir / f"{sid}.pdf"
        self._images_to_pdf(images, str(dst))
        return str(dst)

    # ── Rendering ────────────────────────────────────────────────────────

    def _render_text(self, text: str,
                     settings: Dict) -> List[Image.Image]:
        """
        Wrap text and render one-or-more page images.
        Automatic page-breaks are inserted when text overflows.
        """
        W            = settings.get("page_width",   794)
        H            = settings.get("page_height", 1123)
        font_size    = settings.get("font_size",     28)
        spacing      = settings.get("line_spacing",  1.8)
        ink_name     = settings.get("ink_color",   "blue")
        margin       = settings.get("margin",        60)
        paper_style  = settings.get("paper_style", "ruled")
        font_name    = settings.get("font_name",   "Kalam")

        ink        = INK.get(ink_name, INK["blue"])
        font       = self._load_font(font_name, font_size)
        line_h     = int(font_size * spacing)
        text_w     = W - 2 * margin - 30   # 30 px for margin line
        text_top   = margin + 10
        text_left  = margin + 35

        # Wrap all paragraphs → flat list of visual lines
        all_lines: List[str] = []
        for para in text.split("\n"):
            if para.strip() == "":
                all_lines.append("")
            else:
                all_lines.extend(self._wrap(para, font, text_w))

        # Split into pages
        lines_per_page = max(1, (H - text_top - margin) // line_h)
        page_chunks    = [all_lines[i: i + lines_per_page]
                          for i in range(0, max(1, len(all_lines)),
                                         lines_per_page)]

        rendered: List[Image.Image] = []
        for chunk in page_chunks:
            img  = self._make_paper(W, H, paper_style, settings)
            draw = ImageDraw.Draw(img)
            y    = text_top

            for line in chunk:
                if y + line_h > H - margin:
                    break
                if line.strip():
                    self._draw_line(draw, line, text_left, y, font, ink)
                y += line_h

            img = img.filter(ImageFilter.GaussianBlur(radius=0.25))
            rendered.append(img)

        return rendered or [self._make_paper(W, H, paper_style, settings)]

    # ── Paper background ─────────────────────────────────────────────────

    def _make_paper(self, W: int, H: int,
                    style: str, settings: Dict) -> Image.Image:
        bg   = PAPER_BG.get(style, PAPER_BG["ruled"])
        img  = Image.new("RGB", (W, H), bg)
        draw = ImageDraw.Draw(img)
        m    = settings.get("margin", 60)
        fs   = settings.get("font_size", 28)
        sp   = settings.get("line_spacing", 1.8)
        lh   = int(fs * sp)

        if style == "ruled":
            # Horizontal guide lines
            y = m + lh
            while y < H - m:
                draw.line([(m, y), (W - m, y)],
                           fill=(173, 216, 230), width=1)
                y += lh
            # Red margin line
            draw.line([(m + 30, 0), (m + 30, H)],
                       fill=(255, 150, 150), width=2)
            # Top margin
            draw.line([(0, m - 5), (W, m - 5)],
                       fill=(255, 160, 160), width=1)

        elif style == "exam":
            # Outer border
            bm = 30
            draw.rectangle([bm, bm, W - bm, H - bm],
                             outline=(0, 0, 120), width=2)
            # Header box
            draw.rectangle([bm, bm, W - bm, m],
                             outline=(0, 0, 120), width=1)
            # Guide lines
            y = m + lh
            while y < H - m:
                draw.line([(m, y), (W - m, y)],
                           fill=(100, 100, 200), width=1)
                y += lh
            # Left column margin
            draw.line([(m + 20, m), (m + 20, H - bm)],
                       fill=(100, 100, 200), width=1)

        elif style == "graph":
            # Minor grid
            gs = 20
            for x in range(0, W, gs):
                draw.line([(x, 0), (x, H)], fill=(200, 220, 255), width=1)
            for y in range(0, H, gs):
                draw.line([(0, y), (W, y)], fill=(200, 220, 255), width=1)
            # Major grid
            for x in range(0, W, gs * 5):
                draw.line([(x, 0), (x, H)], fill=(160, 190, 240), width=1)
            for y in range(0, H, gs * 5):
                draw.line([(0, y), (W, y)], fill=(160, 190, 240), width=1)

        # Add subtle paper texture
        self._texture(img)
        return img

    @staticmethod
    def _texture(img: Image.Image) -> None:
        """Apply very faint grain so the paper looks real."""
        try:
            import numpy as np
            arr  = np.array(img, dtype=np.int16)
            noise = np.random.randint(-3, 4, arr.shape, dtype=np.int16)
            arr   = np.clip(arr + noise, 0, 255).astype(np.uint8)
            img.paste(Image.fromarray(arr))
        except ImportError:
            pass

    # ── Text drawing ─────────────────────────────────────────────────────

    def _draw_line(self, draw: ImageDraw.Draw,
                   text: str, x: int, y: float,
                   font: ImageFont.FreeTypeFont,
                   ink: Tuple[int, int, int]) -> None:
        """
        Draw a single text line with per-character micro-jitter to
        simulate natural handwriting variation.
        """
        cx = float(x)
        for ch in text:
            # Vertical jitter ±1 px
            cy = y + random.uniform(-1.0, 1.0)
            # Colour micro-variation ±6
            v  = random.randint(-6, 6)
            col = tuple(max(0, min(255, c + v)) for c in ink)
            draw.text((cx, cy), ch, font=font, fill=col)
            cx += self._char_width(ch, font)

    @staticmethod
    def _char_width(ch: str,
                    font: ImageFont.FreeTypeFont) -> float:
        try:
            bb = font.getbbox(ch)
            return float(bb[2] - bb[0])
        except Exception:
            try:
                return float(font.getlength(ch))
            except Exception:
                return float(font.size) * 0.6

    # ── Text wrapping ─────────────────────────────────────────────────────

    def _wrap(self, text: str,
              font: ImageFont.FreeTypeFont,
              max_w: int) -> List[str]:
        words   = text.split(" ")
        lines   = []
        current = []
        cur_w   = 0.0

        for word in words:
            ww = self._char_width(word + " ", font)
            if cur_w + ww <= max_w:
                current.append(word)
                cur_w += ww
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
                cur_w   = ww

        if current:
            lines.append(" ".join(current))

        return lines or [""]

    # ── Font loading ─────────────────────────────────────────────────────

    def _load_font(self, font_name: str,
                   size: int) -> ImageFont.FreeTypeFont:
        from utils.font_manager import FontManager
        fm   = FontManager(self.fonts_dir)
        path = fm.get_font_path(font_name)

        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception as e:
                logger.warning(f"truetype load failed ({e}); using default")

        return ImageFont.load_default()

    # ── PDF assembly ─────────────────────────────────────────────────────

    def _images_to_pdf(self, images: List[Image.Image],
                       dst: str) -> None:
        """Embed rendered page images into a PDF via PyMuPDF."""
        try:
            import fitz
            doc = fitz.open()

            for img in images:
                buf = io.BytesIO()
                img.save(buf, "PNG")
                buf.seek(0)

                W, H = img.size
                dpi  = 96
                pw   = (W / dpi) * 72   # pixels → points
                ph   = (H / dpi) * 72

                page = doc.new_page(width=pw, height=ph)
                page.insert_image(
                    fitz.Rect(0, 0, pw, ph),
                    stream=buf.read()
                )

            doc.save(dst, deflate=True, garbage=4)
            doc.close()

        except Exception as exc:
            logger.warning(f"PyMuPDF PDF assembly failed ({exc}); "
                            "falling back to ReportLab.")
            self._images_to_pdf_reportlab(images, dst)

    def _images_to_pdf_reportlab(self, images: List[Image.Image],
                                   dst: str) -> None:
        """Fallback PDF creation using ReportLab."""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.platypus import Image as RLImage

        pw, ph = A4
        doc    = SimpleDocTemplate(
            dst, pagesize=A4,
            topMargin=0, bottomMargin=0,
            leftMargin=0, rightMargin=0,
        )
        story  = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, "PNG")
            buf.seek(0)
            story.append(RLImage(buf, width=pw, height=ph))

        doc.build(story)


# ─── Position-Aware Generator ────────────────────────────────────────────────
class PositionAwareGenerator(HandwritingGenerator):
    """
    Renders handwriting at the exact (x, y) positions extracted
    from the original PDF layout, so the output matches the source
    document's spatial arrangement.
    """

    def render_with_layout(self,
                           layout_data: List[Dict],
                           settings: Dict,
                           sid: str) -> str:
        images: List[Image.Image] = []

        for page_layout in layout_data:
            orig_w = float(page_layout.get("width",  595))
            orig_h = float(page_layout.get("height", 842))
            tgt_w  = int(settings.get("page_width",  794))
            tgt_h  = int(settings.get("page_height", 1123))

            sx = tgt_w / orig_w
            sy = tgt_h / orig_h

            img  = self._make_paper(tgt_w, tgt_h,
                                    settings.get("paper_style", "ruled"),
                                    settings)
            draw = ImageDraw.Draw(img)

            ink       = INK.get(settings.get("ink_color", "blue"), INK["blue"])
            font_name = settings.get("font_name", "Kalam")
            user_size = int(settings.get("font_size", 28))

            for block in page_layout.get("blocks", []):
                if block.get("type") != "text":
                    continue
                for line in block.get("lines", []):
                    txt = line.get("text", "").strip()
                    if not txt:
                        continue
                    bbox    = line.get("bbox", [0, 0, 0, 0])
                    orig_fs = float(line.get("font_size", 12))

                    # Scale font proportionally, cap at user setting
                    scaled = int(orig_fs * sy * 1.15)
                    scaled = max(10, min(scaled, user_size))

                    font = self._load_font(font_name, scaled)
                    x    = bbox[0] * sx
                    y    = bbox[1] * sy
                    self._draw_line(draw, txt, int(x), y, font, ink)

            img = img.filter(ImageFilter.GaussianBlur(radius=0.25))
            images.append(img)

        dst = self.output_dir / f"{sid}.pdf"
        self._images_to_pdf(images, str(dst))

        # Save first page as preview JPG
        if images:
            (self.output_dir / f"{sid}_page_0.jpg").write_bytes(
                self._img_to_bytes(images[0], "JPEG")
            )

        return str(dst)

    @staticmethod
    def _img_to_bytes(img: Image.Image, fmt: str) -> bytes:
        buf = io.BytesIO()
        img.save(buf, fmt, quality=95)
        return buf.getvalue()
