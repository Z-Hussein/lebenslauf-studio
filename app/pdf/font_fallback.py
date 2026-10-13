"""
Font-Fallback für Sonderzeichen im PDF.

Problem: Kein einzelner Font deckt alle Unicode-Zeichen ab (z. B. fehlen
✓ ★ ✔ in Arial/Calibri/Times). Zeichen ohne Glyphe erscheinen im PDF als
Kästchen (□). Dieses Modul erkennt solche Zeichen (via fontTools) und
bettet sie automatisch in einen Fallback-Font (Segoe UI Symbol, wird mit
der App in assets/fonts ausgeliefert) ein. Emoji ohne darstellbare Glyphe
werden durch lesbare Ersatztexte ersetzt statt als □ angezeigt.
"""

import os
import threading
from functools import lru_cache
from typing import Dict, List, Optional, Set

# Unter diesem Namen wird der Fallback-Font bei ReportLab registriert
FALLBACK_FONT_NAME = "SegoeUISymbol"

# Aktueller Primär-Font (TTF-Pfad) – wird vom PDFBuilder gesetzt
_primary_font_file: Optional[str] = None
_primary_cmap: Optional[Set[int]] = None

# Still entfernte Zeichen (Glyphe in keinem Font) – für Export-Warnungen
_dropped_lock = threading.Lock()
_dropped_chars: List[str] = []


def reset_dropped() -> None:
    """Setzt den Zähler entfernter Zeichen zurück (vor jedem PDF-Aufbau)."""
    with _dropped_lock:
        _dropped_chars.clear()


def pop_dropped() -> List[str]:
    """Holt und leert die seit reset_dropped() entfernten Zeichen."""
    with _dropped_lock:
        out = sorted(set(_dropped_chars))
        _dropped_chars.clear()
    return out


def _note_dropped(char: str) -> None:
    with _dropped_lock:
        if len(_dropped_chars) < 200:
            _dropped_chars.append(char)

# Ersetzungen für Emoji/Sonderzeichen ohne Glyphe in beiden Fonts
EMOJI_REPLACEMENTS: Dict[str, str] = {
    "📎": "",
    "📌": "",
    "📞": "Tel.",
    "☎": "Tel.",
    "✉": "E-Mail:",
    "📧": "E-Mail:",
    "📍": "",
    "🌐": "Web:",
    "🔗": "",
    "💻": "",
    "📱": "Tel.",
    "✅": "✓",
    "❎": "x",
    "❌": "x",
    "➕": "+",
    "➖": "-",
    "⭐": "★",
    "🌟": "★",
    "😀": "", "😁": "", "😂": "", "😊": "", "😉": "", "😍": "", "🤝": "", "👍": "", "👋": "",
    "🎓": "", "💼": "", "🏆": "", "🎯": "", "🚀": "", "💡": "", "🔧": "", "⚙": "",
}


def _load_cmap(path: str) -> Optional[Set[int]]:
    """Lädt das Zeichen-Repertoire einer TTF-Datei (None bei Fehler)."""
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(path, lazy=True)
        cmap = font.getBestCmap()
        font.close()
        return set(cmap.keys())
    except Exception:
        return None


def set_primary_font_file(path: Optional[str]) -> None:
    """Setzt den aktiven Primär-Font (wird bei jedem PDF-Aufbau gesetzt)."""
    global _primary_font_file, _primary_cmap
    if path == _primary_font_file:
        return
    _primary_font_file = path
    _primary_cmap = _load_cmap(path) if path else None


def _fallback_font_file() -> Optional[str]:
    """Sucht die SegoeUISymbol.ttf (erst assets, dann System)."""
    candidates = []
    try:
        from ..utils.helpers import FONTS_DIR
        candidates.append(os.path.join(FONTS_DIR, "SegoeUISymbol.ttf"))
    except Exception:
        pass
    candidates.append(r"C:\Windows\Fonts\seguisym.ttf")
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


@lru_cache(maxsize=1)
def _fallback_cmap() -> Optional[Set[int]]:
    path = _fallback_font_file()
    if not path:
        return None
    return _load_cmap(path)


@lru_cache(maxsize=1)
def ensure_fallback_registered() -> Optional[str]:
    """Registriert den Fallback-Font bei ReportLab. Gibt den Namen zurück."""
    path = _fallback_font_file()
    if not path:
        return None
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont(FALLBACK_FONT_NAME, path))
        return FALLBACK_FONT_NAME
    except Exception:
        return None


def _needs_fallback(char: str) -> bool:
    """True, wenn das Zeichen im Primär-Font fehlt (und Fallback nötig ist)."""
    code = ord(char)
    # ASCII + Steuerzeichen brauchen nie Fallback
    if code < 128:
        return False
    if _primary_cmap is None:
        # Ohne Info: nur bekannte problematische Bereiche behandeln
        return code > 0x2500 or char in EMOJI_REPLACEMENTS
    return code not in _primary_cmap


def rich_escape(text: str) -> str:
    """
    Maskiert XML-Sonderzeichen UND bettet Zeichen ohne Primär-Glyphe
    in den Fallback-Font ein. Ergebnis ist für ReportLab-Paragraphs gedacht.
    Zeichen ohne jede darstellbare Glyphe werden ersetzt/entfernt (nie □).
    """
    if not text:
        return ""
    text = str(text)
    fallback_name = ensure_fallback_registered()
    fb_cmap = _fallback_cmap() if fallback_name else None

    out: list = []
    open_tag = False
    for ch in text:
        # 1. Emoji-Ersetzungen zuerst
        if ch in EMOJI_REPLACEMENTS:
            repl = EMOJI_REPLACEMENTS[ch]
            if open_tag:
                out.append("</font>")
                open_tag = False
            out.append(repl.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            continue
        # 2. XML-Maskierung
        if ch == "&":
            esc = "&amp;"
        elif ch == "<":
            esc = "&lt;"
        elif ch == ">":
            esc = "&gt;"
        else:
            esc = ch
        # 3. Fallback nötig?
        if _needs_fallback(ch):
            code = ord(ch)
            if fb_cmap is not None and code in fb_cmap:
                if not open_tag:
                    out.append(f'<font name="{fallback_name}">')
                    open_tag = True
                out.append(esc)
            else:
                # In keinem Font darstellbar -> still entfernen (kein □),
                # aber für die Export-Warnung merken
                _note_dropped(ch)
                if open_tag:
                    out.append("</font>")
                    open_tag = False
                continue
        else:
            if open_tag:
                out.append("</font>")
                open_tag = False
            out.append(esc)
    if open_tag:
        out.append("</font>")
    return "".join(out)
