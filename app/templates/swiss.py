"""Vorlage: Swiss - Schweizer Grid, sehr strukturiert, Helvetica, viel Weißraum."""

from .base import TemplateStyle
STYLE = TemplateStyle(
    name="Swiss",
    description="Schweizer Stil – strenges Raster, Helvetica, sehr modern.",
    primary_color="#111111",
    secondary_color="#666666",
    accent_color="#E10600",
    text_color="#111111",
    font="Helvetica",
    bold_font="Helvetica-Bold",
    italic_font="Helvetica-Oblique",
    header_layout="left",
    title_style="line",
    date_style="inline",
    ats_safe=True,
)
