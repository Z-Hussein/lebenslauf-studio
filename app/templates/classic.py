"""Vorlage: Classic - traditioneller deutscher Lebenslauf (Serif, zentriert)."""

from .base import TemplateStyle

STYLE = TemplateStyle(
    name="Classic",
    description="Konservatives deutsches Design, Serifenschrift, klare Datumsangaben.",
    primary_color="#222222",
    secondary_color="#444444",
    text_color="#1A1A1A",
    font="Times-Roman",
    bold_font="Times-Bold",
    italic_font="Times-Italic",
    header_layout="centered",
    title_style="underline",
    date_style="right",
    ats_safe=True,
)
