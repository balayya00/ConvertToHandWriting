"""
Font Manager
Downloads and manages handwriting fonts from Google Fonts GitHub mirror.
"""
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# ─── Font Registry ───────────────────────────────────────────────────────────
# Each entry: key → {display_name, filename, urls (ordered by preference),
#                    style, description}
#
# Primary URLs point to raw GitHub releases (pre-built TTF files).
# Fallback URLs use jsDelivr CDN which mirrors Google Fonts.

_GH = "https://github.com/google/fonts/raw/main"
_CD = "https://cdn.jsdelivr.net/gh/google/fonts@main"

FONT_REGISTRY: Dict[str, Dict] = {
    "HomemadeApple": {
        "display_name": "✍️ Homemade Apple",
        "filename":     "HomemadeApple-Regular.ttf",
        "style":        "cursive",
        "description":  "Natural flowing cursive",
        "urls": [
            f"{_GH}/apache/homemadeapple/HomemadeApple-Regular.ttf",
            f"{_CD}/apache/homemadeapple/HomemadeApple-Regular.ttf",
        ],
    },
    "Caveat": {
        "display_name": "📝 Caveat",
        "filename":     "Caveat-Regular.ttf",
        "style":        "casual",
        "description":  "Relaxed everyday handwriting",
        "urls": [
            f"{_GH}/ofl/caveat/static/Caveat-Regular.ttf",
            f"{_CD}/ofl/caveat/static/Caveat-Regular.ttf",
        ],
    },
    "Kalam": {
        "display_name": "🖊️ Kalam",
        "filename":     "Kalam-Regular.ttf",
        "style":        "natural",
        "description":  "Natural pen writing style",
        "urls": [
            f"{_GH}/ofl/kalam/Kalam-Regular.ttf",
            f"{_CD}/ofl/kalam/Kalam-Regular.ttf",
        ],
    },
    "DancingScript": {
        "display_name": "💫 Dancing Script",
        "filename":     "DancingScript-Regular.ttf",
        "style":        "elegant",
        "description":  "Elegant flowing script",
        "urls": [
            f"{_GH}/ofl/dancingscript/static/DancingScript-Regular.ttf",
            f"{_CD}/ofl/dancingscript/static/DancingScript-Regular.ttf",
        ],
    },
    "Pacifico": {
        "display_name": "🌊 Pacifico",
        "filename":     "Pacifico-Regular.ttf",
        "style":        "bold",
        "description":  "Bold casual handwriting",
        "urls": [
            f"{_GH}/ofl/pacifico/Pacifico-Regular.ttf",
            f"{_CD}/ofl/pacifico/Pacifico-Regular.ttf",
        ],
    },
    "Sacramento": {
        "display_name": "✒️ Sacramento",
        "filename":     "Sacramento-Regular.ttf",
        "style":        "calligraphy",
        "description":  "Fine calligraphic script",
        "urls": [
            f"{_GH}/ofl/sacramento/Sacramento-Regular.ttf",
            f"{_CD}/ofl/sacramento/Sacramento-Regular.ttf",
        ],
    },
    "Satisfy": {
        "display_name": "🎨 Satisfy",
        "filename":     "Satisfy-Regular.ttf",
        "style":        "smooth",
        "description":  "Smooth flowing script",
        "urls": [
            f"{_GH}/ofl/satisfy/Satisfy-Regular.ttf",
            f"{_CD}/ofl/satisfy/Satisfy-Regular.ttf",
        ],
    },
    "GloriaHallelujah": {
        "display_name": "✨ Gloria Hallelujah",
        "filename":     "GloriaHallelujah.ttf",
        "style":        "comic",
        "description":  "Comic book handwriting",
        "urls": [
            f"{_GH}/ofl/gloriahallelujah/GloriaHallelujah.ttf",
            f"{_CD}/ofl/gloriahallelujah/GloriaHallelujah.ttf",
        ],
    },
    "ShadowsIntoLight": {
        "display_name": "🌟 Shadows Into Light",
        "filename":     "ShadowsIntoLight.ttf",
        "style":        "light",
        "description":  "Light delicate handwriting",
        "urls": [
            f"{_GH}/ofl/shadowsintolight/ShadowsIntoLight.ttf",
            f"{_CD}/ofl/shadowsintolight/ShadowsIntoLight.ttf",
        ],
    },
    "IndieFlower": {
        "display_name": "🌸 Indie Flower",
        "filename":     "IndieFlower.ttf",
        "style":        "bubbly",
        "description":  "Cute bubbly handwriting",
        "urls": [
            f"{_GH}/ofl/indieflower/IndieFlower.ttf",
            f"{_CD}/ofl/indieflower/IndieFlower.ttf",
        ],
    },
    "PermanentMarker": {
        "display_name": "🖌️ Permanent Marker",
        "filename":     "PermanentMarker-Regular.ttf",
        "style":        "marker",
        "description":  "Bold marker handwriting",
        "urls": [
            f"{_GH}/apache/permanentmarker/PermanentMarker-Regular.ttf",
            f"{_CD}/apache/permanentmarker/PermanentMarker-Regular.ttf",
        ],
    },
    "PatrickHand": {
        "display_name": "📋 Patrick Hand",
        "filename":     "PatrickHand-Regular.ttf",
        "style":        "print",
        "description":  "Clean neat handprinting",
        "urls": [
            f"{_GH}/ofl/patrickhand/PatrickHand-Regular.ttf",
            f"{_CD}/ofl/patrickhand/PatrickHand-Regular.ttf",
        ],
    },
    "AmaticSC": {
        "display_name": "📐 Amatic SC",
        "filename":     "AmaticSC-Regular.ttf",
        "style":        "print",
        "description":  "Condensed handprinted style",
        "urls": [
            f"{_GH}/ofl/amaticsc/AmaticSC-Regular.ttf",
            f"{_CD}/ofl/amaticsc/AmaticSC-Regular.ttf",
        ],
    },
    "CoveredByYourGrace": {
        "display_name": "💌 Covered By Your Grace",
        "filename":     "CoveredByYourGrace.ttf",
        "style":        "romantic",
        "description":  "Romantic letter writing",
        "urls": [
            f"{_GH}/ofl/coveredbyyourgrace/CoveredByYourGrace.ttf",
            f"{_CD}/ofl/coveredbyyourgrace/CoveredByYourGrace.ttf",
        ],
    },
    "RockSalt": {
        "display_name": "🧂 Rock Salt",
        "filename":     "RockSalt-Regular.ttf",
        "style":        "rough",
        "description":  "Rough textured handwriting",
        "urls": [
            f"{_GH}/apache/rocksalt/RockSalt-Regular.ttf",
            f"{_CD}/apache/rocksalt/RockSalt-Regular.ttf",
        ],
    },
    "Yellowtail": {
        "display_name": "🟡 Yellowtail",
        "filename":     "Yellowtail-Regular.ttf",
        "style":        "retro",
        "description":  "Retro flowing script",
        "urls": [
            f"{_GH}/apache/yellowtail/Yellowtail-Regular.ttf",
            f"{_CD}/apache/yellowtail/Yellowtail-Regular.ttf",
        ],
    },
    "ArchitectsDaughter": {
        "display_name": "🏗️ Architects Daughter",
        "filename":     "ArchitectsDaughter.ttf",
        "style":        "technical",
        "description":  "Technical drafting style",
        "urls": [
            f"{_GH}/ofl/architectsdaughter/ArchitectsDaughter.ttf",
            f"{_CD}/ofl/architectsdaughter/ArchitectsDaughter.ttf",
        ],
    },
    "NothingYouCouldDo": {
        "display_name": "💭 Nothing You Could Do",
        "filename":     "NothingYouCouldDo.ttf",
        "style":        "dreamy",
        "description":  "Dreamy flowing handwriting",
        "urls": [
            f"{_GH}/ofl/nothingyoucoulddo/NothingYouCouldDo.ttf",
            f"{_CD}/ofl/nothingyoucoulddo/NothingYouCouldDo.ttf",
        ],
    },
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}


class FontManager:
    def __init__(self, fonts_dir: Path):
        self.dir = Path(fonts_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────

    def get_available_fonts(self) -> List[Dict]:
        out = []
        for key, info in FONT_REGISTRY.items():
            out.append({
                "key":          key,
                "display_name": info["display_name"],
                "style":        info["style"],
                "description":  info["description"],
                "filename":     info["filename"],
                "available":    (self.dir / info["filename"]).exists(),
            })
        return out

    def get_font_path(self, font_name: str) -> Optional[str]:
        """Return local path, downloading first if needed."""
        if font_name not in FONT_REGISTRY:
            font_name = "Kalam"

        info = FONT_REGISTRY[font_name]
        path = self.dir / info["filename"]

        if not path.exists():
            self._download(font_name)

        if path.exists():
            return str(path)

        # Last resort: another font that IS available
        for key in FONT_REGISTRY:
            p = self.dir / FONT_REGISTRY[key]["filename"]
            if p.exists():
                logger.warning(f"Using fallback font: {key}")
                return str(p)

        return self._system_font()

    def ensure_fonts_downloaded(self) -> int:
        """Download any missing fonts. Returns number available."""
        ok = 0
        for key in FONT_REGISTRY:
            path = self.dir / FONT_REGISTRY[key]["filename"]
            if path.exists():
                ok += 1
            else:
                if self._download(key):
                    ok += 1
        logger.info(f"Fonts available: {ok}/{len(FONT_REGISTRY)}")
        return ok

    # ── Private ──────────────────────────────────────────────────────────

    def _download(self, font_name: str) -> bool:
        info = FONT_REGISTRY[font_name]
        dest = self.dir / info["filename"]

        for url in info["urls"]:
            try:
                logger.info(f"  Downloading {font_name} from {url}")
                r = requests.get(url, headers=_HEADERS,
                                 timeout=25, allow_redirects=True)
                if r.status_code == 200 and len(r.content) > 4096:
                    dest.write_bytes(r.content)
                    logger.info(f"  ✅ {font_name} saved ({len(r.content)//1024} KB)")
                    return True
                else:
                    logger.warning(f"  ⚠ {url}: HTTP {r.status_code}, "
                                   f"size={len(r.content)}")
            except Exception as exc:
                logger.warning(f"  ⚠ {url}: {exc}")
            time.sleep(0.3)

        logger.error(f"  ❌ Could not download {font_name}")
        return False

    @staticmethod
    def _system_font() -> Optional[str]:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
        for p in candidates:
            if Path(p).exists():
                return p
        return None
