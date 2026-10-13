"""Vorlage: ZH Modern - exakter Nachbau von z-hussein.com/cv (Modern Professional)."""

from .base import TemplateStyle

STYLE = TemplateStyle(
    name="ZH Modern",
    description="Nachbau z-hussein.com – pink #FF2D95, zentrierter Header, moderne Sans-Serif.",
    primary_color="#FF2D95",
    secondary_color="#1F1F1F",
    accent_color="#2A2A2A",
    text_color="#333333",
    background_color="#FFFFFF",
    font="Helvetica",
    bold_font="Helvetica-Bold",
    italic_font="Helvetica-Oblique",
    heading_font="Helvetica-Bold",
    header_layout="centered",
    title_style="zh",
    date_style="right",
    ats_safe=True,
    origin="z-hussein.com",
)
