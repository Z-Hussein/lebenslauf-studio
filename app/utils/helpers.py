"""Hilfsfunktionen für die gesamte Anwendung."""

import os
import re
from typing import Optional

# Projekt-Root (Ordner, in dem main.py liegt)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")


def escape_xml(text: str) -> str:
    """
    Maskiert XML-Sonderzeichen für ReportLab-Paragraphs UND bettet
    Zeichen ohne Glyphe im aktiven Font automatisch in den
    Fallback-Font ein (keine □-Kästchen mehr).
    """
    if not text:
        return ""
    try:
        from ..pdf.font_fallback import rich_escape
        return rich_escape(text)
    except Exception:
        # Absoluter Fallback: reines Escaping ohne Font-Logik
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


def nl2br(text: str) -> str:
    """Ersetzt Zeilenumbrüche durch <br/> für Paragraph-Texte."""
    return escape_xml(text).replace("\n", "<br/>")


def safe_str(value: Optional[str]) -> str:
    """Gibt immer einen sauberen String zurück."""
    return value.strip() if isinstance(value, str) else ""


def is_valid_email(email: str) -> bool:
    """Sehr einfache E-Mail-Prüfung für Warnhinweise."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email or "") is not None


def hex_or(value: Optional[str], fallback: str = "#000000") -> str:
    """Validiert Hex-Farben, gibt bei Fehlern `fallback` zurück."""
    if not value:
        return fallback
    v = str(value).strip()
    if re.match(r"^#[0-9a-fA-F]{6}$", v):
        return v
    return fallback


def is_dark_color(hex_color: str) -> bool:
    """True, wenn die Farbe dunkel ist (relative Luminanz < 0,35)."""
    try:
        h = str(hex_color).strip().lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return lum < 0.35
    except Exception:
        return False


def lighten_color(hex_color: str, amount: float = 0.55) -> str:
    """Mischt die Farbe mit Weiß (amount 0..1) und gibt Hex zurück."""
    try:
        h = str(hex_color).strip().lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r = int(r + (255 - r) * amount)
        g = int(g + (255 - g) * amount)
        b = int(b + (255 - b) * amount)
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return str(hex_color)


def font_size_or(value: Any, fallback: float = 10.0) -> float:
    try:
        size = float(value)
        return min(14.0, max(7.0, size))
    except (TypeError, ValueError):
        return fallback


def spacing_or(value: Any, fallback: float, lo: float, hi: float) -> float:
    try:
        s = float(value)
        return min(hi, max(lo, s))
    except (TypeError, ValueError):
        return fallback


def unique_path(path: str) -> str:
    """Hängt ' (1)', ' (2)' ... an, falls der Pfad bereits existiert."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"
