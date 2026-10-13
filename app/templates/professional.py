"""Vorlage: Professional - dunkelblaue Überschriftenbalken, Business-Stil."""

from .base import TemplateStyle

STYLE = TemplateStyle(
    name="Professional",
    description="Business-Stil mit dunklen Überschriftenbalken und klarer Gliederung.",
    primary_color="#17365D",
    secondary_color="#444444",
    text_color="#212121",
    font="Helvetica",
    bold_font="Helvetica-Bold",
    italic_font="Helvetica-Oblique",
    header_layout="split",
    title_style="bar",
    date_style="right",
    ats_safe=True,
)
