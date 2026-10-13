"""Gemeinsame Basis für alle Vorlagen."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TemplateStyle:
    """
    Beschreibt das Layout einer Vorlage.

    Wichtig: Die Vorlagen unterscheiden sich nicht nur in Farben,
    sondern tatsächlich im Layout (Header-Aufbau, Überschriften-Stil,
    Position der Daten, Spaltenaufbau).
    """

    name: str = ""
    description: str = ""

    # Farben
    primary_color: str = "#1F4E79"      # Akzentfarbe (Überschriften/Linien)
    secondary_color: str = "#555555"    # Zweitfarbe (kleine Texte)
    text_color: str = "#222222"         # Fließtext
    accent_color: str = ""              # dritte Farbe (Linien/Hintergrund), fällt auf primary zurück
    background_color: str = "#FFFFFF"   # Seitenhintergrund (für künftige HTML-Exporte)

    # Typografie
    font: str = "Helvetica"             # Standard-Font (Body)
    bold_font: str = "Helvetica-Bold"
    italic_font: str = "Helvetica-Oblique"
    heading_font: str = ""              # falls abweichend vom Body

    # Layout-Varianten
    header_layout: str = "left"          # left | centered | split | two_column | terminal
    title_style: str = "line"            # line | underline | caps | bar | box | zh | terminal
    date_style: str = "right"            # right | inline
    ats_safe: bool = True
    origin: str = ""                    # z. B. "z-hussein.com" für Web-Nachbau
    dark_mode: bool = False             # dunkler Seitenhintergrund (Terminal)

    # Terminal-/Dark-Farben (nur bei dark_mode genutzt)
    page_background: str = "#0C0B09"
    frame_color: str = "#2E2A22"
    titlebar_background: str = "#14120F"
    muted_color: str = "#8C8472"         # gedämpftes Grau (Pfad, Daten)
    body_color: str = "#C9C1AD"          # Fließtext im Terminal

    # Zwei-Spalten-Layout (nur Creative): welche Abschnitte links erscheinen
    sidebar_sections: List[str] = field(default_factory=list)
    sidebar_background: str = ""
