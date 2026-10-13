"""Vorlagen-Registry: alle verfügbaren Vorlagen der App."""

from typing import Dict, List

from .base import TemplateStyle
from . import modern, classic, minimal, professional, creative
from . import zh_modern, zh_classic, zh_creative, zh_tech, zh_executive
from . import swiss, nordic, terminal


def _all_styles() -> List[TemplateStyle]:
    return [
        modern.STYLE,
        classic.STYLE,
        minimal.STYLE,
        professional.STYLE,
        creative.STYLE,
        zh_modern.STYLE,
        zh_classic.STYLE,
        zh_creative.STYLE,
        zh_tech.STYLE,
        zh_executive.STYLE,
        swiss.STYLE,
        nordic.STYLE,
        terminal.STYLE,
    ]


#: name -> TemplateStyle
TEMPLATES: Dict[str, TemplateStyle] = {s.name: s for s in _all_styles()}

#: Reihenfolge für die Sidebar-Auswahl
TEMPLATE_ORDER: List[str] = [s.name for s in _all_styles()]

DEFAULT_TEMPLATE: str = "Modern"


def get_template(name: str) -> TemplateStyle:
    """Gibt die Vorlage zurück; fällt bei unbekanntem Namen auf Modern zurück."""
    style = TEMPLATES.get(name)
    if style is None:
        return TEMPLATES[DEFAULT_TEMPLATE]
    return style
