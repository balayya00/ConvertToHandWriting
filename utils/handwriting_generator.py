import os
import logging
import random
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

logger = logging.getLogger(__name__)

# Paper dimensions (at 96 DPI for screen, 150 DPI for print)
PAPER_SIZES = {
    'A4': (794, 1123),      # A4 at 96dpi
    'Letter': (816, 1056),   # US Letter at 96dpi
    'A4_150': (1240, 1754),  # A4 at 150dpi
}

# Color definitions
INK_COLORS = {
    'blue': (10, 10, 180),
    'dark_blue': (0, 0, 139),
    'black': (20, 20, 20),
    'dark_black': (0, 0, 0),
    'red': (180, 0, 0),
    'green': (0, 128, 0),
    'pencil': (80, 80, 80),
}

PAPER_COLORS = {
    'plain': (255, 255, 255),
    'ruled': (255, 255, 252),
    'cream': (255, 253, 240),
    'exam': (250, 250, 248),
    'graph': (252, 252, 255),
    'yellow': (255, 255, 220),
}

LINE_COLORS = {
    'plain': None,
    'ruled': (173, 216, 230),
    'cream': (200, 200, 180),
    'exam': (150, 150, 200),
    'graph': (200, 220, 255),
    'yellow': (200, 200, 150),
}

class HandwritingGenerator:
    """Generate handwritten text images and PDFs"""
    
    def __init__(self, fonts_folder: Path, output_folder: Path):
        self.fonts_folder = Path(fonts_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
    
    def _get_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """Load font with fallback handling"""
        from utils.font_manager import FontManager, HANDWRITING_FONTS
        
        fm = FontManager(self.fonts_folder)
        font_path = fm.get_font_path(font_name)
        
        if font_path and os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                logger.warning(f"Failed to load font {font_name}: {e}")
        
        # Try default fonts
        try:
            return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
        except:
            return ImageFont.load_default()
    
    def _create_paper(self, width: int, height: int, style: str, settings: Dict) -> Image.Image:
        """Create paper background with appropriate styling"""
        bg_color = PAPER_COLORS.get(style, PAPER_COLORS['ruled'])
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        margin = settings.get('margin', 60)
        font_size = settings.get('font_size', 28)
        line_spacing = settings.get('line_spacing', 1.8)
        
        line_height = int(font_size * line_spacing)
        
        if style == 'plain':
            # Just white paper with slight texture
            self._add_paper_texture(img, draw)
            
        elif style == 'ruled':
            # Classic ruled notebook paper
            self._add_paper_texture(img, draw)
            line_color = LINE_COLORS['ruled']
            
            # Draw horizontal lines
            y = margin + line_height
            while y < height - margin:
                draw.line([(margin, y), (width - margin, y)], 
                         fill=line_color, width=1)
                y += line_height
            
            # Red left margin line
            draw.line([(margin + 30, 0), (margin + 30, height)], 
                     fill=(255, 150, 150), width=2)
            
            # Top margin lines
            draw.line([(0, margin - 10), (width, margin - 10)], 
                     fill=(255, 150, 150), width=1)
        
        elif style == 'exam':
            # Exam sheet with boxes and lines
            self._add_paper_texture(img, draw)
            line_color = (100, 100, 200)
            
            # Outer border
            border_margin = 30
            draw.rectangle([border_margin, border_margin, 
                           width - border_margin, height - border_margin],
                          outline=(0, 0, 100), width=2)
            
            # Horizontal lines
            y = margin + line_height
            while y < height - margin:
                draw.line([(margin, y), (width - margin, y)], 
                         fill=line_color, width=1)
                y += line_height
            
            # Header box
            draw.rectangle([border_margin, border_margin, 
                           width - border_margin, margin], 
                          outline=(0, 0, 100), width=1)
            
            # Left margin
            draw.line([(margin + 20, margin), (margin + 20, height - border_margin)], 
                     fill=(100, 100, 200), width=1)
        
        elif style == 'graph':
            # Graph/grid paper
            self._add_paper_texture(img, draw, intensity=5)
            
            # Grid lines (minor)
            grid_size = 20
            for x in range(0, width, grid_size):
                draw.line([(x, 0), (x, height)], 
                         fill=(200, 220, 255), width=1)
            for y in range(0, height, grid_size):
                draw.line([(0, y), (width, y)], 
                         fill=(200, 220, 255), width=1)
            
            # Major grid lines
            major_grid = grid_size * 5
            for x in range(0, width, major_grid):
                draw.line([(x, 0), (x, height)], 
                         fill=(150, 180, 240), width=1)
            for y in range(0, height, major_grid):
                draw.line([(0, y), (width, y)], 
                         fill=(150, 180, 240), width=1)
        
        elif style in ['cream', 'yellow']:
            self._add_paper_texture(img, draw, intensity=8)
            
        return img
    
    def _add_paper_texture(self, img: Image.Image, draw: ImageDraw.Draw, intensity: int = 3):
        """Add subtle paper texture"""
        try:
            import numpy as np
            width, height = img.size
            
            # Create noise texture
            noise = np.random.randint(0, intensity, (height, width), dtype=np.uint8)
            noise_img = Image.fromarray(noise, mode='L').convert('RGB')
            
            # Very subtle blend
            img_array = np.array(img)
            noise_array = np.array(noise_img)
            textured = np.clip(img_array.astype(int) - noise_array // 3, 0, 255).astype(np.uint8)
            
            result = Image.fromarray(textured)
            img.paste(result)
        except ImportError:
            pass  # Skip texture if numpy not available
    
    def _apply_handwriting_effect(self, img: Image.Image, draw: ImageDraw.Draw,
                                   text: str, x: int, y: int, 
                                   font: ImageFont.FreeTypeFont,
                                   ink_color: Tuple[int, int, int],
                                   jitter: float = 0.8) -> None:
        """Draw text with handwriting-like effects"""
        
        # Add slight character-level variations for realism
        chars = list(text)
        current_x = x
        
        for i, char in enumerate(chars):
            # Slight vertical jitter per character
            char_y = y + random.uniform(-jitter, jitter)
            char_x = current_x
            
            # Slight rotation effect (very subtle)
            angle = random.uniform(-0.5, 0.5)
            
            # Vary ink color slightly
            color_variation = random.randint(-8, 8)
            char_color = tuple(max(0, min(255, c + color_variation)) for c in ink_color)
            
            # Draw the character
            draw.text((char_x, char_y), char, font=font, fill=char_color)
            
            # Get character width for next position
            try:
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
            except:
                char_width = font.getlength(char) if hasattr(font, 'getlength') else len(char) * (font.size // 2)
            
            # Slight spacing variation
            spacing_variation = random.uniform(-0.5, 0.5)
            current_x += char_width + spacing_variation
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, 
                   max_width: int) -> List[str]:
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            try:
                bbox = font.getbbox(word + ' ')
                word_width = bbox[2] - bbox[0]
            except:
                try:
                    word_width = int(font.getlength(word + ' '))
                except:
                    word_width = len(word) * (font.size // 2)
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else ['']
    
    def _render_page(self, text: str, settings: Dict, page_num: int = 0) -> List[Image.Image]:
        """Render text to one or more page images"""
        width = settings.get('page_width', 794)
        height = settings.get('page_height', 1123)
        font_name = settings.get('font_name', 'Kalam')
        font_size = settings.get('font_size', 28)
        line_spacing = settings.get('line_spacing', 1.8)
        ink_color_name = settings.get('ink_color', 'blue')
        margin = settings.get('margin', 60)
        paper_style = settings.get('paper_style', 'ruled')
        
        ink_color = INK_COLORS.get(ink_color_name, INK_COLORS['blue'])
        font = self._get_font(font_name, font_size)
        
        line_height = int(font_size * line_spacing)
        text_width = width - (margin * 2) - 30  # Extra margin for ruled line
        
        # Split text into paragraphs
        paragraphs = text.split('\n')
        
        # Wrap all paragraphs into lines
        all_lines = []
        for para in paragraphs:
            if para.strip() == '':
                all_lines.append('')  # Empty line for paragraph break
            else:
                wrapped = self._wrap_text(para, font, text_width)
                all_lines.extend(wrapped)
        
        # Calculate how many lines fit per page
        text_start_y = margin + 10
        available_height = height - margin - text_start_y
        lines_per_page = max(1, int(available_height / line_height))
        
        # Split lines into pages
        pages = []
        for i in range(0, max(1, len(all_lines)), lines_per_page):
            page_lines = all_lines[i:i + lines_per_page]
            pages.append(page_lines)
        
        if not pages:
            pages = [['']]
        
        # Render each page
        rendered_pages = []
        for page_lines in pages:
            img = self._create_paper(width, height, paper_style, settings)
            draw = ImageDraw.Draw(img)
            
            y = text_start_y
            left_x = margin + 35  # After the red margin line
            
            for line in page_lines:
                if y + line_height > height - margin:
                    break
                
                if line.strip():
                    # Add slight line-level baseline variation
                    baseline_var = random.uniform(-0.5, 0.5)
                    
                    self._apply_handwriting_effect(
                        img, draw, line,
                        left_x, y + baseline_var,
                        font, ink_color
                    )
                
                y += line_height
            
            # Add subtle ink smudge/bleed effect
            img = self._add_ink_effect(img)
            
            rendered_pages.append(img)
        
        return rendered_pages
    
    def _add_ink_effect(self, img: Image.Image) -> Image.Image:
        """Add subtle ink bleed/feathering effect for realism"""
        try:
            # Very slight blur to simulate ink spreading
            blurred = img.filter(ImageFilter.GaussianBlur(radius=0.3))
            # Blend slightly
            result = Image.blend(img, blurred, alpha=0.15)
            return result
        except:
            return img
    
    def generate_jpg(self, pages: List[str], settings: Dict, session_id: str) -> List[str]:
        """Generate JPG images for each page"""
        all_image_paths = []
        global_page_num = 0
        
        for page_text in pages:
            if not page_text.strip():
                continue
            
            rendered_pages = self._render_page(page_text, settings, global_page_num)
            
            for rendered_page in rendered_pages:
                # High quality output
                output_path = self.output_folder / f"{session_id}_page_{global_page_num}.jpg"
                
                rendered_page.save(
                    str(output_path),
                    'JPEG',
                    quality=95,
                    dpi=(150, 150),
                    optimize=True
                )
                
                all_image_paths.append(str(output_path))
                global_page_num += 1
        
        return all_image_paths
    
    def generate_pdf(self, pages: List[str], settings: Dict, session_id: str) -> str:
        """Generate PDF with all handwritten pages"""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Image as RLImage
        from reportlab.lib.units import inch
        import io
        
        output_path = self.output_folder / f"{session_id}.pdf"
        
        # First generate all page images
        all_images = []
        global_page_num = 0
        
        for page_text in pages:
            if not page_text.strip():
                continue
            
            rendered_pages = self._render_page(page_text, settings, global_page_num)
            
            for rendered_page in rendered_pages:
                all_images.append(rendered_page)
                global_page_num += 1
        
        if not all_images:
            all_images = [self._render_page('', settings, 0)[0]]
        
        # Create PDF with images
        try:
            self._create_pdf_from_images(all_images, str(output_path), settings)
        except Exception as e:
            logger.error(f"PDF creation error: {e}")
            # Fallback: simple PDF
            self._create_simple_pdf(all_images, str(output_path))
        
        return str(output_path)
    
    def _create_pdf_from_images(self, images: List[Image.Image], 
                                  output_path: str, settings: Dict):
        """Create PDF by embedding rendered page images"""
        import fitz
        
        doc = fitz.open()
        
        for img in images:
            # Convert PIL image to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', dpi=(150, 150))
            img_bytes.seek(0)
            
            # Get image dimensions
            width, height = img.size
            
            # Create PDF page with same dimensions (convert pixels to points)
            # 1 inch = 72 points, assuming 96 DPI
            dpi = 96
            page_width_pt = (width / dpi) * 72
            page_height_pt = (height / dpi) * 72
            
            page = doc.new_page(width=page_width_pt, height=page_height_pt)
            
            # Insert image
            rect = fitz.Rect(0, 0, page_width_pt, page_height_pt)
            page.insert_image(rect, stream=img_bytes.read())
        
        doc.save(output_path, deflate=True, garbage=4)
        doc.close()
    
    def _create_simple_pdf(self, images: List[Image.Image], output_path: str):
        """Fallback PDF creation using reportlab"""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.lib import colors
        import io
        
        doc = SimpleDocTemplate(output_path, pagesize=A4, 
                               topMargin=0, bottomMargin=0,
                               leftMargin=0, rightMargin=0)
        
        story = []
        page_width, page_height = A4
        
        for img in images:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            from reportlab.platypus import Image as RLImage
            rl_img = RLImage(img_bytes, width=page_width, height=page_height)
            story.append(rl_img)
        
        doc.build(story)


class PositionAwareGenerator(HandwritingGenerator):
    """Generate handwriting that preserves original PDF layout positions"""
    
    def render_with_layout(self, layout_data: List[Dict], 
                           settings: Dict, session_id: str) -> str:
        """Render handwriting preserving original PDF layout"""
        all_images = []
        
        for page_layout in layout_data:
            orig_width = page_layout.get('width', 595)
            orig_height = page_layout.get('height', 842)
            
            target_width = settings.get('page_width', 794)
            target_height = settings.get('page_height', 1123)
            
            # Scale factors
            scale_x = target_width / orig_width
            scale_y = target_height / orig_height
            
            paper_style = settings.get('paper_style', 'ruled')
            img = self._create_paper(target_width, target_height, paper_style, settings)
            draw = ImageDraw.Draw(img)
            
            font_name = settings.get('font_name', 'Kalam')
            ink_color = INK_COLORS.get(settings.get('ink_color', 'blue'), INK_COLORS['blue'])
            
            for block in page_layout.get('blocks', []):
                if block.get('type') == 'text':
                    for line in block.get('lines', []):
                        line_text = line.get('text', '').strip()
                        if not line_text:
                            continue
                        
                        bbox = line.get('bbox', [0, 0, 0, 0])
                        orig_font_size = line.get('font_size', 12)
                        
                        # Scale position
                        x = bbox[0] * scale_x
                        y = bbox[1] * scale_y
                        
                        # Scale font size proportionally
                        scaled_font_size = int(orig_font_size * scale_y * 1.2)
                        scaled_font_size = max(12, min(scaled_font_size, 
                                                        settings.get('font_size', 28)))
                        
                        font = self._get_font(font_name, scaled_font_size)
                        
                        self._apply_handwriting_effect(
                            img, draw, line_text, x, y, font, ink_color
                        )
            
            img = self._add_ink_effect(img)
            all_images.append(img)
        
        self._create_pdf_from_images(all_images, 
                                      str(self.output_folder / f"{session_id}.pdf"),
                                      settings)
        
        # Save preview image
        if all_images:
            preview_path = self.output_folder / f"{session_id}_page_0.jpg"
            all_images[0].save(str(preview_path), 'JPEG', quality=95)
        
        return str(self.output_folder / f"{session_id}.pdf")
