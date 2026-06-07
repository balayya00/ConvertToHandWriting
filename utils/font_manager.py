"""
Font Manager v4.0
- Uses Google Fonts API CSS to get direct gstatic.com TTF/OTF URLs
- Falls back to multiple CDN mirrors
- 30+ handwriting & calligraphy fonts
"""
import logging
import time
import os
from pathlib import Path
from typing import List, Dict, Optional

log = logging.getLogger(__name__)

# ── Font Registry ──────────────────────────────────────────────────────────────
# URLs are direct .ttf links from gstatic CDN (stable, no redirect)
FONTS: Dict[str, Dict] = {

    # ── Classic Cursive ────────────────────────────────────────
    "HomemadeApple": {
        "display": "Homemade Apple",
        "emoji":   "✍️",
        "style":   "Classic Cursive",
        "file":    "HomemadeApple-Regular.ttf",
        "google":  "Homemade+Apple",
        "urls": [
            "https://fonts.gstatic.com/s/homemadeapple/v19/Qw3EZQFXECDrI2q789EKQZJob0x9.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/apache/homemadeapple/HomemadeApple-Regular.ttf",
        ],
    },
    "DancingScript": {
        "display": "Dancing Script",
        "emoji":   "💃",
        "style":   "Elegant Cursive",
        "file":    "DancingScript-Regular.ttf",
        "google":  "Dancing+Script",
        "urls": [
            "https://fonts.gstatic.com/s/dancingscript/v25/If2cXTr6YS-zF4S-kcSWSVi_sxjsohD9F50Ruu7BMSo3Sup5.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/dancingscript/static/DancingScript-Regular.ttf",
        ],
    },
    "GreatVibes": {
        "display": "Great Vibes",
        "emoji":   "🎀",
        "style":   "Flowing Calligraphy",
        "file":    "GreatVibes-Regular.ttf",
        "google":  "Great+Vibes",
        "urls": [
            "https://fonts.gstatic.com/s/greatvibes/v19/RWmMoKWR9v4ksMfaWd_JN9XFiaQ.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/greatvibes/GreatVibes-Regular.ttf",
        ],
    },
    "Allura": {
        "display": "Allura",
        "emoji":   "🪶",
        "style":   "Fine Calligraphy",
        "file":    "Allura-Regular.ttf",
        "google":  "Allura",
        "urls": [
            "https://fonts.gstatic.com/s/allura/v21/9oRPNYsQpS4zjuAPjAIXPtrrGA.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/allura/Allura-Regular.ttf",
        ],
    },
    "Sacramento": {
        "display": "Sacramento",
        "emoji":   "✒️",
        "style":   "Formal Script",
        "file":    "Sacramento-Regular.ttf",
        "google":  "Sacramento",
        "urls": [
            "https://fonts.gstatic.com/s/sacramento/v15/buEzpo6gcdjy0EiZMBUG4C0f-w.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/sacramento/Sacramento-Regular.ttf",
        ],
    },
    "Parisienne": {
        "display": "Parisienne",
        "emoji":   "🗼",
        "style":   "French Script",
        "file":    "Parisienne-Regular.ttf",
        "google":  "Parisienne",
        "urls": [
            "https://fonts.gstatic.com/s/parisienne/v13/E21i_d3kivvAkxhLEVZpcy96DuKu.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/parisienne/Parisienne-Regular.ttf",
        ],
    },
    "Pinyon_Script": {
        "display": "Pinyon Script",
        "emoji":   "🖋️",
        "style":   "Victorian Script",
        "file":    "PinyonScript-Regular.ttf",
        "google":  "Pinyon+Script",
        "urls": [
            "https://fonts.gstatic.com/s/pinyonscript/v22/6xKpdSJbL9-e9LuoeQiDRQR8aOLP.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/pinyonscript/PinyonScript-Regular.ttf",
        ],
    },
    "Tangerine": {
        "display": "Tangerine",
        "emoji":   "🍊",
        "style":   "Copperplate Script",
        "file":    "Tangerine-Regular.ttf",
        "google":  "Tangerine",
        "urls": [
            "https://fonts.gstatic.com/s/tangerine/v17/IurY6Y5j_oScZZow4VOxCZZM.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/tangerine/Tangerine-Regular.ttf",
        ],
    },
    "AlexBrush": {
        "display": "Alex Brush",
        "emoji":   "🖌️",
        "style":   "Brush Calligraphy",
        "file":    "AlexBrush-Regular.ttf",
        "google":  "Alex+Brush",
        "urls": [
            "https://fonts.gstatic.com/s/alexbrush/v22/SZc83FzrJKuqFbwMKk6EtUL57DtS.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/alexbrush/AlexBrush-Regular.ttf",
        ],
    },
    "Yellowtail": {
        "display": "Yellowtail",
        "emoji":   "🟡",
        "style":   "Retro Script",
        "file":    "Yellowtail-Regular.ttf",
        "google":  "Yellowtail",
        "urls": [
            "https://fonts.gstatic.com/s/yellowtail/v22/OZpGg_pnoDtINPfRIlLotlzNiQ.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/apache/yellowtail/Yellowtail-Regular.ttf",
        ],
    },
    "Satisfy": {
        "display": "Satisfy",
        "emoji":   "😊",
        "style":   "Smooth Script",
        "file":    "Satisfy-Regular.ttf",
        "google":  "Satisfy",
        "urls": [
            "https://fonts.gstatic.com/s/satisfy/v21/rP2Hp2yn6lkG50LoOZSCHBeHFl0.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/satisfy/Satisfy-Regular.ttf",
        ],
    },

    # ── Natural Handwriting ────────────────────────────────────
    "Kalam": {
        "display": "Kalam",
        "emoji":   "🖊️",
        "style":   "Natural Pen",
        "file":    "Kalam-Regular.ttf",
        "google":  "Kalam",
        "urls": [
            "https://fonts.gstatic.com/s/kalam/v16/YA9dr0Wd4kDdMuhWMibDszkB.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/kalam/Kalam-Regular.ttf",
        ],
    },
    "Caveat": {
        "display": "Caveat",
        "emoji":   "📝",
        "style":   "Casual Everyday",
        "file":    "Caveat-Regular.ttf",
        "google":  "Caveat",
        "urls": [
            "https://fonts.gstatic.com/s/caveat/v18/WnznHAc5bAfYB2QRah7pcpNvOx-pjcJ9SIKjYBxPigs.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/caveat/static/Caveat-Regular.ttf",
        ],
    },
    "Patrick_Hand": {
        "display": "Patrick Hand",
        "emoji":   "📋",
        "style":   "Neat Printing",
        "file":    "PatrickHand-Regular.ttf",
        "google":  "Patrick+Hand",
        "urls": [
            "https://fonts.gstatic.com/s/patrickhand/v20/LDI1apSQOAYtSuYWp8ZweqbHoxIB.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/patrickhand/PatrickHand-Regular.ttf",
        ],
    },
    "Indie_Flower": {
        "display": "Indie Flower",
        "emoji":   "🌸",
        "style":   "Bubbly Casual",
        "file":    "IndieFlower.ttf",
        "google":  "Indie+Flower",
        "urls": [
            "https://fonts.gstatic.com/s/indieflower/v21/m8JVjfNVeKWVnh3QMuKkFcZVaUr2.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/indieflower/IndieFlower.ttf",
        ],
    },
    "Shadows_Into_Light": {
        "display": "Shadows Into Light",
        "emoji":   "🌟",
        "style":   "Light Touch",
        "file":    "ShadowsIntoLight.ttf",
        "google":  "Shadows+Into+Light",
        "urls": [
            "https://fonts.gstatic.com/s/shadowsintolight/v19/UqyNK9UOIntux_czAvDQx_ZcHqZXBNQDcsr4xzSL.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/shadowsintolight/ShadowsIntoLight.ttf",
        ],
    },
    "Nothing_You_Could_Do": {
        "display": "Nothing You Could Do",
        "emoji":   "💭",
        "style":   "Dreamy Writing",
        "file":    "NothingYouCouldDo.ttf",
        "google":  "Nothing+You+Could+Do",
        "urls": [
            "https://fonts.gstatic.com/s/nothingyoucoulddo/v19/oY1B8fbBpaP5OX3DtrRYf_Q2BPB1SnfZb0OJl1ol.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/nothingyoucoulddo/NothingYouCouldDo.ttf",
        ],
    },
    "Covered_By_Your_Grace": {
        "display": "Covered By Your Grace",
        "emoji":   "💌",
        "style":   "Love Letter",
        "file":    "CoveredByYourGrace.ttf",
        "google":  "Covered+By+Your+Grace",
        "urls": [
            "https://fonts.gstatic.com/s/coveredbyyourgrace/v15/QGYwz-AZahWOJJI9kykWW9mD6opopoqXSOS0FgItq6bFIg.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/coveredbyyourgrace/CoveredByYourGrace.ttf",
        ],
    },
    "GloriaHallelujah": {
        "display": "Gloria Hallelujah",
        "emoji":   "✨",
        "style":   "Comic Style",
        "file":    "GloriaHallelujah.ttf",
        "google":  "Gloria+Hallelujah",
        "urls": [
            "https://fonts.gstatic.com/s/gloriahallelujah/v17/LYjYdHv3kUk9BMV96EIswT9DIbW-MLSy3TKEvkCF.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/gloriahallelujah/GloriaHallelujah.ttf",
        ],
    },
    "Architects_Daughter": {
        "display": "Architects Daughter",
        "emoji":   "📐",
        "style":   "Technical Draft",
        "file":    "ArchitectsDaughter.ttf",
        "google":  "Architects+Daughter",
        "urls": [
            "https://fonts.gstatic.com/s/architectsdaughter/v18/KtkxAKiDZI_td1Lkx62xHZHDtgO_Y-bvTYlg4-7.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/architectsdaughter/ArchitectsDaughter.ttf",
        ],
    },

    # ── Bold / Marker ──────────────────────────────────────────
    "Permanent_Marker": {
        "display": "Permanent Marker",
        "emoji":   "🖌️",
        "style":   "Bold Marker",
        "file":    "PermanentMarker-Regular.ttf",
        "google":  "Permanent+Marker",
        "urls": [
            "https://fonts.gstatic.com/s/permanentmarker/v16/Fh4uPib9Iyv2ucM6pGQMWimMp004La2Cfw.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/apache/permanentmarker/PermanentMarker-Regular.ttf",
        ],
    },
    "Rock_Salt": {
        "display": "Rock Salt",
        "emoji":   "🪨",
        "style":   "Rough Textured",
        "file":    "RockSalt-Regular.ttf",
        "google":  "Rock+Salt",
        "urls": [
            "https://fonts.gstatic.com/s/rocksalt/v22/MwQ2bhXp1eSBqjkPGJJRtGs-lbU.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/apache/rocksalt/RockSalt-Regular.ttf",
        ],
    },
    "Pacifico": {
        "display": "Pacifico",
        "emoji":   "🌊",
        "style":   "Bold Casual",
        "file":    "Pacifico-Regular.ttf",
        "google":  "Pacifico",
        "urls": [
            "https://fonts.gstatic.com/s/pacifico/v22/FwZY7-Qmy14u9lezJ96A4sijpFu_.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/pacifico/Pacifico-Regular.ttf",
        ],
    },

    # ── Extra Calligraphy ──────────────────────────────────────
    "Norican": {
        "display": "Norican",
        "emoji":   "🎭",
        "style":   "Italic Calligraphy",
        "file":    "Norican-Regular.ttf",
        "google":  "Norican",
        "urls": [
            "https://fonts.gstatic.com/s/norican/v15/MwQ2bhXp1eSBqjkPGJJRtGs-lbU.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/norican/Norican-Regular.ttf",
        ],
    },
    "Damion": {
        "display": "Damion",
        "emoji":   "🌀",
        "style":   "Fluid Script",
        "file":    "Damion-Regular.ttf",
        "google":  "Damion",
        "urls": [
            "https://fonts.gstatic.com/s/damion/v14/hv-XlzJ3KEsyZir7e7amYA.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/damion/Damion-Regular.ttf",
        ],
    },
    "Marck_Script": {
        "display": "Marck Script",
        "emoji":   "🎨",
        "style":   "Artistic Script",
        "file":    "MarckScript-Regular.ttf",
        "google":  "Marck+Script",
        "urls": [
            "https://fonts.gstatic.com/s/marckscript/v16/nwpTtK2oNgBA3Or78gapdwuyzRI.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/marckscript/MarckScript-Regular.ttf",
        ],
    },
    "Engagement": {
        "display": "Engagement",
        "emoji":   "💍",
        "style":   "Wedding Script",
        "file":    "Engagement-Regular.ttf",
        "google":  "Engagement",
        "urls": [
            "https://fonts.gstatic.com/s/engagement/v20/x3dkckHVYrCU5BU15c4BfPACvy761Q.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/engagement/Engagement-Regular.ttf",
        ],
    },
    "Euphoria_Script": {
        "display": "Euphoria Script",
        "emoji":   "🌺",
        "style":   "Romantic Script",
        "file":    "EuphoriaScript-Regular.ttf",
        "google":  "Euphoria+Script",
        "urls": [
            "https://fonts.gstatic.com/s/euphoriascript/v19/mFTpWb0X2bLajMM_CA0pSsxvrgBL.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/euphoriascript/EuphoriaScript-Regular.ttf",
        ],
    },
    "Italianno": {
        "display": "Italianno",
        "emoji":   "🇮🇹",
        "style":   "Italian Calligraphy",
        "file":    "Italianno-Regular.ttf",
        "google":  "Italianno",
        "urls": [
            "https://fonts.gstatic.com/s/italianno/v16/dg4n_p3sv6gCJkwzT6RXiZ0.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/italianno/Italianno-Regular.ttf",
        ],
    },
    "Qwitcher_Grypen": {
        "display": "Qwitcher Grypen",
        "emoji":   "🐉",
        "style":   "Gothic Calligraphy",
        "file":    "QwitcherGrypen-Regular.ttf",
        "google":  "Qwitcher+Grypen",
        "urls": [
            "https://fonts.gstatic.com/s/qwitchergrypen/v5/fC1jPY5JYWzbywv7c4V6UkKJtSuY.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/qwitchergrypen/QwitcherGrypen-Regular.ttf",
        ],
    },
    "Dr_Sugiyama": {
        "display": "Dr Sugiyama",
        "emoji":   "🎌",
        "style":   "Japanese-inspired",
        "file":    "DrSugiyama-Regular.ttf",
        "google":  "Dr+Sugiyama",
        "urls": [
            "https://fonts.gstatic.com/s/drsugiyama/v22/Ko05hz5iYxg-tzF1KY9uok7T6Q.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/drsugiyama/DrSugiyama-Regular.ttf",
        ],
    },
    "Rouge_Script": {
        "display": "Rouge Script",
        "emoji":   "💋",
        "style":   "Passionate Script",
        "file":    "RougeScript-Regular.ttf",
        "google":  "Rouge+Script",
        "urls": [
            "https://fonts.gstatic.com/s/rougescript/v16/LDIpaoiQNgArA8kR7ulhZ8P_w4s.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/rougescript/RougeScript-Regular.ttf",
        ],
    },
    "Clicker_Script": {
        "display": "Clicker Script",
        "emoji":   "⌨️",
        "style":   "Typewriter Script",
        "file":    "ClickerScript-Regular.ttf",
        "google":  "Clicker+Script",
        "urls": [
            "https://fonts.gstatic.com/s/clickerscript/v13/raxkHiKDdgtBKmhMBQBNEaJ2sRQ.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/clickerscript/ClickerScript-Regular.ttf",
        ],
    },
    "Kurale": {
        "display": "Kurale",
        "emoji":   "🔮",
        "style":   "Decorative Print",
        "file":    "Kurale-Regular.ttf",
        "google":  "Kurale",
        "urls": [
            "https://fonts.gstatic.com/s/kurale/v11/4iCs6KV9e9dXjhoKcQ72j00.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/kurale/Kurale-Regular.ttf",
        ],
    },
    "Amatic_SC": {
        "display": "Amatic SC",
        "emoji":   "🏷️",
        "style":   "Condensed Print",
        "file":    "AmaticSC-Regular.ttf",
        "google":  "Amatic+SC",
        "urls": [
            "https://fonts.gstatic.com/s/amaticsc/v26/TUZyzwprpvBS1izr_vO0De6ecZQf1A.ttf",
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/amaticsc/AmaticSC-Regular.ttf",
        ],
    },
}

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


class FontManager:
    def __init__(self, fonts_dir: Path):
        self.dir = Path(fonts_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    # ── Public ──────────────────────────────────────────────────

    def get_available_fonts(self) -> List[Dict]:
        result = []
        for key, info in FONTS.items():
            p = self.dir / info["file"]
            result.append({
                "key":       key,
                "display":   info["display"],
                "emoji":     info["emoji"],
                "style":     info["style"],
                "file":      info["file"],
                "google":    info.get("google", ""),
                "available": p.exists(),
            })
        return result

    def get_font_path(self, name: str) -> Optional[str]:
        if name not in FONTS:
            name = "Kalam"
        info = FONTS[name]
        p    = self.dir / info["file"]
        if not p.exists():
            self._download_one(name)
        if p.exists():
            return str(p)
        # fallback: any available font
        for k, v in FONTS.items():
            fp = self.dir / v["file"]
            if fp.exists():
                log.warning(f"Fallback font: {k}")
                return str(fp)
        return self._system_font()

    def ensure_fonts_downloaded(self) -> int:
        ok = 0
        for key in FONTS:
            p = self.dir / FONTS[key]["file"]
            if p.exists():
                ok += 1
            elif self._download_one(key):
                ok += 1
        log.info(f"Fonts ready: {ok}/{len(FONTS)}")
        return ok

    # ── Private ─────────────────────────────────────────────────

    def _download_one(self, key: str) -> bool:
        import requests
        info = FONTS[key]
        dest = self.dir / info["file"]

        for url in info["urls"]:
            try:
                log.info(f"  ⬇ {key} ← {url}")
                r = requests.get(url, headers=_HDR, timeout=20,
                                 allow_redirects=True, stream=False)
                if r.status_code == 200 and len(r.content) > 4096:
                    dest.write_bytes(r.content)
                    log.info(f"  ✅ {key} ({len(r.content)//1024} KB)")
                    return True
                log.warning(f"  ✗ {url} → HTTP {r.status_code} "
                            f"size={len(r.content)}")
            except Exception as e:
                log.warning(f"  ✗ {url} → {e}")
            time.sleep(0.2)

        log.error(f"  ❌ {key} download failed all URLs")
        return False

    @staticmethod
    def _system_font() -> Optional[str]:
        for p in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]:
            if os.path.exists(p):
                return p
        return None
