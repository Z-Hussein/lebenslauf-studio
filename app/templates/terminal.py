"""Vorlage: Terminal - Nachbau von "Stil 3 - Terminal" (FiSi-CV, 794x1123).

Dunkles Terminal-Fenster mit JetBrains Mono, Akzentfarbe umschaltbar
(orange/grün/blau/pink wie im Mockup). Abschnitte als Shell-Kommandos,
Erfahrung als git-log-Graph, Skills als YAML, Levels als Block-Balken.
Nicht ATS-geeignet (dunkler Hintergrund) - aber exakt der Mockup-Stil.
"""

from .base import TemplateStyle

STYLE = TemplateStyle(
    name="Terminal",
    description="Terminal-Fenster wie Stil-3-Mockup: dunkel, JetBrains Mono, Shell-Kommandos, Level-Balken. Nicht ATS-geeignet.",
    primary_color="#FFB454",
    secondary_color="#8C8472",
    accent_color="#FFB454",
    text_color="#E6DFCD",
    background_color="#0C0B09",
    font="JetBrains Mono",
    bold_font="JetBrains Mono",
    italic_font="JetBrains Mono",
    heading_font="JetBrains Mono",
    header_layout="terminal",
    title_style="terminal",
    date_style="inline",
    ats_safe=False,
    origin="terminal-mockup",
    dark_mode=True,
    page_background="#0C0B09",
    frame_color="#2E2A22",
    titlebar_background="#14120F",
    muted_color="#8C8472",
    body_color="#C9C1AD",
)
