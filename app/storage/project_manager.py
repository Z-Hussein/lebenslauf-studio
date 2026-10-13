"""
ProjectManager: Laden und Speichern von Lebenslauf-Projekten als JSON.

Verwaltet den aktuellen Dateipfad und stellt sicher, dass beim Öffnen
das komplette Projekt wiederhergestellt wird.
"""

import json
import os
from typing import Optional

from ..models.resume import Resume
from ..utils.helpers import unique_path

PROJECT_EXTENSION = "*.json"
PROJECT_FILTER = "Lebenslauf-Projekt (*.json);;Alle Dateien (*)"


class ProjectManager:
    """Verwaltet das aktuelle Projekt (Neu / Öffnen / Speichern)."""

    def __init__(self) -> None:
        self.current_path: Optional[str] = None
        self.dirty: bool = False

    # ------------------------------------------------------------------
    # Projektoperationen
    # ------------------------------------------------------------------

    def new_project(self) -> Resume:
        """Erstellt ein leeres Projekt mit Standardabschnitten."""
        resume = Resume()
        self._add_default_sections(resume)
        self.current_path = None
        self.dirty = False
        return resume

    @staticmethod
    def _add_default_sections(resume: Resume) -> None:
        from ..models.section import SectionType

        for stype in (
            SectionType.PROFILE,
            SectionType.EXPERIENCE,
            SectionType.EDUCATION,
            SectionType.SKILLS,
            SectionType.LANGUAGES,
        ):
            resume.add_section(stype)

    def load(self, path: str) -> Resume:
        """Lädt ein Projekt aus einer JSON-Datei (mit verständlichen Fehlern)."""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            raise ValueError(f"Datei nicht gefunden:\n{path}")
        except json.JSONDecodeError:
            raise ValueError(
                "Die Datei ist keine gültige Projektdatei\n"
                "(JSON beschädigt). Wurde sie manuell bearbeitet?"
            )
        except OSError as exc:
            raise ValueError(f"Datei kann nicht gelesen werden:\n{exc}")
        if not isinstance(data, dict):
            raise ValueError("Ungültiges Projektformat.")
        version = data.get("version", 1)
        if not isinstance(version, int) or version > 2:
            raise ValueError(
                f"Unbekannte Projektversion ({data.get('version')}).\n"
                "Bitte eine neuere App-Version verwenden."
            )
        resume = Resume.from_dict(data)
        self.current_path = path
        self.dirty = False
        return resume

    def save(self, resume: Resume, path: Optional[str] = None) -> str:
        """
        Speichert das Projekt atomar (Temp-Datei + Umbenennen), damit ein
        Absturz keine 0-Byte-Datei hinterlässt. Alte Datei bleibt als .bak.
        """
        import tempfile

        target = path or self.current_path
        if not target:
            raise ValueError("Kein Speicherort angegeben.")
        directory = os.path.dirname(os.path.abspath(target)) or "."
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as exc:
            raise ValueError(f"Ordner kann nicht erstellt werden:\n{exc}")
        payload = json.dumps(resume.to_dict(), ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(
            prefix=".lebenslauf-", suffix=".tmp", dir=directory
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            if os.path.exists(target):
                bak_path = target + ".bak"
                try:
                    if os.path.exists(bak_path):
                        os.remove(bak_path)
                    os.replace(target, bak_path)
                except OSError:
                    pass  # Backup ist optional, Speichern geht weiter
            os.replace(tmp_path, target)
        except OSError as exc:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            raise ValueError(f"Projekt kann nicht gespeichert werden:\n{exc}")
        self.current_path = target
        self.dirty = False
        return target

    def save_as_unique(self, resume: Resume, directory: str, base_name: str = "lebenslauf") -> str:
        """Speichert unter einem nicht vorhandenen Namen im Verzeichnis."""
        path = os.path.join(directory, f"{base_name}.json")
        path = unique_path(path)
        return self.save(resume, path)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def display_name(self) -> str:
        if self.current_path:
            return os.path.basename(self.current_path)
        return "Unbenannt"
