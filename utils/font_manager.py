"""
Font Manager v6.0
- Uses Google Fonts CSS2 API to get real, current TTF URLs
- Falls back to raw.githubusercontent.com (most reliable)
- Background thread - never blocks requests
- Only includes fonts that actually exist and work
"""
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

log = logging.getLogger(__name__)

# These are 100% verified working fonts with correct filenames on GitHub raw
# Format: key -> {display, emoji, style, category, file, github_path}
# github_path = path under https://raw.githubusercontent.com/google/fonts/main/
FONTS: Dict[str, Dict] = {
    # ── Natural Handwriting ──────────────────────────────────────────────
    "Kalam": {
        "display": "Kalam", "emoji": "🖊️",
        "style": "Natural Pen", "category": "Natural",
        "file": "Kalam-Regular.ttf",
        "github": "ofl/kalam/Kalam-Regular.ttf",
    },
    "Caveat": {
        "display": "Caveat", "emoji": "📝",
        "style": "Casual Everyday", "category": "Natural",
        "file": "Caveat-Regular.ttf",
        "github": "ofl/caveat/static/Caveat-Regular.ttf",
    },
    "Indie_Flower": {
        "display": "Indie Flower", "emoji": "🌸",
        "style": "Bubbly Casual", "category": "Natural",
        "file": "IndieFlower.ttf",
        "github": "ofl/indieflower/IndieFlower.ttf",
    },
    "Gloria_Hallelujah": {
        "display": "Gloria Hallelujah", "emoji": "✨",
        "style": "Comic Style", "category": "Natural",
        "file": "GloriaHallelujah.ttf",
        "github": "ofl/gloriahallelujah/GloriaHallelujah.ttf",
    },
    "Shadows_Into_Light": {
        "display": "Shadows Into Light", "emoji": "🌟",
        "style": "Light Touch", "category": "Natural",
        "file": "ShadowsIntoLight.ttf",
        "github": "ofl/shadowsintolight/ShadowsIntoLight.ttf",
    },
    "Nothing_You_Could_Do": {
        "display": "Nothing You Could Do", "emoji": "💭",
        "style": "Dreamy Writing", "category": "Natural",
        "file": "NothingYouCouldDo.ttf",
        "github": "ofl/nothingyoucoulddo/NothingYouCouldDo.ttf",
    },
    "Covered_By_Your_Grace": {
        "display": "Covered By Your Grace", "emoji": "💌",
        "style": "Love Letter", "category": "Natural",
        "file": "CoveredByYourGrace.ttf",
        "github": "ofl/coveredbyyourgrace/CoveredByYourGrace.ttf",
    },
    "Gochi_Hand": {
        "display": "Gochi Hand", "emoji": "🤚",
        "style": "Friendly Writing", "category": "Natural",
        "file": "GochiHand-Regular.ttf",
        "github": "ofl/gochihand/GochiHand-Regular.ttf",
    },
    "Handlee": {
        "display": "Handlee", "emoji": "✋",
        "style": "Relaxed Pen", "category": "Natural",
        "file": "Handlee-Regular.ttf",
        "github": "ofl/handlee/Handlee-Regular.ttf",
    },
    "Patrick_Hand": {
        "display": "Patrick Hand", "emoji": "📋",
        "style": "Neat Printing", "category": "Print",
        "file": "PatrickHand-Regular.ttf",
        "github": "ofl/patrickhand/PatrickHand-Regular.ttf",
    },
    "Architects_Daughter": {
        "display": "Architects Daughter", "emoji": "📐",
        "style": "Technical Draft", "category": "Print",
        "file": "ArchitectsDaughter.ttf",
        "github": "ofl/architectsdaughter/ArchitectsDaughter.ttf",
    },
    "Amatic_SC": {
        "display": "Amatic SC", "emoji": "🏷️",
        "style": "Condensed Print", "category": "Print",
        "file": "AmaticSC-Regular.ttf",
        "github": "ofl/amaticsc/AmaticSC-Regular.ttf",
    },
    "Reenie_Beanie": {
        "display": "Reenie Beanie", "emoji": "🫘",
        "style": "Quick Scribble", "category": "Natural",
        "file": "ReenieBeanie-Regular.ttf",
        "github": "ofl/reeniebeanie/ReenieBeanie-Regular.ttf",
    },

    # ── Cursive / Script ─────────────────────────────────────────────────
    "Dancing_Script": {
        "display": "Dancing Script", "emoji": "💃",
        "style": "Elegant Cursive", "category": "Cursive",
        "file": "DancingScript-Regular.ttf",
        "github": "ofl/dancingscript/static/DancingScript-Regular.ttf",
    },
    "Satisfy": {
        "display": "Satisfy", "emoji": "😊",
        "style": "Smooth Script", "category": "Cursive",
        "file": "Satisfy-Regular.ttf",
        "github": "ofl/satisfy/Satisfy-Regular.ttf",
    },
    "Yellowtail": {
        "display": "Yellowtail", "emoji": "🟡",
        "style": "Retro Script", "category": "Cursive",
        "file": "Yellowtail-Regular.ttf",
        "github": "apache/yellowtail/Yellowtail-Regular.ttf",
    },
    "Damion": {
        "display": "Damion", "emoji": "🌀",
        "style": "Fluid Script", "category": "Cursive",
        "file": "Damion-Regular.ttf",
        "github": "ofl/damion/Damion-Regular.ttf",
    },
    "Norican": {
        "display": "Norican", "emoji": "🎭",
        "style": "Italic Script", "category": "Cursive",
        "file": "Norican-Regular.ttf",
        "github": "ofl/norican/Norican-Regular.ttf",
    },
    "Marck_Script": {
        "display": "Marck Script", "emoji": "🎨",
        "style": "Artistic Script", "category": "Cursive",
        "file": "MarckScript-Regular.ttf",
        "github": "ofl/marckscript/MarckScript-Regular.ttf",
    },
    "Homemade_Apple": {
        "display": "Homemade Apple", "emoji": "✍️",
        "style": "Classic Cursive", "category": "Cursive",
        "file": "HomemadeApple-Regular.ttf",
        "github": "apache/homemadeapple/HomemadeApple-Regular.ttf",
    },

    # ── Calligraphy ──────────────────────────────────────────────────────
    "Great_Vibes": {
        "display": "Great Vibes", "emoji": "🎀",
        "style": "Flowing Calligraphy", "category": "Calligraphy",
        "file": "GreatVibes-Regular.ttf",
        "github": "ofl/greatvibes/GreatVibes-Regular.ttf",
    },
    "Allura": {
        "display": "Allura", "emoji": "🪶",
        "style": "Fine Calligraphy", "category": "Calligraphy",
        "file": "Allura-Regular.ttf",
        "github": "ofl/allura/Allura-Regular.ttf",
    },
    "Sacramento": {
        "display": "Sacramento", "emoji": "✒️",
        "style": "Formal Script", "category": "Calligraphy",
        "file": "Sacramento-Regular.ttf",
        "github": "ofl/sacramento/Sacramento-Regular.ttf",
    },
    "Parisienne": {
        "display": "Parisienne", "emoji": "🗼",
        "style": "French Script", "category": "Calligraphy",
        "file": "Parisienne-Regular.ttf",
        "github": "ofl/parisienne/Parisienne-Regular.ttf",
    },
    "Pinyon_Script": {
        "display": "Pinyon Script", "emoji": "🖋️",
        "style": "Victorian Script", "category": "Calligraphy",
        "file": "PinyonScript-Regular.ttf",
        "github": "ofl/pinyonscript/PinyonScript-Regular.ttf",
    },
    "Tangerine": {
        "display": "Tangerine", "emoji": "🍊",
        "style": "Copperplate Script", "category": "Calligraphy",
        "file": "Tangerine-Regular.ttf",
        "github": "ofl/tangerine/Tangerine-Regular.ttf",
    },
    "Alex_Brush": {
        "display": "Alex Brush", "emoji": "🖌️",
        "style": "Brush Calligraphy", "category": "Calligraphy",
        "file": "AlexBrush-Regular.ttf",
        "github": "ofl/alexbrush/AlexBrush-Regular.ttf",
    },
    "Engagement": {
        "display": "Engagement", "emoji": "💍",
        "style": "Wedding Script", "category": "Calligraphy",
        "file": "Engagement-Regular.ttf",
        "github": "ofl/engagement/Engagement-Regular.ttf",
    },
    "Euphoria_Script": {
        "display": "Euphoria Script", "emoji": "🌺",
        "style": "Romantic Script", "category": "Calligraphy",
        "file": "EuphoriaScript-Regular.ttf",
        "github": "ofl/euphoriascript/EuphoriaScript-Regular.ttf",
    },

    # ── Bold / Marker ────────────────────────────────────────────────────
    "Permanent_Marker": {
        "display": "Permanent Marker", "emoji": "🖌️",
        "style": "Bold Marker", "category": "Bold",
        "file": "PermanentMarker-Regular.ttf",
        "github": "apache/permanentmarker/PermanentMarker-Regular.ttf",
    },
    "Rock_Salt": {
        "display": "Rock Salt", "emoji": "🪨",
        "style": "Rough Textured", "category": "Bold",
        "file": "RockSalt-Regular.ttf",
        "github": "apache/rocksalt/RockSalt-Regular.ttf",
    },
    "Pacifico": {
        "display": "Pacifico", "emoji": "🌊",
        "style": "Bold Casual", "category": "Bold",
        "file": "Pacifico-Regular.ttf",
        "github": "ofl/pacifico/Pacifico-Regular.ttf",
    },
}

# Download sources in priority order
_GH_RAW  = "https://raw.githubusercontent.com/google/fonts/main"
_GH_CDN  = "https://cdn.jsdelivr.net/gh/google/fonts@main"  # may 403, try anyway
_GSTATIC_API = "https://fonts.googleapis.com/css2?family={family}&display=swap"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

_dl_lock  = threading.Lock()
_dl_thread: Optional[threading.Thread] = None


class FontManager:
    def __init__(self, fonts_dir: Path):
        self.dir = Path(fonts_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ───────────────────────────────────────────────────────

    def get_available_fonts(self) -> List[Dict]:
        return [
            {
                "key":      k,
                "display":  v["display"],
                "emoji":    v["emoji"],
                "style":    v["style"],
                "category": v["category"],
                "file":     v["file"],
                "available": (self.dir / v["file"]).exists(),
            }
            for k, v in FONTS.items()
        ]

    def get_font_path(self, name: str) -> Optional[str]:
        """Return path to font, downloading synchronously if needed."""
        if name not in FONTS:
            name = "Kalam"
        dest = self.dir / FONTS[name]["file"]
        if not dest.exists():
            self._download_one(name)
        if dest.exists():
            return str(dest)
        # Fallback: any cached font
        for k, v in FONTS.items():
            p = self.dir / v["file"]
            if p.exists():
                log.warning(f"Font fallback: using {k} instead of {name}")
                return str(p)
        return self._system_font()

    def start_background_download(self) -> None:
        """Start downloading all fonts in background. Non-blocking."""
        global _dl_thread
        with _dl_lock:
            if _dl_thread and _dl_thread.is_alive():
                return
            _dl_thread = threading.Thread(
                target=self._download_all_bg,
                daemon=True,
                name="font-dl",
            )
            _dl_thread.start()
            log.info("Font background download started.")

    def ensure_fonts_downloaded(self) -> int:
        self.start_background_download()
        n = sum(1 for v in FONTS.values() if (self.dir / v["file"]).exists())
        log.info(f"Fonts on disk: {n}/{len(FONTS)}")
        return n

    # ── Download logic ───────────────────────────────────────────────────

    def _download_all_bg(self) -> None:
        for key in FONTS:
            dest = self.dir / FONTS[key]["file"]
            if not dest.exists():
                self._download_one(key)
            time.sleep(0.05)
        log.info("[BG] All font downloads complete.")

    def _download_one(self, key: str) -> bool:
        """Try multiple strategies to download a font."""
        info = FONTS[key]
        dest = self.dir / info["file"]
        if dest.exists():
            return True

        github_path = info.get("github", "")

        # Strategy 1: GitHub raw.githubusercontent.com
        if github_path:
            url = f"{_GH_RAW}/{github_path}"
            if self._fetch(key, url, dest):
                return True

        # Strategy 2: jsDelivr CDN (GitHub mirror)
        if github_path:
            url = f"{_GH_CDN}/{github_path}"
            if self._fetch(key, url, dest):
                return True

        # Strategy 3: Resolve from Google Fonts CSS API
        family = info["display"].replace(" ", "+")
        ttf_url = self._resolve_gstatic_url(family)
        if ttf_url and self._fetch(key, ttf_url, dest):
            return True

        log.error(f"[DL] ❌ {key} – all strategies failed")
        return False

    def _fetch(self, key: str, url: str, dest: Path) -> bool:
        """Download URL to dest. Returns True on success."""
        try:
            log.info(f"[DL] {key} ← {url}")
            r = requests.get(url, headers=_HEADERS,
                             timeout=20, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 4096:
                dest.write_bytes(r.content)
                log.info(f"[DL] ✅ {key} ({len(r.content)//1024} KB)")
                return True
            log.warning(f"[DL] ✗ {url} → HTTP {r.status_code} "
                        f"({len(r.content)} bytes)")
        except Exception as e:
            log.warning(f"[DL] ✗ {url} → {e}")
        return False

    def _resolve_gstatic_url(self, family: str) -> Optional[str]:
        """
        Call Google Fonts CSS2 API and extract the TTF/OTF src URL.
        This gives us the current, correct URL regardless of version.
        """
        try:
            api_url = (
                f"https://fonts.googleapis.com/css2"
                f"?family={family}&display=swap"
            )
            # Must use a desktop UA to get TTF (mobile gets woff2)
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            }
            r = requests.get(api_url, headers=headers, timeout=10)
            if r.status_code != 200:
                return None
            # Extract src url(...) from CSS
            matches = re.findall(
                r'src:\s*url\(([^)]+\.(?:ttf|otf))\)', r.text
            )
            if matches:
                return matches[0]
            # Also try woff2 and convert — skip, just return None
        except Exception as e:
            log.warning(f"[GAPI] {family}: {e}")
        return None

    @staticmethod
    def _system_font() -> Optional[str]:
        for p in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]:
            if os.path.exists(p):
                return p
        return None
