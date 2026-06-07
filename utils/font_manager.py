import os
import logging
import requests
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

# Google Fonts - Handwriting fonts with direct download URLs
HANDWRITING_FONTS = {
    'HomemadeApple': {
        'display_name': '✍️ Homemade Apple (Classic Cursive)',
        'url': 'https://github.com/google/fonts/raw/main/apache/homemadeapple/HomemadeApple-Regular.ttf',
        'filename': 'HomemadeApple-Regular.ttf',
        'style': 'cursive',
        'description': 'Natural flowing cursive handwriting'
    },
    'Caveat': {
        'display_name': '📝 Caveat (Casual Handwriting)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf',
        'filename': 'Caveat-Regular.ttf',
        'fallback_url': 'https://fonts.gstatic.com/s/caveat/v17/WnznHAc5bAfYB2QRah7pcpNvOx-pjfJ9SIKjYBxPigs.woff2',
        'style': 'casual',
        'description': 'Relaxed everyday handwriting'
    },
    'Kalam': {
        'display_name': '🖊️ Kalam (Natural Pen)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf',
        'filename': 'Kalam-Regular.ttf',
        'style': 'natural',
        'description': 'Natural pen writing style'
    },
    'DancingScript': {
        'display_name': '💫 Dancing Script (Elegant Cursive)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/dancingscript/DancingScript%5Bwght%5D.ttf',
        'filename': 'DancingScript-Regular.ttf',
        'style': 'elegant',
        'description': 'Elegant flowing script'
    },
    'Pacifico': {
        'display_name': '🌊 Pacifico (Bold Casual)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf',
        'filename': 'Pacifico-Regular.ttf',
        'style': 'bold',
        'description': 'Bold casual handwriting'
    },
    'Sacramento': {
        'display_name': '✒️ Sacramento (Fine Calligraphy)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/sacramento/Sacramento-Regular.ttf',
        'filename': 'Sacramento-Regular.ttf',
        'style': 'calligraphy',
        'description': 'Fine calligraphic script'
    },
    'Satisfy': {
        'display_name': '🎨 Satisfy (Smooth Script)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/satisfy/Satisfy-Regular.ttf',
        'filename': 'Satisfy-Regular.ttf',
        'style': 'smooth',
        'description': 'Smooth flowing script'
    },
    'GloriaHallelujah': {
        'display_name': '✨ Gloria Hallelujah (Comic Style)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/gloriahallelujah/GloriaHallelujah.ttf',
        'filename': 'GloriaHallelujah.ttf',
        'style': 'comic',
        'description': 'Comic book style handwriting'
    },
    'Shadows_Into_Light': {
        'display_name': '🌟 Shadows Into Light (Light Touch)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/shadowsintolight/ShadowsIntoLight.ttf',
        'filename': 'ShadowsIntoLight.ttf',
        'style': 'light',
        'description': 'Light delicate handwriting'
    },
    'Indie_Flower': {
        'display_name': '🌸 Indie Flower (Bubbly)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/indieflower/IndieFlower.ttf',
        'filename': 'IndieFlower.ttf',
        'style': 'bubbly',
        'description': 'Cute bubbly handwriting'
    },
    'Permanent_Marker': {
        'display_name': '🖌️ Permanent Marker (Marker Style)',
        'url': 'https://github.com/google/fonts/raw/main/apache/permanentmarker/PermanentMarker-Regular.ttf',
        'filename': 'PermanentMarker-Regular.ttf',
        'style': 'marker',
        'description': 'Bold marker handwriting'
    },
    'Patrick_Hand': {
        'display_name': '📋 Patrick Hand (Neat Print)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/patrickhand/PatrickHand-Regular.ttf',
        'filename': 'PatrickHand-Regular.ttf',
        'style': 'print',
        'description': 'Clean neat handprinting'
    },
    'Amatic_SC': {
        'display_name': '📐 Amatic SC (Small Caps Print)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/amaticsc/AmaticSC-Regular.ttf',
        'filename': 'AmaticSC-Regular.ttf',
        'style': 'print',
        'description': 'Condensed handprinted style'
    },
    'Covered_By_Your_Grace': {
        'display_name': '💌 Covered By Your Grace (Love Letter)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/coveredbyyourgrace/CoveredByYourGrace.ttf',
        'filename': 'CoveredByYourGrace.ttf',
        'style': 'romantic',
        'description': 'Romantic letter writing style'
    },
    'Rock_Salt': {
        'display_name': '🧂 Rock Salt (Rough Writing)',
        'url': 'https://github.com/google/fonts/raw/main/apache/rocksalt/RockSalt-Regular.ttf',
        'filename': 'RockSalt-Regular.ttf',
        'style': 'rough',
        'description': 'Rough textured handwriting'
    },
    'Yellowtail': {
        'display_name': '🟡 Yellowtail (Retro Script)',
        'url': 'https://github.com/google/fonts/raw/main/apache/yellowtail/Yellowtail-Regular.ttf',
        'filename': 'Yellowtail-Regular.ttf',
        'style': 'retro',
        'description': 'Retro flowing script'
    },
    'Architects_Daughter': {
        'display_name': '🏗️ Architects Daughter (Technical)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/architectsdaughter/ArchitectsDaughter.ttf',
        'filename': 'ArchitectsDaughter.ttf',
        'style': 'technical',
        'description': 'Technical drafting style'
    },
    'Nothing_You_Could_Do': {
        'display_name': '💭 Nothing You Could Do (Dreamy)',
        'url': 'https://github.com/google/fonts/raw/main/ofl/nothingyoucoulddo/NothingYouCouldDo.ttf',
        'filename': 'NothingYouCouldDo.ttf',
        'style': 'dreamy',
        'description': 'Dreamy flowing handwriting'
    },
}

# Alternative CDN URLs for fallback
FONT_CDN_BASE = "https://fonts.gstatic.com/s"

class FontManager:
    def __init__(self, fonts_folder: Path):
        self.fonts_folder = Path(fonts_folder)
        self.fonts_folder.mkdir(parents=True, exist_ok=True)
    
    def get_available_fonts(self) -> List[Dict]:
        """Return list of available fonts with their info"""
        fonts = []
        for key, info in HANDWRITING_FONTS.items():
            font_path = self.fonts_folder / info['filename']
            fonts.append({
                'key': key,
                'display_name': info['display_name'],
                'style': info['style'],
                'description': info['description'],
                'available': font_path.exists(),
                'filename': info['filename']
            })
        return fonts
    
    def get_font_path(self, font_name: str) -> str:
        """Get the file path for a font"""
        if font_name not in HANDWRITING_FONTS:
            font_name = 'Kalam'  # Default fallback
        
        font_info = HANDWRITING_FONTS[font_name]
        font_path = self.fonts_folder / font_info['filename']
        
        if not font_path.exists():
            logger.info(f"Font {font_name} not found, downloading...")
            self.download_font(font_name)
        
        if font_path.exists():
            return str(font_path)
        
        # Try system fonts as last resort
        return self._get_system_font()
    
    def _get_system_font(self) -> str:
        """Try to find a system font as fallback"""
        system_font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            'C:/Windows/Fonts/arial.ttf',
        ]
        for path in system_font_paths:
            if os.path.exists(path):
                return path
        return None
    
    def download_font(self, font_name: str) -> bool:
        """Download a specific font"""
        if font_name not in HANDWRITING_FONTS:
            return False
        
        font_info = HANDWRITING_FONTS[font_name]
        font_path = self.fonts_folder / font_info['filename']
        
        if font_path.exists():
            return True
        
        urls_to_try = [font_info['url']]
        if 'fallback_url' in font_info:
            urls_to_try.append(font_info['fallback_url'])
        
        for url in urls_to_try:
            try:
                logger.info(f"Downloading font {font_name} from {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=30, headers=headers)
                if response.status_code == 200 and len(response.content) > 1000:
                    font_path.write_bytes(response.content)
                    logger.info(f"✅ Downloaded font: {font_name}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to download {font_name} from {url}: {e}")
        
        logger.error(f"❌ Failed to download font: {font_name}")
        return False
    
    def ensure_fonts_downloaded(self):
        """Download all fonts that haven't been downloaded yet"""
        success_count = 0
        for font_name in HANDWRITING_FONTS:
            font_info = HANDWRITING_FONTS[font_name]
            font_path = self.fonts_folder / font_info['filename']
            if not font_path.exists():
                if self.download_font(font_name):
                    success_count += 1
            else:
                success_count += 1
        
        logger.info(f"Font status: {success_count}/{len(HANDWRITING_FONTS)} fonts available")
        return success_count
