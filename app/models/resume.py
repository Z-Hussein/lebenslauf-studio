"""
Zentrales Datenmodell: Resume.

Enthält persönliche Daten, Design-Einstellungen und die geordnete
Liste der Abschnitte. Die Reihenfolge in `sections` entspricht exakt
der Reihenfolge im erzeugten PDF.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .section import SectionType

# Standard-Design-Einstellungen
DEFAULT_SETTINGS: Dict[str, Any] = {
    "primary_color": "#1F4E79",
    "secondary_color": "#555555",
    "accent_color": "",
    # "" = automatisch: Weiß bei hellen Vorlagen, Dunkel bei Terminal
    "background_color": "",
    "font": "Helvetica",
    "font_size": 10,
    "line_spacing": 1.2,
    "section_spacing": 8,
    "margin_left": 18,
    "margin_right": 18,
    "margin_top": 16,
    "margin_bottom": 16,
    # Neue Features
    "icons_enabled": False,
    "show_photo_border": True,
    "include_cover_letter": False,
    "include_certificates_appendix": True,
}

# Anschreiben nach DIN 5008 – alle Regeln als Default-Felder
EMPTY_COVER_LETTER: Dict[str, Any] = {
    "enabled": False,
    "sender_extra": "",  # zusätzliche Zeile über Absender (z. B. „Max Mustermann · Musterstr. 1“)
    "recipient_company": "",
    "recipient_contact": "",
    "recipient_street": "",
    "recipient_postal_city": "",
    "city_date": "",  # z. B. „Berlin, 25. August 2026“ – leer = automatisch aus Ort/Datum
    "city": "",
    "date": "",  # ISO YYYY-MM-DD oder freier Text
    "subject": "Bewerbung als",
    "salutation": "Sehr geehrte Damen und Herren,",
    "body": (
        "mit großem Interesse habe ich Ihre Stellenausschreibung gelesen. "
        "Gerne möchte ich mich mit meinen bisherigen Erfahrungen und Kenntnissen einbringen.\n\n"
        "In meiner aktuellen Tätigkeit konnte ich ...\n\n"
        "Ich freue mich darauf, Sie in einem persönlichen Gespräch kennenzulernen."
    ),
    "closing": "Mit freundlichen Grüßen",
    "enclosures": "Lebenslauf, Zeugnisse",
}

EMPTY_PERSONAL: Dict[str, str] = {
    "first_name": "",
    "last_name": "",
    "title": "",
    "address": "",
    "postal_code": "",
    "city": "",
    "country": "Deutschland",
    "phone": "",
    "email": "",
    "linkedin": "",
    "website": "",
    "github": "",
    "birth_date": "",
    "birth_place": "",
    "nationality": "",
    "photo": "",
}


@dataclass
class Resume:
    """Komplettes Lebenslauf-Projekt."""

    personal: Dict[str, Any] = field(default_factory=lambda: dict(EMPTY_PERSONAL))
    template: str = "Modern"
    settings: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))
    sections: List[Dict[str, Any]] = field(default_factory=list)
    cover_letter: Dict[str, Any] = field(default_factory=lambda: dict(EMPTY_COVER_LETTER))

    # ------------------------------------------------------------------
    # Hilfsfunktionen für Abschnittsverwaltung
    # ------------------------------------------------------------------

    def full_name(self) -> str:
        first = (self.personal.get("first_name") or "").strip()
        last = (self.personal.get("last_name") or "").strip()
        return f"{first} {last}".strip()

    def get_section(self, index: int) -> Dict[str, Any]:
        return self.sections[index]

    def add_section(self, stype: SectionType, title: str = "") -> int:
        """Fügt einen neuen, leeren Abschnitt hinzu und gibt die Position zurück."""
        section = {
            "type": stype.value,
            "title": title or _default_title(stype),
            "data": _default_data(stype),
        }
        self.sections.append(section)
        return len(self.sections) - 1

    def remove_section(self, index: int) -> None:
        if 0 <= index < len(self.sections):
            del self.sections[index]

    def duplicate_section(self, index: int) -> Optional[int]:
        """Dupliziert einen Abschnitt direkt dahinter."""
        import copy

        if not (0 <= index < len(self.sections)):
            return None
        clone = copy.deepcopy(self.sections[index])
        t = clone.get("type", "")
        if t != SectionType.CUSTOM.value:
            # Standardabschnitte nur einmal erlaubt -> nur Inhalt kopieren
            for existing in self.sections:
                if existing is not clone and existing.get("type") == t:
                    return None
            clone["title"] = f'{clone.get("title", "")} (Kopie)'
        else:
            clone["title"] = f'{clone.get("title", "Abschnitt")} (Kopie)'
        self.sections.insert(index + 1, clone)
        return index + 1

    def move_section(self, index: int, delta: int) -> bool:
        """Verschiebt einen Abschnitt um `delta` Positionen (±1)."""
        new_index = index + delta
        if not (0 <= index < len(self.sections)):
            return False
        if not (0 <= new_index < len(self.sections)):
            return False
        item = self.sections.pop(index)
        self.sections.insert(new_index, item)
        return True

    def has_section_type(self, stype: SectionType) -> bool:
        return any(s.get("type") == stype.value for s in self.sections)

    def find_section(self, stype: SectionType) -> Optional[Dict[str, Any]]:
        for s in self.sections:
            if s.get("type") == stype.value:
                return s
        return None

    # ------------------------------------------------------------------
    # Serialisierung
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        # Tiefe Kopien: sonst teilen Export/Speichern/Preview sich die
        # verschachtelten dicts/lists mit dem Live-Modell (Aliasing-Bug).
        import copy
        return {
            "version": 2,
            "template": self.template,
            "settings": copy.deepcopy(self.settings),
            "personal": copy.deepcopy(self.personal),
            "cover_letter": copy.deepcopy(self.cover_letter),
            "sections": copy.deepcopy(self.sections),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resume":
        resume = cls()
        resume.template = data.get("template", "Modern")
        settings = data.get("settings", {}) or {}
        merged = dict(DEFAULT_SETTINGS)
        merged.update({k: v for k, v in settings.items() if v is not None})
        # Migration: alte Settings ohne neue Keys behalten Defaults
        resume.settings = merged
        personal = data.get("personal", {}) or {}
        merged_personal = dict(EMPTY_PERSONAL)
        merged_personal.update(personal)
        resume.personal = merged_personal
        # Anschreiben (ab v2)
        cl = data.get("cover_letter") or {}
        merged_cl = dict(EMPTY_COVER_LETTER)
        merged_cl.update({k: v for k, v in cl.items() if v is not None})
        resume.cover_letter = merged_cl
        # Migration: altes Top-Level include_cover_letter -> cover_letter.enabled
        if "include_cover_letter" in settings and "enabled" not in cl:
            resume.cover_letter["enabled"] = bool(settings.get("include_cover_letter"))
        import copy
        sections = data.get("sections", []) or []
        resume.sections = copy.deepcopy([dict(s) for s in sections])
        return resume


def _default_title(stype: SectionType) -> str:
    from .section import SECTION_TITLES

    return SECTION_TITLES.get(stype.value, stype.value.title())


def _default_data(stype: SectionType) -> Dict[str, Any]:
    """Legt die leere Datenstruktur je Abschnittstyp an."""
    if stype == SectionType.PROFILE:
        return {"content": ""}
    if stype in (
        SectionType.EXPERIENCE,
        SectionType.EDUCATION,
        SectionType.CERTIFICATES,
        SectionType.PRACTICA,
        SectionType.VOLUNTEER,
        SectionType.PUBLICATIONS,
        SectionType.AWARDS,
        SectionType.COURSES,
        SectionType.CONFERENCES,
    ):
        return {"entries": []}
    if stype == SectionType.SKILLS:
        return {"skills": []}
    if stype == SectionType.LANGUAGES:
        return {"languages": []}
    if stype == SectionType.PROJECTS:
        return {"entries": []}
    if stype == SectionType.INTERESTS:
        return {"items": []}
    if stype == SectionType.REFERENCES:
        return {"entries": []}
    if stype == SectionType.CUSTOM:
        return {"content": ""}
    return {}
