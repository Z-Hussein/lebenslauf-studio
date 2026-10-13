"""Vorlage: Creative - zweispaltiges Layout mit Seitenleiste und Akzentfarbe."""

from .base import TemplateStyle

STYLE = TemplateStyle(
    name="Creative",
    description="Zweispaltiges Design mit farbiger Seitenleiste für Kontakt & Kenntnisse.",
    primary_color="#0E7C7B",
    secondary_color="#5F6B6B",
    text_color="#263238",
    sidebar_background="#EAF4F4",
    font="Helvetica",
    bold_font="Helvetica-Bold",
    italic_font="Helvetica-Oblique",
    header_layout="two_column",
    title_style="line",
    date_style="right",
    ats_safe=False,
    # Diese Abschnitte erscheinen in der linken Spalte:
    sidebar_sections=["kenntnisse", "sprachen", "interessen"],
)
