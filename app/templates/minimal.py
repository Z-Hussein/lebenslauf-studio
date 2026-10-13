"""Vorlage: Minimal - schwarz/weiß, maximal schlicht und lesbar."""

from .base import TemplateStyle

STYLE = TemplateStyle(
    name="Minimal",
    description="Schwarz/weiß, sehr schlicht, maximale Lesbarkeit. Ideal für IT & Business.",
    primary_color="#333333",
    secondary_color="#777777",
    text_color="#111111",
    font="Helvetica",
    bold_font="Helvetica-Bold",
    italic_font="Helvetica-Oblique",
    header_layout="left",
    title_style="caps",
    date_style="inline",
    ats_safe=True,
)
