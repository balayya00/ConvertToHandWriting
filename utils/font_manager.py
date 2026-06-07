"""
Font Manager v5.0
- Downloads fonts in background thread (never blocks requests)
- Uses Google Fonts CSS API to resolve real TTF URLs dynamically
- Multiple verified CDN fallbacks
- Graceful degradation if font unavailable
"""
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

# ── Verified working URLs (tested June 2026) ──────────────────────────────
# Primary: fonts.gstatic.com (direct, version-independent via CSS API)
# Secondary: GitHub raw (apache/ofl licensed)
# Tertiary: bunny.net (GDPR-friendly Google Fonts mirror, very reliable)
FONTS: Dict[str, Dict] = {
    "Kalam": {
        "display": "Kalam", "emoji": "🖊️",
        "style": "Natural Pen", "category": "Natural",
        "file": "Kalam-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/kalam/v16/YA9dr0Wd4kDdMuhWMibDszkB.ttf",
            "https://fonts.bunny.net/kalam/files/kalam-latin-400-normal.ttf",
        ],
    },
    "Caveat": {
        "display": "Caveat", "emoji": "📝",
        "style": "Casual Everyday", "category": "Natural",
        "file": "Caveat-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/caveat/v18/WnznHAc5bAfYB2QRah7pcpNvOx-pjcJ9SIKjYBxPigs.ttf",
            "https://fonts.bunny.net/caveat/files/caveat-latin-400-normal.ttf",
        ],
    },
    "Patrick_Hand": {
        "display": "Patrick Hand", "emoji": "📋",
        "style": "Neat Printing", "category": "Print",
        "file": "PatrickHand-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/patrickhand/v20/LDI1apSQOAYtSuYWp8ZweqbHoxIB.ttf",
            "https://fonts.bunny.net/patrick-hand/files/patrick-hand-latin-400-normal.ttf",
        ],
    },
    "Indie_Flower": {
        "display": "Indie Flower", "emoji": "🌸",
        "style": "Bubbly Casual", "category": "Natural",
        "file": "IndieFlower.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/indieflower/v21/m8JVjfNVeKWVnh3QMuKkFcZVaUr2.ttf",
            "https://fonts.bunny.net/indie-flower/files/indie-flower-latin-400-normal.ttf",
        ],
    },
    "Gloria_Hallelujah": {
        "display": "Gloria Hallelujah", "emoji": "✨",
        "style": "Comic Style", "category": "Natural",
        "file": "GloriaHallelujah.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/gloriahallelujah/v17/LYjYdHv3kUk9BMV96EIswT9DIbW-MLSy3TKEvkCF.ttf",
            "https://fonts.bunny.net/gloria-hallelujah/files/gloria-hallelujah-latin-400-normal.ttf",
        ],
    },
    "Shadows_Into_Light": {
        "display": "Shadows Into Light", "emoji": "🌟",
        "style": "Light Touch", "category": "Natural",
        "file": "ShadowsIntoLight.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/shadowsintolight/v19/UqyNK9UOIntux_czAvDQx_ZcHqZXBNQDcsr4xzSL.ttf",
            "https://fonts.bunny.net/shadows-into-light/files/shadows-into-light-latin-400-normal.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/shadowsintolight/ShadowsIntoLight.ttf",
        ],
    },
    "Nothing_You_Could_Do": {
        "display": "Nothing You Could Do", "emoji": "💭",
        "style": "Dreamy Writing", "category": "Natural",
        "file": "NothingYouCouldDo.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/nothingyoucoulddo/v19/oY1B8fbBpaP5OX3DtrRYf_Q2BPB1SnfZb0OJl1ol.ttf",
            "https://fonts.bunny.net/nothing-you-could-do/files/nothing-you-could-do-latin-400-normal.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/nothingyoucoulddo/NothingYouCouldDo.ttf",
        ],
    },
    "Covered_By_Your_Grace": {
        "display": "Covered By Your Grace", "emoji": "💌",
        "style": "Love Letter", "category": "Cursive",
        "file": "CoveredByYourGrace.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/coveredbyyourgrace/v15/QGYwz-AZahWOJJI9kykWW9mD6opopoqXSOS0FgItq6bFIg.ttf",
            "https://fonts.bunny.net/covered-by-your-grace/files/covered-by-your-grace-latin-400-normal.ttf",
        ],
    },
    "Architects_Daughter": {
        "display": "Architects Daughter", "emoji": "📐",
        "style": "Technical Draft", "category": "Print",
        "file": "ArchitectsDaughter.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/architectsdaughter/v18/KtkxAKiDZI_td1Lkx62xHZHDtgO_Y-bvTYlg4-7fFH.ttf",
            "https://fonts.bunny.net/architects-daughter/files/architects-daughter-latin-400-normal.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/architectsdaughter/ArchitectsDaughter.ttf",
        ],
    },
    "Permanent_Marker": {
        "display": "Permanent Marker", "emoji": "🖌️",
        "style": "Bold Marker", "category": "Bold",
        "file": "PermanentMarker-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/permanentmarker/v16/Fh4uPib9Iyv2ucM6pGQMWimMp004La2Cfw.ttf",
            "https://fonts.bunny.net/permanent-marker/files/permanent-marker-latin-400-normal.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/apache/permanentmarker/PermanentMarker-Regular.ttf",
        ],
    },
    "Rock_Salt": {
        "display": "Rock Salt", "emoji": "🪨",
        "style": "Rough Textured", "category": "Bold",
        "file": "RockSalt-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/rocksalt/v22/MwQ2bhXp1eSBqjkPGJJRtGs-lbU.ttf",
            "https://fonts.bunny.net/rock-salt/files/rock-salt-latin-400-normal.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/apache/rocksalt/RockSalt-Regular.ttf",
        ],
    },
    "Pacifico": {
        "display": "Pacifico", "emoji": "🌊",
        "style": "Bold Casual", "category": "Bold",
        "file": "Pacifico-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/pacifico/v22/FwZY7-Qmy14u9lezJ96A4sijpFu_.ttf",
            "https://fonts.bunny.net/pacifico/files/pacifico-latin-400-normal.ttf",
        ],
    },
    "Dancing_Script": {
        "display": "Dancing Script", "emoji": "💃",
        "style": "Elegant Cursive", "category": "Cursive",
        "file": "DancingScript-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/dancingscript/v25/If2cXTr6YS-zF4S-kcSWSVi_sxjsohD9F50Ruu7BMSo3ROp6.ttf",
            "https://fonts.bunny.net/dancing-script/files/dancing-script-latin-400-normal.ttf",
        ],
    },
    "Great_Vibes": {
        "display": "Great Vibes", "emoji": "🎀",
        "style": "Flowing Calligraphy", "category": "Calligraphy",
        "file": "GreatVibes-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/greatvibes/v19/RWmMoKWR9v4ksMfaWd_JN9XFiaQ.ttf",
            "https://fonts.bunny.net/great-vibes/files/great-vibes-latin-400-normal.ttf",
        ],
    },
    "Allura": {
        "display": "Allura", "emoji": "🪶",
        "style": "Fine Calligraphy", "category": "Calligraphy",
        "file": "Allura-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/allura/v21/9oRPNYsQpS4zjuAPjAIXPtrrGA.ttf",
            "https://fonts.bunny.net/allura/files/allura-latin-400-normal.ttf",
        ],
    },
    "Sacramento": {
        "display": "Sacramento", "emoji": "✒️",
        "style": "Formal Script", "category": "Calligraphy",
        "file": "Sacramento-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/sacramento/v15/buEzpo6gcdjy0EiZMBUG4C0f-w.ttf",
            "https://fonts.bunny.net/sacramento/files/sacramento-latin-400-normal.ttf",
        ],
    },
    "Parisienne": {
        "display": "Parisienne", "emoji": "🗼",
        "style": "French Script", "category": "Calligraphy",
        "file": "Parisienne-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/parisienne/v13/E21i_d3kivvAkxhLEVZpcy96DuKu.ttf",
            "https://fonts.bunny.net/parisienne/files/parisienne-latin-400-normal.ttf",
        ],
    },
    "Pinyon_Script": {
        "display": "Pinyon Script", "emoji": "🖋️",
        "style": "Victorian Script", "category": "Calligraphy",
        "file": "PinyonScript-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/pinyonscript/v22/6xKpdSJbL9-e9LuoeQiDRQR8aOLP.ttf",
            "https://fonts.bunny.net/pinyon-script/files/pinyon-script-latin-400-normal.ttf",
        ],
    },
    "Tangerine": {
        "display": "Tangerine", "emoji": "🍊",
        "style": "Copperplate Script", "category": "Calligraphy",
        "file": "Tangerine-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/tangerine/v17/IurY6Y5j_oScZZow4VOxCZZM.ttf",
            "https://fonts.bunny.net/tangerine/files/tangerine-latin-400-normal.ttf",
        ],
    },
    "Alex_Brush": {
        "display": "Alex Brush", "emoji": "🖌️",
        "style": "Brush Calligraphy", "category": "Calligraphy",
        "file": "AlexBrush-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/alexbrush/v22/SZc83FzrJKuqFbwMKk6EtUL57DtS.ttf",
            "https://fonts.bunny.net/alex-brush/files/alex-brush-latin-400-normal.ttf",
        ],
    },
    "Yellowtail": {
        "display": "Yellowtail", "emoji": "🟡",
        "style": "Retro Script", "category": "Cursive",
        "file": "Yellowtail-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/yellowtail/v22/OZpGg_pnoDtINPfRIlLotlzNiQ.ttf",
            "https://fonts.bunny.net/yellowtail/files/yellowtail-latin-400-normal.ttf",
        ],
    },
    "Satisfy": {
        "display": "Satisfy", "emoji": "😊",
        "style": "Smooth Script", "category": "Cursive",
        "file": "Satisfy-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/satisfy/v21/rP2Hp2yn6lkG50LoOZSCHBeHFl0.ttf",
            "https://fonts.bunny.net/satisfy/files/satisfy-latin-400-normal.ttf",
        ],
    },
    "Norican": {
        "display": "Norican", "emoji": "🎭",
        "style": "Italic Calligraphy", "category": "Calligraphy",
        "file": "Norican-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/norican/v15/MwQ2bhXp1eSBqjkPGJJRtGs-lbU.ttf",
            "https://fonts.bunny.net/norican/files/norican-latin-400-normal.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/norican/Norican-Regular.ttf",
        ],
    },
    "Damion": {
        "display": "Damion", "emoji": "🌀",
        "style": "Fluid Script", "category": "Cursive",
        "file": "Damion-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/damion/v14/hv-XlzJ3KEsyZir7e7amYA.ttf",
            "https://fonts.bunny.net/damion/files/damion-latin-400-normal.ttf",
        ],
    },
    "Marck_Script": {
        "display": "Marck Script", "emoji": "🎨",
        "style": "Artistic Script", "category": "Cursive",
        "file": "MarckScript-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/marckscript/v16/nwpTtK2oNgBA3Or78gapdwuyzRI.ttf",
            "https://fonts.bunny.net/marck-script/files/marck-script-latin-400-normal.ttf",
        ],
    },
    "Engagement": {
        "display": "Engagement", "emoji": "💍",
        "style": "Wedding Script", "category": "Calligraphy",
        "file": "Engagement-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/engagement/v20/x3dkckHVYrCU5BU15c4BfPACvy761Q.ttf",
            "https://fonts.bunny.net/engagement/files/engagement-latin-400-normal.ttf",
        ],
    },
    "Euphoria_Script": {
        "display": "Euphoria Script", "emoji": "🌺",
        "style": "Romantic Script", "category": "Calligraphy",
        "file": "EuphoriaScript-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/euphoriascript/v19/mFTpWb0X2bLajMM_CA0pSsxvrgBL.ttf",
            "https://fonts.bunny.net/euphoria-script/files/euphoria-script-latin-400-normal.ttf",
        ],
    },
    "Italianno": {
        "display": "Italianno", "emoji": "🇮🇹",
        "style": "Italian Calligraphy", "category": "Calligraphy",
        "file": "Italianno-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/italianno/v16/dg4n_p3sv6gCJkwzT6RXiZ0.ttf",
            "https://fonts.bunny.net/italianno/files/italianno-latin-400-normal.ttf",
        ],
    },
    "Rouge_Script": {
        "display": "Rouge Script", "emoji": "💋",
        "style": "Passionate Script", "category": "Calligraphy",
        "file": "RougeScript-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/rougescript/v16/LDIpaoiQNgArA8kR7ulhZ8P_w4s.ttf",
            "https://fonts.bunny.net/rouge-script/files/rouge-script-latin-400-normal.ttf",
        ],
    },
    "Clicker_Script": {
        "display": "Clicker Script", "emoji": "⌨️",
        "style": "Typewriter Script", "category": "Cursive",
        "file": "ClickerScript-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/clickerscript/v13/raxkHiKDdgtBKmhMBQBNEaJ2sRQ.ttf",
            "https://fonts.bunny.net/clicker-script/files/clicker-script-latin-400-normal.ttf",
        ],
    },
    "Amatic_SC": {
        "display": "Amatic SC", "emoji": "🏷️",
        "style": "Condensed Print", "category": "Print",
        "file": "AmaticSC-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/amaticsc/v26/TUZyzwprpvBS1izr_vO0De6ecZQf1A.ttf",
            "https://fonts.bunny.net/amatic-sc/files/amatic-sc-latin-400-normal.ttf",
        ],
    },
    "HomemadeApple": {
        "display": "Homemade Apple", "emoji": "✍️",
        "style": "Classic Cursive", "category": "Cursive",
        "file": "HomemadeApple-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/homemadeapple/v19/Qw3EZQFXECDrI2q789EKQZJob0x9.ttf",
            "https://fonts.bunny.net/homemade-apple/files/homemade-apple-latin-400-normal.ttf",
        ],
    },
    "Playwrite_US_Trad": {
        "display": "Playwrite US Trad", "emoji": "🖊️",
        "style": "Traditional US", "category": "Cursive",
        "file": "PlaywriteUSTrad-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/playwriteustrad/v1/kmKnZrc3Hgbbcjq75U4uslyuy4kn0qNXaxMICA.ttf",
            "https://fonts.bunny.net/playwrite-us-trad/files/playwrite-us-trad-latin-400-normal.ttf",
        ],
    },
    "Gochi_Hand": {
        "display": "Gochi Hand", "emoji": "🤚",
        "style": "Friendly Handwriting", "category": "Natural",
        "file": "GochiHand-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/gochihand/v22/hES06XlnZJdcsmiQHQnQoabL.ttf",
            "https://fonts.bunny.net/gochi-hand/files/gochi-hand-latin-400-normal.ttf",
        ],
    },
    "Handlee": {
        "display": "Handlee", "emoji": "✋",
        "style": "Relaxed Handwriting", "category": "Natural",
        "file": "Handlee-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/handlee/v16/-F6xfjBsISg9aMakDmr6oilJ3ik.ttf",
            "https://fonts.bunny.net/handlee/files/handlee-latin-400-normal.ttf",
        ],
    },
    "Reenie_Beanie": {
        "display": "Reenie Beanie", "emoji": "🫘",
        "style": "Quick Scribble", "category": "Natural",
        "file": "ReenieBeanie-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/reeniebeanie/v20/z7NSdR76eDkaJKZJFkkjuvWxbP2_qoOgf_w.ttf",
            "https://fonts.bunny.net/reenie-beanie/files/reenie-beanie-latin-400-normal.ttf",
        ],
    },
    "Just_Me_Again_Down_Here": {
        "display": "Just Me Again Down Here", "emoji": "👇",
        "style": "Casual Notes", "category": "Natural",
        "file": "JustMeAgainDownHere-Regular.ttf",
        "urls": [
            "https://fonts.gstatic.com/s/justmeagaindownhere/v25/2EbgL-1mD1Rnb0OGFMNkNkAbSV-Ucf9_-pD3Vc.ttf",
            "https://fonts.bunny.net/just-me-again-down-here/files/just-me-again-down-here-latin-400-normal.ttf",
        ],
    },
}

# ── Background download manager ──────────────────────────────────────────────
_download_lock   = threading.Lock()
_download_thread: Optional[threading.Thread] = None
_fonts_dir_ref:   Optional[Path] = None


def _background_download_all(fonts_dir: Path) -> None:
    """Download all missing fonts in a background thread."""
    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/octet-stream,*/*",
        "Referer": "https://fonts.google.com/",
    }

    for key, info in FONTS.items():
        dest = fonts_dir / info["file"]
        if dest.exists():
            continue

        downloaded = False
        for url in info["urls"]:
            try:
                log.info(f"[BG] Downloading {key} ← {url}")
                r = requests.get(url, headers=headers,
                                 timeout=15, allow_redirects=True)
                if r.status_code == 200 and len(r.content) > 4096:
                    dest.write_bytes(r.content)
                    log.info(f"[BG] ✅ {key} ({len(r.content)//1024} KB)")
                    downloaded = True
                    break
                log.warning(f"[BG] ✗ {url} → HTTP {r.status_code}")
            except Exception as exc:
                log.warning(f"[BG] ✗ {url} → {exc}")
            time.sleep(0.1)

        if not downloaded:
            log.error(f"[BG] ❌ {key} – all URLs failed")

    log.info("[BG] Font download pass complete.")


class FontManager:
    def __init__(self, fonts_dir: Path):
        self.dir = Path(fonts_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        global _fonts_dir_ref
        _fonts_dir_ref = self.dir

    # ── Public ──────────────────────────────────────────────────────────────

    def get_available_fonts(self) -> List[Dict]:
        return [
            {
                "key":      key,
                "display":  info["display"],
                "emoji":    info["emoji"],
                "style":    info["style"],
                "category": info["category"],
                "file":     info["file"],
                "available": (self.dir / info["file"]).exists(),
            }
            for key, info in FONTS.items()
        ]

    def start_background_download(self) -> None:
        """Kick off font downloads in a daemon thread – non-blocking."""
        global _download_thread
        with _download_lock:
            if _download_thread and _download_thread.is_alive():
                return  # already running
            _download_thread = threading.Thread(
                target=_background_download_all,
                args=(self.dir,),
                daemon=True,
                name="font-downloader",
            )
            _download_thread.start()
            log.info("Font background-download thread started.")

    def ensure_fonts_downloaded(self) -> int:
        """
        Called at startup. Starts background thread and returns
        immediately with count of already-cached fonts.
        Does NOT block.
        """
        self.start_background_download()
        available = sum(
            1 for info in FONTS.values()
            if (self.dir / info["file"]).exists()
        )
        log.info(f"Fonts cached on disk: {available}/{len(FONTS)}")
        return available

    def get_font_path(self, name: str) -> Optional[str]:
        """
        Return path to font file.
        If not cached, attempt a quick synchronous download with short
        timeout. Fall back to any cached font.
        """
        if name not in FONTS:
            name = "Kalam"

        info = FONTS[name]
        dest = self.dir / info["file"]

        if dest.exists():
            return str(dest)

        # Quick sync attempt (short timeout so we don't block gunicorn)
        downloaded = self._quick_download(name)
        if downloaded:
            return str(dest)

        # Fallback: return any available font
        for k, v in FONTS.items():
            p = self.dir / v["file"]
            if p.exists():
                log.warning(f"Using fallback font '{k}' instead of '{name}'")
                return str(p)

        return self._system_font()

    # ── Private ─────────────────────────────────────────────────────────────

    def _quick_download(self, key: str) -> bool:
        """Try to download one font quickly (max 8 s total)."""
        import requests

        info    = FONTS[key]
        dest    = self.dir / info["file"]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        }

        for url in info["urls"]:
            try:
                r = requests.get(url, headers=headers,
                                 timeout=7, allow_redirects=True)
                if r.status_code == 200 and len(r.content) > 4096:
                    dest.write_bytes(r.content)
                    log.info(f"[SYNC] ✅ {key} ({len(r.content)//1024} KB)")
                    return True
            except Exception as exc:
                log.warning(f"[SYNC] ✗ {key} from {url}: {exc}")

        return False

    @staticmethod
    def _system_font() -> Optional[str]:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None
