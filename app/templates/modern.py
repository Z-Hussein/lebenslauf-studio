"""Vorlage: Modern - modern, einspaltig, blaue Akzente, ATS-freundlich."""

from .base import TemplateStyle

STYLE = TemplateStyle(
    name="Modern",
    description="Modernes Design mit blauen Akzenten, viel Weißraum, ATS-freundlich.",
    primary_color="#1F4E79",
    secondary_color="#555555",
    text_color="#222222",
    font="Helvetica",
    bold_font="Helvetica-Bold",
    italic_font="Helvetica-Oblique",
    header_layout="left",
    title_style="line",
    date_style="right",
    ats_safe=True,
)
