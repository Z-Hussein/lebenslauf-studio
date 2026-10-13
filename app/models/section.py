"""
Datenmodelle für einzelne Abschnitte des Lebenslaufs.

Jeder Abschnittstyp hat eigene Eintrags-Klassen mit Serialisierung
nach/von JSON (dict), damit Projekte vollständig gespeichert werden können.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SectionType(str, Enum):
    """Alle unterstützten Abschnittstypen."""

    PROFILE = "profil"
    EXPERIENCE = "berufserfahrung"
    EDUCATION = "ausbildung"
    SKILLS = "kenntnisse"
    LANGUAGES = "sprachen"
    CERTIFICATES = "zertifikate"
    PROJECTS = "projekte"
    PRACTICA = "praktika"
    VOLUNTEER = "ehrenamt"
    PUBLICATIONS = "publikationen"
    AWARDS = "auszeichnungen"
    COURSES = "kurse"
    CONFERENCES = "konferenzen"
    INTERESTS = "interessen"
    REFERENCES = "referenzen"
    CUSTOM = "eigener_abschnitt"


# Anzeigetitel der Standardabschnitte (deutsch)
SECTION_TITLES: Dict[str, str] = {
    SectionType.PROFILE.value: "Profil",
    SectionType.EXPERIENCE.value: "Berufserfahrung",
    SectionType.EDUCATION.value: "Ausbildung",
    SectionType.SKILLS.value: "Kenntnisse",
    SectionType.LANGUAGES.value: "Sprachen",
    SectionType.CERTIFICATES.value: "Zertifikate",
    SectionType.PROJECTS.value: "Projekte",
    SectionType.PRACTICA.value: "Praktika",
    SectionType.VOLUNTEER.value: "Ehrenamt",
    SectionType.PUBLICATIONS.value: "Publikationen",
    SectionType.AWARDS.value: "Auszeichnungen",
    SectionType.COURSES.value: "Kurse",
    SectionType.CONFERENCES.value: "Konferenzen",
    SectionType.INTERESTS.value: "Interessen",
    SectionType.REFERENCES.value: "Referenzen",
    SectionType.CUSTOM.value: "Eigener Abschnitt",
}


@dataclass
class ExperienceEntry:
    """Ein Eintrag im Abschnitt Berufserfahrung."""

    position: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current_position: bool = False
    description: str = ""
    achievements: List[str] = field(default_factory=list)

    def period_text(self) -> str:
        """Zeitraum als lesbare Zeichenkette, z. B. '01/2023 – heute'."""
        end = "heute" if self.current_position else self.end_date
        if self.start_date and end:
            return f"{self.start_date} – {end}"
        return self.start_date or end

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "company": self.company,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "current_position": self.current_position,
            "description": self.description,
            "achievements": list(self.achievements),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperienceEntry":
        return cls(
            position=data.get("position", ""),
            company=data.get("company", ""),
            location=data.get("location", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            current_position=bool(data.get("current_position", False)),
            description=data.get("description", ""),
            achievements=list(data.get("achievements", [])),
        )


@dataclass
class EducationEntry:
    """Ein Eintrag im Abschnitt Ausbildung."""

    degree: str = ""
    institution: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    grade: str = ""
    description: str = ""

    def period_text(self) -> str:
        if self.start_date and self.end_date:
            return f"{self.start_date} – {self.end_date}"
        return self.start_date or self.end_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "degree": self.degree,
            "institution": self.institution,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "grade": self.grade,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EducationEntry":
        return cls(
            degree=data.get("degree", ""),
            institution=data.get("institution", ""),
            location=data.get("location", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            grade=data.get("grade", "") or "",
            description=data.get("description", ""),
        )


@dataclass
class SkillEntry:
    """Ein Eintrag im Abschnitt Kenntnisse."""

    name: str = ""
    category: str = ""      # z. B. Programmiersprachen, Software, Tools ...
    level: str = ""         # optional, z. B. "sehr gut"

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "category": self.category, "level": self.level}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillEntry":
        return cls(
            name=data.get("name", ""),
            category=data.get("category", "") or "",
            level=data.get("level", "") or "",
        )


@dataclass
class LanguageEntry:
    """Ein Eintrag im Abschnitt Sprachen."""

    name: str = ""
    level: str = ""   # Muttersprache, C2, C1, B2, B1, A2, A1, Grundkenntnisse

    LEVELS = ["Muttersprache", "C2", "C1", "B2", "B1", "A2", "A1", "Grundkenntnisse"]

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "level": self.level}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LanguageEntry":
        return cls(name=data.get("name", ""), level=data.get("level", ""))


@dataclass
class CertificateEntry:
    """Ein Eintrag im Abschnitt Zertifikate – optional mit Datei-Anhang (Scan)."""

    name: str = ""
    issuer: str = ""
    year: str = ""
    description: str = ""
    file_path: str = ""  # lokaler Pfad zu Scan (JPG/PNG/PDF)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "issuer": self.issuer,
            "year": self.year,
            "description": self.description,
            "file_path": self.file_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CertificateEntry":
        return cls(
            name=data.get("name", ""),
            issuer=data.get("issuer", ""),
            year=str(data.get("year", "") or ""),
            description=data.get("description", ""),
            file_path=str(data.get("file_path", "") or ""),
        )


@dataclass
class ProjectEntry:
    """Ein Eintrag im Abschnitt Projekte."""

    name: str = ""
    role: str = ""
    period: str = ""
    description: str = ""
    technologies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "period": self.period,
            "description": self.description,
            "technologies": list(self.technologies),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectEntry":
        return cls(
            name=data.get("name", ""),
            role=data.get("role", ""),
            period=data.get("period", ""),
            description=data.get("description", ""),
            technologies=list(data.get("technologies", [])),
        )


@dataclass
class ListItemEntry:
    """
    Generischer Eintrag für Listen-Abschnitte:
    Praktika, Ehrenamt, Publikationen, Auszeichnungen, Kurse, Konferenzen.
    """

    title: str = ""        # Haupttext, z. B. Kursname oder Position
    subtitle: str = ""     # z. B. Anbieter oder Organisation
    period: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "period": self.period,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListItemEntry":
        return cls(
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            period=data.get("period", ""),
            description=data.get("description", ""),
        )


@dataclass
class ReferenceEntry:
    """Ein Eintrag im Abschnitt Referenzen."""

    name: str = ""
    position_company: str = ""
    contact: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "position_company": self.position_company,
            "contact": self.contact,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReferenceEntry":
        return cls(
            name=data.get("name", ""),
            position_company=data.get("position_company", ""),
            contact=data.get("contact", ""),
        )
