"""
PDF-Generator mit ReportLab.

Erzeugt hochwertige A4-PDFs aus einem Resume-Datenobjekt und berücksichtigt
die ausgewählte Vorlage sowie die Design-Einstellungen des Benutzers.
"""

import io
import os
import re
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..models.resume import Resume
from ..models.section import (
    CertificateEntry,
    EducationEntry,
    ExperienceEntry,
    LanguageEntry,
    ListItemEntry,
    ProjectEntry,
    ReferenceEntry,
    SectionType,
    SkillEntry,
)
from ..templates import get_template
from ..utils.helpers import (
    escape_xml,
    font_size_or,
    hex_or,
    is_dark_color,
    lighten_color,
    nl2br,
    safe_str,
    spacing_or,
)

# ---------------------------------------------------------------------------
# Schriftarten: versuche eingebettete TrueType-Fonts (Windows-Systemfonts),
# falle ansonsten auf die eingebauten Base-14-Fonts zurück.
# ---------------------------------------------------------------------------

# Verfügbare Fonts: logischer Name -> (Dateien je Schnitt, Base14-Fallback)
# Wir probieren mehrere System-Schriften und Assets/fonts
_FONT_ALIASES = {
    "Helvetica": ({"regular": ["arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"],
                   "bold": ["arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"],
                   "italic": ["ariali.ttf", "LiberationSans-Italic.ttf", "DejaVuSans-Oblique.ttf"],
                   "bolditalic": ["arialbi.ttf", "LiberationSans-BoldItalic.ttf", "DejaVuSans-BoldOblique.ttf"]}, "Helvetica"),
    "Times-Roman": ({"regular": ["times.ttf", "times new roman.ttf", "LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"],
                     "bold": ["timesbd.ttf", "LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"],
                     "italic": ["timesi.ttf", "LiberationSerif-Italic.ttf", "DejaVuSerif-Italic.ttf"],
                     "bolditalic": ["timesbi.ttf", "LiberationSerif-BoldItalic.ttf", "DejaVuSerif-BoldItalic.ttf"]}, "Times-Roman"),
    "DejaVu Sans": ({"regular": ["DejaVuSans.ttf"], "bold": ["DejaVuSans-Bold.ttf"], "italic": ["DejaVuSans-Oblique.ttf"], "bolditalic": ["DejaVuSans-BoldOblique.ttf"]}, "Helvetica"),
    "Liberation Sans": ({"regular": ["LiberationSans-Regular.ttf"], "bold": ["LiberationSans-Bold.ttf"], "italic": ["LiberationSans-Italic.ttf"], "bolditalic": ["LiberationSans-BoldItalic.ttf"]}, "Helvetica"),
    "Calibri": ({"regular": ["calibri.ttf"], "bold": ["calibrib.ttf"], "italic": ["calibrii.ttf"], "bolditalic": ["calibriz.ttf"]}, "Helvetica"),
    "Segoe UI": ({"regular": ["segoeui.ttf"], "bold": ["segoeuib.ttf"], "italic": ["segoeuii.ttf"], "bolditalic": ["segoeuiz.ttf"]}, "Helvetica"),
    "Noto Sans": ({"regular": ["NotoSans-Regular.ttf"], "bold": ["NotoSans-Bold.ttf"], "italic": ["NotoSans-Italic.ttf"], "bolditalic": ["NotoSans-BoldItalic.ttf"]}, "Helvetica"),
    "Garamond": ({"regular": ["Garamond.ttf", "GARA.ttf", "EBGaramond-Regular.ttf"], "bold": ["Garamond-Bold.ttf", "GARABD.ttf"], "italic": ["Garamond-Italic.ttf", "GARAIT.ttf"], "bolditalic": ["Garamond-BoldItalic.ttf", "GARAIT.ttf"]}, "Times-Roman"),
    "JetBrains Mono": ({"regular": ["JetBrainsMono-Regular.ttf"], "bold": ["JetBrainsMono-Bold.ttf"], "italic": ["JetBrainsMono-Italic.ttf"], "bolditalic": ["JetBrainsMono-BoldItalic.ttf"]}, "Courier"),
    "Inter": ({"regular": ["Inter-Regular.ttf"], "bold": ["Inter-Bold.ttf"], "italic": ["Inter-Italic.ttf"], "bolditalic": ["Inter-BoldItalic.ttf"]}, "Helvetica"),
    "Consolas": ({"regular": ["Consolas.ttf", "consola.ttf"], "bold": ["Consolas-Bold.ttf", "consolab.ttf"], "italic": ["Consolas-Italic.ttf", "consolai.ttf"], "bolditalic": ["consolaz.ttf"]}, "Courier"),
}

_REGISTERED: Dict[str, Dict[str, str]] = {}

# Merkt sich die gefundene TTF-Datei je logischem Font (für Zeichenabdeckung)
_FONT_FILES: Dict[str, str] = {}


def primary_font_file(logical: str) -> Optional[str]:
    """Gibt die TTF-Datei des regulären Schnitts zurück (None wenn unbekannt)."""
    _register_fonts()
    return _FONT_FILES.get(logical)

# Kontakt-Icons (Unicode, optional per Setting icons_enabled)
# Für Base14-Helvetica verwenden wir PDF-sichere Text-Label statt Emoji,
# die mit Helvetica/WinAnsi nicht darstellbar wären (sonst □-Kästchen).
CONTACT_ICONS: Dict[str, str] = {
    "address": "Adr.",
    "phone": "Tel.",
    "email": "E-Mail:",
    "linkedin": "LinkedIn:",
    "website": "Web:",
    "github": "GitHub:",
}


def _find_font_file(candidates: List[str], search_dirs: List[str]) -> Optional[str]:
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for name in candidates:
            # case-insensitive Suche
            try:
                for entry in os.listdir(d):
                    if entry.lower() == name.lower():
                        return os.path.join(d, entry)
            except Exception:
                continue
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def _register_fonts() -> None:
    """Registriert TTF-Fonts, wenn sie auf dem System gefunden werden."""
    if _REGISTERED:
        return
    # zusätzliche Suche im Projekt assets/fonts
    from ..utils.helpers import FONTS_DIR  # lokaler Import um Zirkel zu vermeiden
    candidates_dir = [
        r"C:\Windows\Fonts",
        "/usr/share/fonts/truetype/msttcorefonts",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "/Library/Fonts",
        "/System/Library/Fonts",
        FONTS_DIR,
    ]
    for logical, (file_map, fallback) in _FONT_ALIASES.items():
        mapping: Dict[str, str] = {}
        reg_map = {
            f"{logical}": _find_font_file(file_map["regular"], candidates_dir),
            f"{logical}-Bold": _find_font_file(file_map["bold"], candidates_dir),
            f"{logical}-Italic": _find_font_file(file_map["italic"], candidates_dir),
            f"{logical}-BoldItalic": _find_font_file(file_map["bolditalic"], candidates_dir),
        }
        local_hits = {}
        for style_name, path in reg_map.items():
            if not path:
                continue
            try:
                pdfmetrics.registerFont(TTFont(style_name, path))
                local_hits[style_name] = style_name
                if style_name == logical:
                    _FONT_FILES[logical] = path
            except Exception:
                continue
        if local_hits:
            # Fehlende Schnitte ergänzen (Fallback auf regulär oder Base14)
            base = logical
            any_reg = next(iter(local_hits.values()))
            mapping.update(local_hits)
            mapping.setdefault(base, any_reg if any_reg else fallback)
            mapping.setdefault(f"{base}-Bold", local_hits.get(f"{base}-Bold", mapping[base]))
            mapping.setdefault(f"{base}-Italic", local_hits.get(f"{base}-Italic", mapping[base]))
            mapping.setdefault(f"{base}-BoldItalic", local_hits.get(f"{base}-BoldItalic", mapping[f"{base}-Bold"]))
            _REGISTERED[logical] = mapping


AVAILABLE_FONTS: List[str] = list(_FONT_ALIASES.keys())

def resolve_font(logical: str) -> Dict[str, str]:
    """Liefert {'regular','bold','italic','bold_italic'} Fontnamen für ReportLab."""
    _register_fonts()
    reg = _REGISTERED.get(logical)
    if reg:
        return {
            "regular": reg.get(logical, logical),
            "bold": reg.get(f"{logical}-Bold", f"{logical}-Bold"),
            "italic": reg.get(f"{logical}-Italic", f"{logical}-Italic"),
            "bold_italic": reg.get(f"{logical}-BoldItalic", f"{logical}-BoldItalic"),
        }
    # Base-14 Fallback
    if logical in ("Times-Roman", "Garamond"):
        return {"regular": "Times-Roman", "bold": "Times-Bold", "italic": "Times-Italic", "bold_italic": "Times-BoldItalic"}
    if logical in ("JetBrains Mono", "Consolas", "Courier"):
        # Monospace-Kette: registriertes Consolas nutzen, sonst Base14-Courier
        if "Consolas" in _REGISTERED:
            c = _REGISTERED["Consolas"]
            return {"regular": c.get("Consolas", "Courier"), "bold": c.get("Consolas-Bold", "Courier-Bold"),
                    "italic": c.get("Consolas-Italic", "Courier-Oblique"), "bold_italic": c.get("Consolas-BoldItalic", "Courier-BoldOblique")}
        return {"regular": "Courier", "bold": "Courier-Bold", "italic": "Courier-Oblique", "bold_italic": "Courier-BoldOblique"}
    return {"regular": "Helvetica", "bold": "Helvetica-Bold", "italic": "Helvetica-Oblique", "bold_italic": "Helvetica-BoldOblique"}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class PDFBuilder:
    """Baut den Story-Inhalt für eine Vorlage."""

    def __init__(self, resume: Resume):
        self.resume = resume
        self.style = get_template(resume.template)
        s = resume.settings

        self.is_zh = getattr(self.style, "origin", "") == "z-hussein.com" or self.style.title_style == "zh"
        self.is_terminal = (
            getattr(self.style, "dark_mode", False)
            or self.style.header_layout == "terminal"
            or self.style.title_style == "terminal"
        )
        if self.is_terminal:
            # Terminal: Akzent aus User-Setting (Mockup-Umschalter), Rest fix dunkel
            self.primary = colors.HexColor(hex_or(s.get("primary_color"), self.style.primary_color))
            self.secondary = colors.HexColor(hex_or(self.style.secondary_color, "#8C8472"))
            self.text_col = colors.HexColor(hex_or(self.style.text_color, "#E6DFCD"))
            self.body_col = colors.HexColor(hex_or(getattr(self.style, "body_color", "#C9C1AD"), "#C9C1AD"))
            accent_raw = s.get("accent_color") or self.style.primary_color
            self.accent = colors.HexColor(hex_or(accent_raw, self.style.primary_color))
            self.page_bg = colors.HexColor(hex_or(getattr(self.style, "page_background", "#0C0B09"), "#0C0B09"))
            self.frame_col = colors.HexColor(hex_or(getattr(self.style, "frame_color", "#2E2A22"), "#2E2A22"))
            self.titlebar_bg = colors.HexColor(hex_or(getattr(self.style, "titlebar_background", "#14120F"), "#14120F"))
            # Feste Terminal-Ränder (Rahmen + Innenabstand), unabhängig von Settings
            self.frame_inset = 9 * mm
            self.margin_left = 15 * mm
            self.margin_right = 15 * mm
            self.margin_top = 10.5 * mm
            self.margin_bottom = 15 * mm
        elif self.is_zh:
            # ZH-Vorlagen verwenden exakt die Website-Farben, unabhängig von gespeicherten Settings
            self.primary = colors.HexColor(hex_or(self.style.primary_color))
            self.secondary = colors.HexColor(hex_or(self.style.secondary_color))
            self.text_col = colors.HexColor(hex_or(self.style.text_color, "#222222"))
            accent_raw = getattr(self.style, "accent_color", "") or self.style.primary_color
            self.accent = colors.HexColor(hex_or(accent_raw, self.style.primary_color))
        else:
            self.primary = colors.HexColor(hex_or(s.get("primary_color"), self.style.primary_color))
            self.secondary = colors.HexColor(hex_or(s.get("secondary_color"), self.style.secondary_color))
            self.text_col = colors.HexColor(hex_or(self.style.text_color, "#222222"))
            self.body_col = self.text_col
            accent_raw = s.get("accent_color") or getattr(self.style, "accent_color", "") or self.style.primary_color
            self.accent = colors.HexColor(hex_or(accent_raw, self.style.primary_color))

        # Seitenhintergrund: bei ALLEN Vorlagen änderbar ("" = automatisch:
        # Dunkel bei Terminal, sonst Weiß). Textfarben folgen automatisch,
        # damit alles lesbar bleibt (dunkler Grund -> heller Text u. umgekehrt).
        self.dark_bg = False
        user_bg = safe_str(s.get("background_color"))
        if self.is_terminal:
            self.page_bg_hex = hex_or(user_bg, hex_or(getattr(self.style, "page_background", "#0C0B09"), "#0C0B09"))
            self.page_bg = colors.HexColor(self.page_bg_hex)
            if is_dark_color(self.page_bg_hex):
                self.dark_bg = True
            else:
                # Heller Grund im Terminal: dunkles Textschema (warme Grautöne)
                self.text_col = colors.HexColor("#201C15")
                self.body_col = colors.HexColor("#3D372C")
                self.secondary = colors.HexColor("#6E6656")
        else:
            self.page_bg_hex = hex_or(user_bg, "#FFFFFF")
            self.page_bg = colors.HexColor(self.page_bg_hex)
            if is_dark_color(self.page_bg_hex):
                self.dark_bg = True
                self.text_col = colors.HexColor("#E9E3D3")
                self.body_col = colors.HexColor("#D8D2C0")
                self.secondary = colors.HexColor("#A79F8D")
                if is_dark_color(self.primary.hexval()):
                    self.primary = colors.HexColor(lighten_color(self.primary.hexval(), 0.55))
                if is_dark_color(self.accent.hexval()):
                    self.accent = colors.HexColor(lighten_color(self.accent.hexval(), 0.55))

        self.icons_enabled = bool(s.get("icons_enabled", False))

        self.font_size = font_size_or(s.get("font_size"), 10.0)
        self.line_spacing = spacing_or(s.get("line_spacing"), 1.2, 1.0, 2.0)
        self.section_gap = spacing_or(s.get("section_spacing"), 8, 3, 24)

        if not self.is_terminal:
            self.margin_left = mm * float(spacing_or(s.get("margin_left"), 18, 10, 35))
            self.margin_right = mm * float(spacing_or(s.get("margin_right"), 18, 10, 35))
            self.margin_top = mm * float(spacing_or(s.get("margin_top"), 16, 10, 30))
            self.margin_bottom = mm * float(spacing_or(s.get("margin_bottom"), 16, 10, 30))

        fonts = resolve_font(self._logical_font())
        self.f_reg = fonts["regular"]
        self.f_bold = fonts["bold"]
        self.f_it = fonts["italic"]

        # Zeichenabdeckung für Sonderzeichen-Fallback bekanntgeben
        try:
            from .font_fallback import set_primary_font_file
            set_primary_font_file(primary_font_file(self._logical_font()))
        except Exception:
            pass

        self.content_width = A4[0] - self.margin_left - self.margin_right

        # Gesammelte Hinweise für den Export-Dialog (fehlende Dateien etc.)
        self.warnings: List[str] = []

        self.styles = self._build_styles()

    # -- Fonts ------------------------------------------------------------

    def _logical_font(self) -> str:
        requested = safe_str(self.resume.settings.get("font")) or self.style.font
        # Direkte Treffer aus AVAILABLE_FONTS
        if requested in AVAILABLE_FONTS:
            return requested
        if requested in ("Helvetica", "Arial", "Arial Unicode MS"):
            return "Helvetica"
        if requested.lower().startswith("times"):
            return "Times-Roman"
        # Fallback: normalize
        low = requested.lower()
        for cand in AVAILABLE_FONTS:
            if cand.lower() in low or low in cand.lower():
                return cand
        return "Helvetica"

    # -- Styles -----------------------------------------------------------

    def _build_styles(self) -> Dict[str, ParagraphStyle]:
        fs = self.font_size
        lead = fs * self.line_spacing
        st: Dict[str, ParagraphStyle] = {}

        # Minimal nutzt dunkles Grau/Schwarz für den Namen (schwarz/weiß-Look),
        # bei dunklem Hintergrund aber hell (Lesbarkeit)
        name_color = self.primary
        if self.style.name == "Classic":
            name_color = self.text_col
        elif self.style.name == "Minimal":
            name_color = self.text_col if self.dark_bg else colors.HexColor("#333333")
        # ZH-Vorlagen: Name groß (32px ≈ 24pt), kräftig pink/primär, immer zentriert
        if self.is_zh:
            st["name"] = ParagraphStyle(
                "Name", fontName=self.f_bold, fontSize=22, leading=24,
                textColor=self.primary,
                alignment=TA_CENTER,
                spaceAfter=1.2 * mm,
            )
            st["jobtitle"] = ParagraphStyle(
                "JobTitle", fontName=self.f_reg, fontSize=11, leading=13,
                textColor=self.secondary,
                alignment=TA_CENTER,
                spaceAfter=2 * mm,
            )
            st["contact"] = ParagraphStyle(
                "Contact", fontName=self.f_reg, fontSize=8.5, leading=10.5,
                textColor=self.secondary,
                alignment=TA_CENTER,
                spaceAfter=0,
            )
        else:
            st["name"] = ParagraphStyle(
                "Name", fontName=self.f_bold, fontSize=fs + 12, leading=(fs + 12) * 1.1,
                textColor=name_color,
                alignment=TA_LEFT if self.style.header_layout != "centered" else TA_CENTER,
                spaceAfter=1.5 * mm,
            )
            st["jobtitle"] = ParagraphStyle(
                "JobTitle", fontName=self.f_reg, fontSize=fs + 2, leading=lead,
                textColor=self.secondary,
                alignment=TA_LEFT if self.style.header_layout != "centered" else TA_CENTER,
                spaceAfter=2 * mm,
            )
            st["contact"] = ParagraphStyle(
                "Contact", fontName=self.f_reg, fontSize=fs - 1, leading=lead * 0.95,
                textColor=self.secondary,
                alignment=TA_LEFT if self.style.header_layout != "centered" else TA_CENTER,
            )

        if self.is_zh:
            # ZH: section-title 20px (≈14pt) bold primary, Linie 1px accent
            st["section"] = ParagraphStyle(
                "Section", fontName=self.f_bold, fontSize=13, leading=15,
                textColor=self.primary,
                alignment=TA_LEFT,
                spaceBefore=self.section_gap + 3, spaceAfter=1.2 * mm,
            )
        else:
            title_align = TA_LEFT
            title_bg = None
            title_pad_left = 0
            if self.style.title_style == "bar":
                title_bg = self.primary
                title_text_col = colors.white
                title_pad_left = 4
                title_fs = fs + 1
            else:
                title_text_col = self.primary if self.style.name != "Minimal" else self.secondary
                title_fs = fs + 1.5
            st["section"] = ParagraphStyle(
                "Section", fontName=self.f_bold, fontSize=title_fs,
                leading=title_fs * 1.25, textColor=title_text_col,
                alignment=title_align, backColor=title_bg,
                borderPadding=(3, 3, 3, title_pad_left),
                spaceBefore=self.section_gap + 2, spaceAfter=1.6 * mm,
            )

        # Terminal: Fließtext in body-Farbe (#C9C1AD), Überschriften hell
        bt = self.body_col if self.is_terminal else self.text_col
        st["entry_head"] = ParagraphStyle(
            "EntryHead", fontName=self.f_bold, fontSize=fs + 0.5, leading=lead,
            textColor=self.text_col, spaceBefore=1.2 * mm,
        )
        st["entry_sub"] = ParagraphStyle(
            "EntrySub", fontName=self.f_reg, fontSize=fs, leading=lead,
            textColor=bt,
        )
        st["date_right"] = ParagraphStyle(
            "DateRight", fontName=self.f_it, fontSize=fs - 0.5, leading=lead,
            textColor=self.secondary, alignment=TA_RIGHT,
        )
        st["body"] = ParagraphStyle(
            "Body", fontName=self.f_reg, fontSize=fs, leading=lead,
            textColor=bt, spaceAfter=0.8 * mm, alignment=TA_LEFT,
        )
        st["bullet"] = ParagraphStyle(
            "Bullet", fontName=self.f_reg, fontSize=fs, leading=lead,
            textColor=bt, leftIndent=5 * mm, bulletIndent=1.2 * mm,
            spaceAfter=0.4 * mm,
        )
        if self.is_terminal:
            # Terminal-Kopf: Name groß in Akzent, Prompt-Zeilen, Cursor
            st["term_name"] = ParagraphStyle(
                "TermName", fontName=self.f_bold, fontSize=23, leading=24,
                textColor=self.primary, spaceBefore=1 * mm, spaceAfter=1 * mm,
            )
            st["term_prompt"] = ParagraphStyle(
                "TermPrompt", fontName=self.f_reg, fontSize=8.5, leading=11,
                textColor=bt, spaceBefore=2.5 * mm, spaceAfter=1 * mm,
            )
            st["term_title"] = ParagraphStyle(
                "TermTitle", fontName=self.f_reg, fontSize=8.5, leading=11,
                textColor=self.secondary, spaceAfter=0,
            )
        st["small"] = ParagraphStyle(
            "Small", fontName=self.f_reg, fontSize=fs - 1, leading=lead * 0.9,
            textColor=self.secondary,
        )
        return st

    # -- Hilfen -------------------------------------------------------------

    def _rule(self, color: Optional[colors.Color] = None, width_mm: float = 0.7) -> Table:
        col = color if color is not None else self.primary
        t = Table([[""]], colWidths=[self.content_width], rowHeights=[width_mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), col),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return t

    # Terminal-Kommandos je Abschnittstyp (Mockup: $ whoami, $ git log, ...)
    TERMINAL_COMMANDS = {
        "profil": "cat profil.md",
        "berufserfahrung": "git log --graph erfahrung",
        "ausbildung": "git log --graph bildung",
        "kenntnisse": "cat skills.yaml",
        "sprachen": "ls -l sprachen/",
        "zertifikate": "ls -l zertifikate/",
        "projekte": "ls -l projekte/",
        "praktika": "git log --graph praktika",
        "ehrenamt": "cat ehrenamt.md",
        "publikationen": "cat publikationen.md",
        "auszeichnungen": "cat awards.md",
        "kurse": "cat kurse.md",
        "konferenzen": "cat konferenzen.md",
        "interessen": "cat interessen.txt",
        "referenzen": "cat referenzen.txt",
    }

    def _terminal_command(self, section: Dict[str, Any]) -> str:
        stype = str(section.get("type", ""))
        if stype == SectionType.CUSTOM.value:
            slug = re.sub(r"[^a-z0-9]+", "-", safe_str(section.get("title") or "abschnitt").lower()).strip("-")
            return f"cat {slug or 'abschnitt'}.md"
        return self.TERMINAL_COMMANDS.get(stype, "cat abschnitt.md")

    def _prompt(self, command: str) -> Paragraph:
        """Eine Terminal-Promptzeile: `$ command` ($ in Akzent)."""
        return Paragraph(
            f'<font color="{self.primary.hexval()}">$</font> {escape_xml(command)}',
            self.styles["term_prompt"],
        )

    def _accent(self, text: str) -> str:
        """Färbt bereits maskierten Text in Akzentfarbe."""
        return f'<font color="{self.primary.hexval()}">{text}</font>'

    def _muted(self, text: str) -> str:
        """Färbt bereits maskierten Text in gedämpftem Grau."""
        return f'<font color="{self.secondary.hexval()}">{text}</font>'

    def _section_title(self, title: str) -> List[Any]:
        """Gibt die Fluss-Elemente für einen Abschnittstitel zurück."""
        out: List[Any] = []
        if self.is_terminal:
            # Terminal: kein Titeltext nötig (Kommando kommt vom Renderer)
            return out
        if self.is_zh:
            # ZH: exakt wie Website: 20px bold primary, Linie 1px accent, 5px Abstand
            out.append(Paragraph(escape_xml(title), self.styles["section"]))
            out.append(self._rule(self.accent, 0.35))
            out.append(Spacer(1, 1.0 * mm))
            return out
        if self.style.title_style in ("caps", "bar"):
            # Großschreibung VOR dem Escaping, sonst werden Entities/Tags zerstört
            label = escape_xml(title.upper())
        else:
            label = escape_xml(title)
        out.append(Paragraph(label, self.styles["section"]))
        if self.style.title_style == "line":
            out.append(self._rule(self.primary, 0.6))
            out.append(Spacer(1, 1.2 * mm))
        elif self.style.title_style == "underline":
            out.append(self._rule(colors.HexColor("#999999"), 0.4))
            out.append(Spacer(1, 1.2 * mm))
        elif self.style.title_style == "bar":
            out.append(Spacer(1, 1.2 * mm))
        else:  # caps / minimal
            out.append(Spacer(1, 0.6 * mm))
        return out

    def _photo_flowable(self, width_mm_: float, height_mm_: float) -> Optional[Image]:
        path = safe_str(self.resume.personal.get("photo"))
        if not path:
            return None
        if not os.path.exists(path):
            self.warnings.append(
                f"Bewerbungsfoto nicht gefunden und weggelassen:\n{path}"
            )
            return None
        try:
            img = Image(path, width=width_mm_ * mm, height=height_mm_ * mm)
            # Seitenverhältnis beibehalten (in den Rahmen einpassen)
            iw, ih = img.imageWidth, img.imageHeight
            if iw > 0 and ih > 0:
                ratio = min(width_mm_ * mm / iw, height_mm_ * mm / ih)
                img.drawWidth = iw * ratio
                img.drawHeight = ih * ratio
            return img
        except Exception:
            return None

    # -- Header-Varianten ---------------------------------------------------

    def build_header(self, story: List[Any]) -> None:
        p = self.resume.personal
        name = escape_xml(self.resume.full_name()) or escape_xml(safe_str(p.get("name")))
        title_txt = escape_xml(safe_str(p.get("title")))
        contact_items = []
        address_parts = [safe_str(p.get("address")), safe_str(p.get("postal_code")), safe_str(p.get("city")), safe_str(p.get("country"))]
        address_line = ", ".join([a for a in address_parts if a])
        if address_line:
            prefix = (CONTACT_ICONS["address"] + " ") if self.icons_enabled else ""
            contact_items.append(prefix + escape_xml(address_line))
        for key in ("phone", "email", "linkedin", "website", "github"):
            v = safe_str(p.get(key))
            if v:
                prefix = (CONTACT_ICONS.get(key, "") + " ") if self.icons_enabled else ""
                contact_items.append(prefix + escape_xml(v))
        optional_items = []
        for key, label in (("birth_date", "Geboren"), ("nationality", "Staatsangehörigkeit")):
            v = safe_str(p.get(key))
            if v:
                optional_items.append(f"{label}: {escape_xml(v)}")

        layout = self.style.header_layout

        # Terminal-Header: Titelleiste, `$ whoami`, Name groß in Akzent, Titel grau, Foto rechts
        if self.is_terminal:
            first = safe_str(p.get("first_name")) or "bewerber"
            user = re.sub(r"[^a-z0-9]+", "", first.lower()) or "bewerber"
            dots = (
                f'<font color="#3A352B">● ●</font> '
                f'<font color="{self.primary.hexval()}">●</font>'
                f'&nbsp;&nbsp;&nbsp;<font color="{self.secondary.hexval()}">'
                f'{escape_xml(user)}@terminal: ~/lebenslauf</font>'
            )
            bar = Table(
                [[Paragraph(dots, ParagraphStyle(
                    "TermBar", parent=self.styles["body"], fontSize=7.5, leading=10,
                    textColor=self.secondary, spaceAfter=0, spaceBefore=0))]],
                colWidths=[self.content_width],
            )
            bar.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.titlebar_bg),
                ("LINEBELOW", (0, 0), (-1, -1), 0.6, self.frame_col),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.append(bar)
            story.append(Spacer(1, 4 * mm))
            left: List[Any] = [self._prompt("whoami")]
            if name:
                left.append(Paragraph(name, self.styles["term_name"]))
            if title_txt:
                left.append(Paragraph(title_txt, self.styles["term_title"]))
            photo = self._photo_flowable(26, 32)
            if photo is not None:
                tbl = Table([[left, photo]], colWidths=[self.content_width - 30 * mm, 30 * mm])
                tbl.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                    ("BOX", (1, 0), (1, 0), 0.4, self.secondary),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                story.append(tbl)
            else:
                for fl in left:
                    story.append(fl)
            story.append(Spacer(1, 1.5 * mm))
            return

        # ZH-Header hat Vorrang: exakter Nachbau der Website (zentriert, Avatar oben, 2px primary Linie)
        if self.is_zh:
            photo = self._photo_flowable(26, 26)
            if photo is not None:
                # Avatar mit 3px-Rahmen simulieren (eingefasste Tabelle)
                inner = Table([[photo]], colWidths=[26 * mm], rowHeights=[26 * mm])
                inner.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                    ("BOX", (0, 0), (-1, -1), 1.0, self.primary),
                ]))
                outer = Table([[inner]], colWidths=[self.content_width])
                outer.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(outer)
            if name:
                story.append(Paragraph(name, self.styles["name"]))
            if title_txt:
                story.append(Paragraph(title_txt, self.styles["jobtitle"]))
            if contact_items:
                # Website nutzt " | " als Trenner
                story.append(Paragraph(" | ".join(contact_items[:6]), self.styles["contact"]))
            if optional_items:
                story.append(Spacer(1, 0.8 * mm))
                story.append(Paragraph(" | ".join(optional_items), self.styles["contact"]))
            story.append(Spacer(1, 3 * mm))
            story.append(self._rule(self.primary, 0.7))
            story.append(Spacer(1, 3 * mm))
            return

        if layout == "centered":
            # Classic: alles zentriert untereinander
            if name:
                story.append(Paragraph(name, self.styles["name"]))
            if title_txt:
                story.append(Paragraph(title_txt, self.styles["jobtitle"]))
            if contact_items:
                story.append(Paragraph(" · ".join(contact_items), self.styles["contact"]))
            if optional_items:
                story.append(Spacer(1, 0.8 * mm))
                story.append(Paragraph(" · ".join(optional_items), self.styles["contact"]))
            story.append(Spacer(1, 2 * mm))
            _classic_rule = self.secondary if self.dark_bg else colors.HexColor("#333333")
            story.append(self._rule(_classic_rule, 0.8))
            story.append(Spacer(1, 2 * mm))

        elif layout == "left":
            # Modern: Name links, Foto rechts
            left: List[Any] = []
            if name:
                left.append(Paragraph(name, self.styles["name"]))
            if title_txt:
                left.append(Paragraph(title_txt, self.styles["jobtitle"]))
            if contact_items:
                left.append(Paragraph("<br/>".join(contact_items), self.styles["contact"]))

            photo = self._photo_flowable(28, 34)
            if photo is not None:
                tbl = Table([[left, photo]], colWidths=[self.content_width - 32 * mm, 32 * mm])
            else:
                tbl = Table([[left]], colWidths=[self.content_width])
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 2 * mm))
            _rule_col = colors.HexColor("#BBBBBB") if self.style.name == "Minimal" else self.primary
            story.append(self._rule(_rule_col, 1.0))
            story.append(Spacer(1, 1.5 * mm))

        elif layout == "split":
            # Professional: Foto rechts, Kontakt zweispaltig
            photo = self._photo_flowable(30, 36)
            left_width = self.content_width - (34 * mm if photo is not None else 0)
            left: List[Any] = []
            if name:
                left.append(Paragraph(name, self.styles["name"]))
            if title_txt:
                left.append(Paragraph(title_txt, self.styles["jobtitle"]))
            if contact_items:
                half = (len(contact_items) + 1) // 2
                col_a = "<br/>".join(contact_items[:half])
                col_b = "<br/>".join(contact_items[half:])
                inner = Table([[Paragraph(col_a, self.styles["small"]), Paragraph(col_b, self.styles["small"])]],
                              colWidths=[left_width / 2] * 2)
                inner.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "LEFT"),
                ]))
                left.append(inner)

            if photo is not None:
                tbl = Table([[left, photo]], colWidths=[left_width, 34 * mm])
            else:
                tbl = Table([[left]], colWidths=[left_width])
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 2 * mm))
            story.append(self._rule(self.primary, 1.4))
            story.append(Spacer(1, 1.5 * mm))

        else:  # two_column -> Creative-Karte (auch ohne Foto als farbiger Header)
            card_inner: List[Any] = []
            if name:
                card_inner.append(Paragraph(name, self.styles["name"]))
            if title_txt:
                card_inner.append(Paragraph(title_txt, self.styles["jobtitle"]))
            if contact_items:
                card_inner.append(Paragraph("<br/>".join(contact_items[:6]), self.styles["contact"]))
            photo = self._photo_flowable(26, 26)
            if photo is not None:
                tbl = Table([[photo, card_inner]], colWidths=[30 * mm, self.content_width - 30 * mm])
                tbl.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                    ("VALIGN", (1, 0), (1, 0), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
            else:
                tbl = Table([[card_inner]], colWidths=[self.content_width - 8])
                tbl.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                boxed = Table([[tbl]], colWidths=[self.content_width])
                boxed.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(hex_or(self.style.sidebar_background, "#EAF4F4"))),
                    ("LINEBEFORE", (0, 0), (0, -1), 3, self.primary),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]))
                story.append(boxed)
            story.append(Spacer(1, 3 * mm))

    # -- Abschnitts-Renderer ---------------------------------------------

    def render_section(self, story: List[Any], section: Dict[str, Any]) -> None:
        stype = section.get("type", "")
        title = safe_str(section.get("title")) or "Abschnitt"
        data = section.get("data", {}) or {}

        if self.is_terminal:
            self._render_terminal_section(story, section, stype, data)
            return

        if stype == SectionType.PROFILE.value:
            content = safe_str(data.get("content", ""))
            if not content:
                return
            head = self._section_title(title)
            body = Paragraph(nl2br(content), self.styles["body"])
            story.append(KeepTogether(head + [body]))

        elif stype == SectionType.EXPERIENCE.value:
            entries = [ExperienceEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.position or e.company]
            if not entries:
                return
            blocks: List[Any] = self._section_title(title)
            for e in entries:
                blocks.extend(self._experience_block(e))
            story.extend(blocks)

        elif stype == SectionType.EDUCATION.value:
            entries = [EducationEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.degree or e.institution]
            if not entries:
                return
            blocks: List[Any] = self._section_title(title)
            for e in entries:
                blocks.extend(self._education_block(e))
            story.extend(blocks)

        elif stype == SectionType.SKILLS.value:
            skills = [SkillEntry.from_dict(x) for x in data.get("skills", [])]
            skills = [s for s in skills if s.name]
            if not skills:
                return
            blocks: List[Any] = self._section_title(title)
            blocks.extend(self._skills_content(skills))
            story.extend(blocks)

        elif stype == SectionType.LANGUAGES.value:
            langs = [LanguageEntry.from_dict(x) for x in data.get("languages", [])]
            langs = [l for l in langs if l.name]
            if not langs:
                return
            blocks: List[Any] = self._section_title(title)
            parts = [f"<b>{escape_xml(l.name)}</b>" + (f" – {escape_xml(l.level)}" if l.level else "") for l in langs]
            sep = "<br/>" if self.style.date_style == "right" else " · "
            blocks.append(Paragraph(sep.join(parts), self.styles["body"]))
            story.extend(blocks)

        elif stype == SectionType.CERTIFICATES.value:
            entries = [CertificateEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.name]
            if not entries:
                return
            blocks: List[Any] = self._section_title(title)
            for c in entries:
                txt = f"<b>{escape_xml(c.name)}</b>"
                sub = " – ".join([x for x in (c.issuer, c.year) if x])
                if sub:
                    txt += f" – {escape_xml(sub)}"
                blocks.append(Paragraph(txt, self.styles["body"]))
                if c.description:
                    blocks.append(Paragraph(escape_xml(c.description), self.styles["small"]))
            story.extend(blocks)

        elif stype == SectionType.PROJECTS.value:
            entries = [ProjectEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.name]
            if not entries:
                return
            blocks: List[Any] = self._section_title(title)
            for pr in entries:
                head = f"<b>{escape_xml(pr.name)}</b>"
                subs = [x for x in (pr.role, pr.period) if x]
                if subs:
                    head += f" – {escape_xml(' · '.join(subs))}"
                blocks.append(Paragraph(head, self.styles["entry_head"]))
                if pr.description:
                    blocks.append(Paragraph(nl2br(pr.description), self.styles["body"]))
                if pr.technologies:
                    tech = ", ".join(escape_xml(t) for t in pr.technologies if safe_str(t))
                    if tech:
                        blocks.append(Paragraph(f"Technologien: {tech}", self.styles["small"]))
                blocks.append(Spacer(1, 1 * mm))
            story.extend(blocks)

        elif stype in (
            SectionType.PRACTICA.value,
            SectionType.VOLUNTEER.value,
            SectionType.PUBLICATIONS.value,
            SectionType.AWARDS.value,
            SectionType.COURSES.value,
            SectionType.CONFERENCES.value,
        ):
            entries = [ListItemEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.title]
            if not entries:
                return
            blocks: List[Any] = self._section_title(title)
            for it in entries:
                head = f"<b>{escape_xml(it.title)}</b>"
                if it.subtitle:
                    head += f" – {escape_xml(it.subtitle)}"
                meta = " · ".join([x for x in (it.period,) if x])
                blocks.append(Paragraph(head, self.styles["body"]))
                if meta:
                    blocks.append(Paragraph(meta, self.styles["small"]))
                if it.description:
                    blocks.append(Paragraph(nl2br(it.description), self.styles["body"]))
                blocks.append(Spacer(1, 0.8 * mm))
            story.extend(blocks)

        elif stype == SectionType.INTERESTS.value:
            items = [safe_str(i) for i in data.get("items", []) if safe_str(i)]
            if not items:
                return
            blocks: List[Any] = self._section_title(title)
            blocks.append(Paragraph(" · ".join(escape_xml(i) for i in items), self.styles["body"]))
            story.extend(blocks)

        elif stype == SectionType.REFERENCES.value:
            entries = [ReferenceEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.name]
            if not entries:
                return
            blocks: List[Any] = self._section_title(title)
            for r in entries:
                txt = f"<b>{escape_xml(r.name)}</b>"
                if r.position_company:
                    txt += f"<br/>{escape_xml(r.position_company)}"
                if r.contact:
                    txt += f"<br/>{escape_xml(r.contact)}"
                blocks.append(Paragraph(txt, self.styles["body"]))
                blocks.append(Spacer(1, 0.8 * mm))
            story.extend(blocks)

        else:  # CUSTOM oder unbekannt -> freier Textabschnitt
            content = safe_str(data.get("content", ""))
            if not content:
                return
            head = self._section_title(title)
            body = Paragraph(nl2br(content), self.styles["body"])
            story.append(KeepTogether(head + [body]))

    # -- Terminal-Renderer (Mockup Stil 3) ----------------------------------

    def _term_graph(self, marker: str, text: str) -> Paragraph:
        """Eine git-log-ähnliche Zeile: akzentfarbenes `*`/`|` + Inhalt."""
        return Paragraph(
            f"{self._accent(escape_xml(marker))}   {text}",
            self.styles["body"],
        )

    @staticmethod
    def _level_percent(level: str) -> Optional[int]:
        """Extrahiert Prozent aus Level-Text wie '80 %' oder '75%'."""
        m = re.search(r"(\d{1,3})\s*%", level or "")
        if not m:
            return None
        try:
            return max(0, min(100, int(m.group(1))))
        except ValueError:
            return None

    @staticmethod
    def _level_bar(percent: int) -> str:
        """Block-Balken wie im Mockup: ███████▌░░ + Prozent."""
        full = percent // 10
        half = 1 if (percent % 10) >= 5 and full < 10 else 0
        empty = 10 - full - half
        return "█" * full + "▌" * half + "░" * empty

    def _render_terminal_section(self, story: List[Any], section: Dict[str, Any],
                                 stype: str, data: Dict[str, Any]) -> None:
        story.append(self._prompt(self._terminal_command(section)))
        story.append(Spacer(1, 1 * mm))

        if stype == SectionType.PROFILE.value:
            content = safe_str(data.get("content", ""))
            if not content:
                return
            story.append(Paragraph(nl2br(content), self.styles["body"]))

        elif stype in (SectionType.EXPERIENCE.value, SectionType.EDUCATION.value,
                       SectionType.PRACTICA.value):
            entries = [ExperienceEntry.from_dict(e) if stype != SectionType.EDUCATION.value
                       else EducationEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if getattr(e, "position", None) or getattr(e, "degree", None)
                       or getattr(e, "company", None) or getattr(e, "institution", None)]
            if not entries:
                return
            for e in entries:
                if isinstance(e, EducationEntry):
                    head = escape_xml(e.degree)
                    meta = " · ".join([x for x in (e.institution, e.location) if x])
                    if e.grade:
                        meta = (meta + " · " if meta else "") + f"Note {e.grade}"
                    period = e.period_text()
                    desc = e.description
                    bullets = []
                else:
                    head = escape_xml(e.position)
                    meta = " · ".join([x for x in (e.company, e.location) if x])
                    period = e.period_text()
                    desc = e.description
                    bullets = [a for a in e.achievements if safe_str(a)]
                story.append(Paragraph(
                    f"{self._accent('*')} {self._muted(escape_xml(period))}  <b>{head}</b>",
                    self.styles["body"],
                ))
                if meta:
                    story.append(self._term_graph("|", escape_xml(meta)))
                if desc:
                    for line in [ln for ln in desc.splitlines() if ln.strip()]:
                        story.append(self._term_graph("|", escape_xml(line.strip())))
                for b in bullets:
                    story.append(self._term_graph("|", "+ " + escape_xml(safe_str(b))))
                story.append(Spacer(1, 1 * mm))

        elif stype == SectionType.SKILLS.value:
            skills = [SkillEntry.from_dict(x) for x in data.get("skills", [])]
            skills = [s for s in skills if s.name]
            if not skills:
                return
            categorized: Dict[str, List[str]] = {}
            uncategorized: List[str] = []
            for s in skills:
                (categorized.setdefault(s.category, []).append(s.name) if s.category
                 else uncategorized.append(s.name))
            if uncategorized:
                categorized.setdefault("sonstige", []).extend(uncategorized)
            for cat, names in categorized.items():
                story.append(Paragraph(
                    f"{self._accent(escape_xml(cat) + ':')} [{escape_xml(', '.join(names))}]",
                    self.styles["body"],
                ))
            # Level-Balken wie `./level --top`, wenn %-Level vorhanden
            leveled = [(s.name, self._level_percent(s.level)) for s in skills
                       if self._level_percent(s.level) is not None]
            if leveled:
                story.append(Spacer(1, 1.5 * mm))
                story.append(self._prompt("./level --top"))
                story.append(Spacer(1, 1 * mm))
                for name, pct in leveled[:8]:
                    # Nur auffüllen, nie abschneiden (lange Namen verschieben nur diese Zeile)
                    label = (name + " " * max(0, 13 - len(name))).replace(" ", "\u00a0")
                    story.append(Paragraph(
                        f"{escape_xml(label)} {self._accent(escape_xml(self._level_bar(pct)))}  {pct}%",
                        self.styles["body"],
                    ))

        elif stype == SectionType.LANGUAGES.value:
            langs = [LanguageEntry.from_dict(x) for x in data.get("languages", [])]
            langs = [l for l in langs if l.name]
            if not langs:
                return
            parts = [f"{escape_xml(l.name)} {self._muted('[' + escape_xml(l.level) + ']' if l.level else '')}"
                     for l in langs]
            story.append(Paragraph(" · ".join(parts), self.styles["body"]))

        elif stype == SectionType.CERTIFICATES.value:
            entries = [CertificateEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.name]
            if not entries:
                return
            for c in entries:
                line = f"<b>{escape_xml(c.name)}</b>"
                if c.year:
                    line += f" {self._muted('[' + escape_xml(c.year) + ']')}"
                story.append(Paragraph(line, self.styles["body"]))
                if c.issuer:
                    story.append(self._term_graph("|", self._muted(escape_xml(c.issuer))))
                if c.description:
                    story.append(self._term_graph("|", escape_xml(c.description)))

        elif stype == SectionType.PROJECTS.value:
            entries = [ProjectEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.name]
            if not entries:
                return
            for pr in entries:
                story.append(Paragraph(f"<b>{escape_xml(pr.name)}</b>", self.styles["body"]))
                subs = [x for x in (pr.role, pr.period) if x]
                if subs:
                    story.append(self._term_graph("|", self._muted(escape_xml(" · ".join(subs)))))
                if pr.technologies:
                    tech = ", ".join(escape_xml(t) for t in pr.technologies if safe_str(t))
                    if tech:
                        story.append(self._term_graph("|", self._muted(escape_xml("[" + tech + "]"))))
                if pr.description:
                    for line in [ln for ln in pr.description.splitlines() if ln.strip()]:
                        story.append(self._term_graph("|", escape_xml(line.strip())))
                story.append(Spacer(1, 1 * mm))

        elif stype in (SectionType.VOLUNTEER.value, SectionType.PUBLICATIONS.value,
                       SectionType.AWARDS.value, SectionType.COURSES.value,
                       SectionType.CONFERENCES.value):
            entries = [ListItemEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.title]
            if not entries:
                return
            for it in entries:
                story.append(Paragraph(
                    f"{self._accent('*')} <b>{escape_xml(it.title)}</b>",
                    self.styles["body"],
                ))
                meta = " · ".join([x for x in (it.subtitle, it.period) if x])
                if meta:
                    story.append(self._term_graph("|", escape_xml(meta)))
                if it.description:
                    story.append(self._term_graph("|", escape_xml(it.description)))

        elif stype == SectionType.INTERESTS.value:
            items = [safe_str(i) for i in data.get("items", []) if safe_str(i)]
            if not items:
                return
            story.append(Paragraph(" · ".join(escape_xml(i) for i in items), self.styles["body"]))

        elif stype == SectionType.REFERENCES.value:
            entries = [ReferenceEntry.from_dict(e) for e in data.get("entries", [])]
            entries = [e for e in entries if e.name]
            if not entries:
                return
            for r in entries:
                line = f"<b>{escape_xml(r.name)}</b>"
                if r.position_company:
                    line += f" {self._muted('[' + escape_xml(r.position_company) + ']')}"
                story.append(Paragraph(line, self.styles["body"]))
                if r.contact:
                    story.append(self._term_graph("|", escape_xml(r.contact)))

        else:  # CUSTOM oder unbekannt
            content = safe_str(data.get("content", ""))
            if not content:
                return
            story.append(Paragraph(nl2br(content), self.styles["body"]))

    def build_terminal_footer(self, story: List[Any]) -> None:
        """`$ echo $KONTAKT`-Block + Cursor am Ende (Mockup)."""
        p = self.resume.personal
        rows = []
        email = safe_str(p.get("email"))
        phone = safe_str(p.get("phone"))
        city = " ".join([x for x in (safe_str(p.get("postal_code")), safe_str(p.get("city"))) if x])
        github = safe_str(p.get("github"))
        linkedin = safe_str(p.get("linkedin"))
        website = safe_str(p.get("website"))
        if email:
            rows.append(("mail", email))
        if phone:
            rows.append(("tel", phone))
        if city:
            rows.append(("ort", city))
        if github:
            rows.append(("github", github))
        if linkedin:
            rows.append(("linkedin", linkedin))
        if website:
            rows.append(("web", website))
        if rows:
            story.append(self._prompt("echo $KONTAKT"))
            story.append(Spacer(1, 1 * mm))
            for label, value in rows:
                pad = label + "\u00a0" * max(1, 9 - len(label))
                story.append(Paragraph(
                    f"{escape_xml(pad)}{escape_xml(value)}",
                    self.styles["body"],
                ))
            story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f'{self._accent("$")} {self._accent("█")}',
            self.styles["body"],
        ))

    # -- Einzelne Blöcke ----------------------------------------------------

    def _experience_block(self, e: ExperienceEntry) -> List[Any]:
        out: List[Any] = []
        heading = f"<b>{escape_xml(e.position)}</b>"
        if self.style.date_style == "inline":
            meta_bits = [x for x in (e.company, e.location, e.period_text()) if x]
            if meta_bits:
                heading += f'<font size="{self.font_size - 1}" color="{self.style.secondary_color}">  ·  ' + escape_xml(" · ".join(meta_bits)) + "</font>"
            out.append(Paragraph(heading, self.styles["entry_head"]))
        else:
            out.append(Paragraph(heading, self.styles["entry_head"]))
            meta_bits = [x for x in (e.company, e.location) if x]
            if meta_bits or e.period_text():
                row = Table(
                    [[Paragraph(escape_xml(" · ".join(meta_bits)), self.styles["entry_sub"]),
                      Paragraph(escape_xml(e.period_text()), self.styles["date_right"])]],
                    colWidths=[self.content_width * 0.62, self.content_width * 0.38],
                )
                row.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                out.append(row)
        if e.description:
            out.append(Paragraph(nl2br(e.description), self.styles["body"]))
        for ach in e.achievements:
            a = safe_str(ach)
            if a:
                out.append(Paragraph(escape_xml(a), self.styles["bullet"], bulletText="•"))
        out.append(Spacer(1, 1.4 * mm))
        return out

    def _education_block(self, e: EducationEntry) -> List[Any]:
        out: List[Any] = []
        heading = f"<b>{escape_xml(e.degree)}</b>"
        out.append(Paragraph(heading, self.styles["entry_head"]))
        meta_bits = [x for x in (e.institution, e.location) if x]
        grade_bit = f"Note: {e.grade}" if e.grade else ""
        left_text = " · ".join(meta_bits + ([grade_bit] if grade_bit else []))
        row = Table(
            [[Paragraph(escape_xml(left_text), self.styles["entry_sub"]),
              Paragraph(escape_xml(e.period_text()), self.styles["date_right"])]],
            colWidths=[self.content_width * 0.62, self.content_width * 0.38],
        )
        row.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        out.append(row)
        if e.description:
            out.append(Paragraph(nl2br(e.description), self.styles["body"]))
        out.append(Spacer(1, 1.4 * mm))
        return out

    def _skills_content(self, skills: List[SkillEntry]) -> List[Any]:
        categorized: Dict[str, List[str]] = {}
        uncategorized: List[str] = []
        for s in skills:
            if s.category:
                categorized.setdefault(s.category, []).append(escape_xml(s.name))
            else:
                lvl = f" ({escape_xml(s.level)})" if s.level else ""
                uncategorized.append(escape_xml(s.name) + lvl)
        # ZH: 2-spaltiges Grid wie auf der Website (skills-grid)
        if self.is_zh:
            cat_style = ParagraphStyle(
                "SkillCatZH", parent=self.styles["body"],
                fontName=self.f_bold, fontSize=self.styles["body"].fontSize,
                textColor=self.primary, spaceBefore=1.2 * mm, spaceAfter=0.8 * mm,
            )
            # baue Zellen: jede Kategorie als Block
            cells: List[List[Any]] = []
            items: List[List[Any]] = []
            if uncategorized:
                cells.append([Paragraph("<b>Sonstige</b>", cat_style), Paragraph(" · ".join(uncategorized), self.styles["body"])])
            for cat, names in categorized.items():
                cells.append([Paragraph(f"<b>{escape_xml(cat)}</b>", cat_style), Paragraph(" · ".join(names), self.styles["body"])])
            # 2 Spalten füllen
            if not cells:
                return []
            rows: List[List[Any]] = []
            for i in range(0, len(cells), 2):
                left = cells[i]
                right = cells[i + 1] if i + 1 < len(cells) else ["", ""]
                def _cell(block):
                    if isinstance(block, list):
                        return block
                    return [Paragraph(block, self.styles["body"])] if block else [Paragraph("", self.styles["body"])]
                left_flow = _cell(left)
                right_flow = _cell(right) if i + 1 < len(cells) else [Paragraph("", self.styles["body"])]
                rows.append([left_flow, right_flow])
            tbl = Table(rows, colWidths=[self.content_width / 2] * 2)
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            return [tbl]
        out: List[Any] = []
        if uncategorized:
            out.append(Paragraph(" · ".join(uncategorized), self.styles["body"]))
        for cat, names in categorized.items():
            out.append(Paragraph(f"<b>{escape_xml(cat)}:</b> " + " · ".join(names), self.styles["body"]))
        return out


# ---------------------------------------------------------------------------
# Zertifikat-Anhang: Bilder/PDFs als Anhang-Seiten in das Gesamt-PDF mergen
# ---------------------------------------------------------------------------


def _cert_file_to_pdf_bytes(path: str, builder) -> Optional[bytes]:
    """Konvertiert ein einzelnes Zertifikats-Bild in ein 1-seitiges A4-PDF."""
    if not path or not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            with open(path, "rb") as fh:
                return fh.read()
        except Exception:
            return None
    # Bild -> PDF
    try:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=builder.margin_left, rightMargin=builder.margin_right,
            topMargin=builder.margin_top, bottomMargin=builder.margin_bottom,
        )
        # Skaliere Bild auf verfügbare Breite/Höhe (abzüglich Titelzeile)
        avail_w = A4[0] - builder.margin_left - builder.margin_right
        avail_h = A4[1] - builder.margin_top - builder.margin_bottom - 20 * mm
        img = Image(path, width=avail_w, height=avail_h)
        # Seitenverhältnis beibehalten
        try:
            iw, ih = img.imageWidth, img.imageHeight
            if iw and ih:
                scale = min(avail_w / iw, avail_h / ih)
                img.drawWidth = iw * scale
                img.drawHeight = ih * scale
        except Exception:
            pass
        title = Paragraph(
            f"<i>{escape_xml(os.path.basename(path))}</i>",
            ParagraphStyle("CertTitle", parent=builder.styles["small"], alignment=TA_CENTER, spaceAfter=4 * mm),
        )
        doc.build([title, img])
        return buf.getvalue()
    except Exception:
        return None


def _merge_with_certificates(cv_bytes: bytes, resume: Resume, builder) -> bytes:
    """Hängt gescannte Zertifikate (Bilder/PDFs) an das CV-PDF an."""
    if not bool(resume.settings.get("include_certificates_appendix", True)):
        return cv_bytes
    # Suche Zertifikats-Abschnitt direkt
    cert_sec = None
    for s in resume.sections:
        if s.get("type") == "zertifikate":
            cert_sec = s
            break
    if not cert_sec:
        return cv_bytes
    entries = cert_sec.get("data", {}).get("entries", [])
    pdf_parts: List[bytes] = []
    for entry in entries:
        fp = safe_str(entry.get("file_path", ""))
        if not fp:
            continue
        if not os.path.exists(fp):
            builder.warnings.append(
                f"Zertifikat-Datei nicht gefunden und weggelassen:\n{fp}"
            )
            continue
        part = _cert_file_to_pdf_bytes(fp, builder)
        if part:
            pdf_parts.append(part)
        else:
            builder.warnings.append(
                f"Zertifikat-Datei kann nicht gelesen werden:\n{fp}"
            )
    if not pdf_parts:
        return cv_bytes
    # Mergen via pypdfium2
    try:
        import pypdfium2 as pdfium
        # Haupt-PDF + alle Anhänge in ein neues Dokument
        merged = pdfium.PdfDocument.new()
        main_doc = pdfium.PdfDocument(cv_bytes)
        merged.import_pages(main_doc)
        main_doc.close()
        for part in pdf_parts:
            try:
                src = pdfium.PdfDocument(part)
                merged.import_pages(src)
                src.close()
            except Exception:
                builder.warnings.append("Ein Zertifikat-Anhang ist beschädigt und wurde weggelassen.")
                continue
        out = io.BytesIO()
        merged.save(out)
        merged.close()
        return out.getvalue()
    except Exception as exc:
        builder.warnings.append(f"Zertifikat-Anhang fehlgeschlagen ({exc}); nur Lebenslauf exportiert.")
        return cv_bytes


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def render_pdf_bytes(resume: Resume, warnings_out: Optional[List[str]] = None) -> bytes:
    """Erzeugt das PDF im Speicher (für Live-Vorschau) und liefert Bytes."""
    buf = io.BytesIO()
    _write_pdf(resume, buf, warnings_out=warnings_out)
    return buf.getvalue()


def generate_pdf(resume: Resume, filename: str,
                 warnings_out: Optional[List[str]] = None) -> str:
    """Schreibt das PDF in eine Datei und gibt den Pfad zurück."""
    with open(filename, "wb") as fh:
        _write_pdf(resume, fh, warnings_out=warnings_out)
    return filename


def render_cover_pdf_bytes(resume: Resume) -> bytes:
    """Erzeugt NUR das Anschreiben als PDF (mit Seiten-Dekor wie Vorschau)."""
    from reportlab.platypus import SimpleDocTemplate
    from .cover_letter import cover_letter_flowables
    builder = PDFBuilder(resume)
    flows = cover_letter_flowables(resume, builder)
    if not flows:
        raise ValueError("Anschreiben ist leer.")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=builder.margin_left, rightMargin=builder.margin_right,
        topMargin=builder.margin_top, bottomMargin=builder.margin_bottom,
    )
    on_page = _page_decorator(builder)
    doc.build(flows, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()


def _page_decorator(builder):
    """
    Canvas-Callback für jede Seite: malt die Hintergrundfarbe (wenn nicht
    Weiß) und beim Terminal zusätzlich den Fenster-Rahmen.
    """

    need_bg = builder.is_terminal or builder.page_bg_hex.upper() != "#FFFFFF"

    def _on_page(canvas, doc):
        if not need_bg and not builder.is_terminal:
            return
        canvas.saveState()
        try:
            if need_bg:
                canvas.setFillColor(builder.page_bg)
                canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
            if builder.is_terminal:
                inset = builder.frame_inset
                canvas.setStrokeColor(builder.frame_col)
                canvas.setLineWidth(0.8)
                canvas.rect(inset, inset, A4[0] - 2 * inset, A4[1] - 2 * inset, stroke=1, fill=0)
        finally:
            canvas.restoreState()

    return _on_page


def _write_pdf(resume: Resume, target: Any,
               warnings_out: Optional[List[str]] = None) -> None:
    from .font_fallback import pop_dropped, reset_dropped
    reset_dropped()
    builder = PDFBuilder(resume)
    # Falls Ziel ein Dateipfad-BytesIO ist, bauen wir erst in einen temporären Buffer,
    # damit wir Zertifikats-Anhänge mergen können, bevor wir in `target` schreiben.
    tmp_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        tmp_buf,
        pagesize=A4,
        rightMargin=builder.margin_right,
        leftMargin=builder.margin_left,
        topMargin=builder.margin_top,
        bottomMargin=builder.margin_bottom,
        title=f"Lebenslauf {resume.full_name()}".strip(),
        author=safe_str(resume.personal.get("first_name")) or "Lebenslauf Studio",
    )
    story: List[Any] = []
    # Anschreiben voranstellen (eigene Seite(n) nach DIN 5008)
    try:
        from .cover_letter import cover_letter_flowables
        cl_flows = cover_letter_flowables(resume, builder)
        if cl_flows:
            story.extend(cl_flows)
            story.append(PageBreak())
    except Exception as exc:
        builder.warnings.append(f"Anschreiben kann nicht erzeugt werden ({exc}) und wurde weggelassen.")
    builder.build_header(story)
    for section in resume.sections:
        builder.render_section(story, section)
    if builder.is_terminal:
        builder.build_terminal_footer(story)
    on_page = _page_decorator(builder)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    cv_bytes = tmp_buf.getvalue()
    # Zertifikate anhängen
    try:
        final_bytes = _merge_with_certificates(cv_bytes, resume, builder)
    except Exception as exc:
        builder.warnings.append(f"Zertifikat-Anhang fehlgeschlagen ({exc}).")
        final_bytes = cv_bytes
    # Entfernte Sonderzeichen + Builder-Hinweise zurückgeben
    if warnings_out is not None:
        dropped = pop_dropped()
        if dropped:
            warnings_out.append(
                "Diese Zeichen haben in keiner Schrift eine Glyphe und wurden entfernt: "
                + " ".join(dropped)
            )
        warnings_out.extend(builder.warnings)
    # In das eigentliche Ziel schreiben
    if hasattr(target, "write"):
        target.write(final_bytes)
    else:
        with open(target, "wb") as fh:
            fh.write(final_bytes)
