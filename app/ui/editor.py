"""
Editoren für alle Lebenslauf-Abschnitte.

Architektur: Ein generischer Listen-Editor (EntryListEditor) deckt alle
dynamischen Abschnitte ab und wird nur mit Feldspezifikationen konfiguriert.
Persönliche Daten und reine Textabschnitte haben eigene Editoren.

Alle Editoren schreiben direkt in die gemeinsame Resume-Datenstruktur und
rufen nach jeder Änderung den Callback `on_change` auf (für Vorschau & Dirty-Markierung).
"""

from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..models.section import LanguageEntry
from .dialogs import (
    EntryEditDialog,
    field_check,
    field_combo,
    field_file,
    field_line,
    field_lines,
    field_text,
)

# ---------------------------------------------------------------------------
# Feld-Konfigurationen je Abschnittstyp
# ---------------------------------------------------------------------------

EXPERIENCE_FIELDS = [
    field_line("position", "Position", "z. B. Softwareentwickler/in"),
    field_line("company", "Unternehmen", "z. B. Muster GmbH"),
    field_line("location", "Ort", "z. B. Berlin"),
    field_line("start_date", "Startdatum", "z. B. 01/2023"),
    field_line("end_date", "Enddatum", "z. B. 12/2025"),
    field_check("current_position", "Aktuelle Position"),
    field_text("description", "Beschreibung", "Kurzbeschreibung der Tätigkeit"),
    field_lines("achievements", "Erfolge / Aufgaben", "Ein Punkt pro Zeile – erscheint als Aufzählung"),
]

EDUCATION_FIELDS = [
    field_line("degree", "Abschluss", "z. B. M.Sc. Informatik"),
    field_line("institution", "Institution", "z. B. TU Berlin"),
    field_line("location", "Ort"),
    field_line("start_date", "Startdatum", "z. B. 10/2018"),
    field_line("end_date", "Enddatum", "z. B. 09/2022"),
    field_line("grade", "Note (optional)", "z. B. 1,7"),
    field_text("description", "Beschreibung", "Schwerpunkte, Vertiefungen …"),
]

SKILL_CATEGORIES = ["Programmiersprachen", "Software", "Tools", "Methoden", "Fachkenntnisse"]

SKILLS_FIELDS = [
    field_line("name", "Kenntnis", "z. B. Python"),
    field_combo("category", "Kategorie (optional)", SKILL_CATEGORIES),
    field_line("level", "Level (optional)", "z. B. sehr gut"),
]

LANGUAGE_FIELDS = [
    field_line("name", "Sprache", "z. B. Deutsch"),
    field_combo("level", "Niveau", LanguageEntry.LEVELS),
]

CERTIFICATE_FIELDS = [
    field_line("name", "Zertifikat", "z. B. ISTQB Certified Tester"),
    field_line("issuer", "Aussteller", "z. B. TÜV"),
    field_line("year", "Jahr", "z. B. 2024"),
    field_text("description", "Beschreibung (optional)"),
    field_file("file_path", "Scan anhängen (optional)", "Bilder/PDF (*.png *.jpg *.jpeg *.pdf);;Alle Dateien (*)"),
]

PROJECT_FIELDS = [
    field_line("name", "Projektname"),
    field_line("role", "Rolle (optional)", "z. B. Tech Lead"),
    field_line("period", "Zeitraum (optional)", "z. B. 2023–2025"),
    field_text("description", "Beschreibung"),
    field_lines("technologies", "Technologien", "Eine Technologie pro Zeile"),
]

LIST_ITEM_FIELDS = [
    field_line("title", "Titel", "z. B. Kursname, Position, Auszeichnung"),
    field_line("subtitle", "Zusatz (optional)", "z. B. Anbieter oder Organisation"),
    field_line("period", "Zeitraum/Jahr (optional)"),
    field_text("description", "Beschreibung (optional)"),
]

REFERENCE_FIELDS = [
    field_line("name", "Name"),
    field_line("position_company", "Position · Unternehmen"),
    field_line("contact", "Kontakt (optional)", "Telefon oder E-Mail"),
]


def _period_str(e: Dict[str, Any]) -> str:
    if e.get("current_position"):
        end = "heute"
    else:
        end = e.get("end_date") or ""
    start = e.get("start_date") or ""
    if start and end:
        return f"{start} – {end}"
    return start or end


#: Zusammenfassungstext je Listeneintrag (für die Listendarstellung)
SUMMARY_BUILDERS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "berufserfahrung": lambda e: " – ".join(x for x in (e.get("position"), e.get("company")) if x)
    + (f"  [{_period_str(e)}]" if _period_str(e) else ""),
    "ausbildung": lambda e: " – ".join(x for x in (e.get("degree"), e.get("institution")) if x),
    "kenntnisse": lambda e: e.get("name", "")
    + (f"  [{e['category']}]" if e.get("category") else "")
    + (f"  ({e['level']})" if e.get("level") else ""),
    "sprachen": lambda e: f"{e.get('name', '')} – {e.get('level', '')}".rstrip(" –"),
    "zertifikate": lambda e: " – ".join(x for x in (e.get("name"), e.get("issuer"), e.get("year")) if x) + (" [PDF]" if e.get("file_path") else ""),
    "projekte": lambda e: " – ".join(x for x in (e.get("name"), e.get("role"), e.get("period")) if x),
    "praktika": lambda e: " – ".join(x for x in (e.get("title"), e.get("subtitle"), e.get("period")) if x),
    "ehrenamt": lambda e: " – ".join(x for x in (e.get("title"), e.get("subtitle"), e.get("period")) if x),
    "publikationen": lambda e: " – ".join(x for x in (e.get("title"), e.get("period")) if x),
    "auszeichnungen": lambda e: " – ".join(x for x in (e.get("title"), e.get("period")) if x),
    "kurse": lambda e: " – ".join(x for x in (e.get("title"), e.get("subtitle"), e.get("period")) if x),
    "konferenzen": lambda e: " – ".join(x for x in (e.get("title"), e.get("period")) if x),
    "referenzen": lambda e: " – ".join(x for x in (e.get("name"), e.get("position_company")) if x),
}

#: Feldspezifikation je Abschnittstyp
FIELDS_BY_TYPE: Dict[str, List[Dict[str, Any]]] = {
    "berufserfahrung": EXPERIENCE_FIELDS,
    "ausbildung": EDUCATION_FIELDS,
    "kenntnisse": SKILLS_FIELDS,
    "sprachen": LANGUAGE_FIELDS,
    "zertifikate": CERTIFICATE_FIELDS,
    "projekte": PROJECT_FIELDS,
    "praktika": LIST_ITEM_FIELDS,
    "ehrenamt": LIST_ITEM_FIELDS,
    "publikationen": LIST_ITEM_FIELDS,
    "auszeichnungen": LIST_ITEM_FIELDS,
    "kurse": LIST_ITEM_FIELDS,
    "konferenzen": LIST_ITEM_FIELDS,
    "referenzen": REFERENCE_FIELDS,
}

#: Schlüssel der Liste im Datenobjekt ("entries" | "skills" | "languages")
LIST_KEY_BY_TYPE: Dict[str, str] = {
    "kenntnisse": "skills",
    "sprachen": "languages",
}

#: Dialogtitel für neue Einträge
ADD_LABELS: Dict[str, str] = {
    "berufserfahrung": "Berufserfahrung hinzufügen",
    "ausbildung": "Ausbildung hinzufügen",
    "kenntnisse": "Kenntnis hinzufügen",
    "sprachen": "Sprache hinzufügen",
    "zertifikate": "Zertifikat hinzufügen",
    "projekte": "Projekt hinzufügen",
    "referenzen": "Referenz hinzufügen",
}


# ---------------------------------------------------------------------------
# Persönliche Daten
# ---------------------------------------------------------------------------


class PersonalEditor(QWidget):
    """Formular für persönliche Daten inklusive Bewerbungsfoto."""

    PERSONAL_FIELDS = [
        ("first_name", "Vorname"),
        ("last_name", "Nachname"),
        ("title", "Berufsbezeichnung", "z. B. Softwareentwickler/in"),
        ("address", "Straße & Hausnummer"),
        ("postal_code", "PLZ"),
        ("city", "Stadt"),
        ("country", "Land"),
        ("phone", "Telefon", "+49 …"),
        ("email", "E-Mail", "name@beispiel.de"),
        ("linkedin", "LinkedIn (optional)"),
        ("website", "Website (optional)"),
        ("github", "GitHub (optional)"),
        ("birth_date", "Geburtsdatum (optional)", "TT.MM.JJJJ"),
        ("birth_place", "Geburtsort (optional)"),
        ("nationality", "Nationalität (optional)"),
    ]

    def __init__(self, resume, on_change: Callable[[], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.resume = resume
        self.on_change = on_change
        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer_layout.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        scroll.setWidget(content)

        from PySide6.QtWidgets import QFormLayout

        header = QLabel("<h2>Persönliche Daten</h2>")
        layout.addWidget(header)

        self.entries: Dict[str, QLineEdit] = {}
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        for spec in self.PERSONAL_FIELDS:
            key, label = spec[0], spec[1]
            placeholder = spec[2] if len(spec) > 2 else ""
            edit = QLineEdit(str(self.resume.personal.get(key, "") or ""))
            edit.setPlaceholderText(placeholder)
            edit.textEdited.connect(self._save_field(key))
            form.addRow(label + ":", edit)
            self.entries[key] = edit

        layout.addLayout(form)

        # --- Foto ---
        layout.addSpacing(12)
        photo_label = QLabel("<h3>Bewerbungsfoto</h3>")
        layout.addWidget(photo_label)

        photo_row = QHBoxLayout()
        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(80, 100)
        self.photo_preview.setStyleSheet(
            "border: 1px dashed gray;"
        )
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_row.addWidget(self.photo_preview)

        btn_col = QVBoxLayout()
        btn_select = QPushButton("Foto auswählen …")
        btn_select.clicked.connect(self.select_photo)
        btn_remove = QPushButton("Foto entfernen")
        btn_remove.clicked.connect(self.remove_photo)
        btn_col.addWidget(btn_select)
        btn_col.addWidget(btn_remove)
        btn_col.addStretch(1)
        photo_row.addLayout(btn_col)
        photo_row.addStretch(1)

        layout.addLayout(photo_row)
        layout.addStretch(1)
        self._refresh_photo()

    def _save_field(self, key: str) -> Callable[[str], None]:
        def handler(text: str) -> None:
            self.resume.personal[key] = text.strip()
            self.on_change()

        return handler

    def select_photo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Foto auswählen", "", "Bilder (*.png *.jpg *.jpeg);;Alle Dateien (*)"
        )
        if not path:
            return
        self.resume.personal["photo"] = path
        self._refresh_photo()
        self.on_change()

    def remove_photo(self) -> None:
        self.resume.personal["photo"] = ""
        self._refresh_photo()
        self.on_change()

    def _refresh_photo(self) -> None:
        path = str(self.resume.personal.get("photo") or "")
        pix = QPixmap(path) if path else QPixmap()
        if not pix.isNull():
            scaled = pix.scaled(
                self.photo_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.photo_preview.setPixmap(scaled)
        else:
            self.photo_preview.setText("Kein\nFoto")

    def refresh(self) -> None:
        """Übernimmt Werte aus dem Modell in die Felder (nach Laden)."""
        for key, edit in self.entries.items():
            edit.setText(str(self.resume.personal.get(key, "") or ""))
        self._refresh_photo()


# ---------------------------------------------------------------------------
# Reine Textabschnitte (Profil / Eigener Abschnitt)
# ---------------------------------------------------------------------------


class TextSectionEditor(QWidget):
    """Mehrzeiliger Texteditor mit Zeichen-/Wortzähler."""

    def __init__(self, resume, section: Dict[str, Any], heading: str,
                 on_change: Callable[[], None], placeholder: str = "",
                 hint: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.resume = resume
        self.section = section
        self.on_change = on_change

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>{heading}</h2>"))

        data = section.setdefault("data", {})
        data.setdefault("content", "")

        self.text_edit = QPlainTextEdit(data.get("content", ""))
        self.text_edit.setPlaceholderText(placeholder)
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)

        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet("color: gray;")
        layout.addWidget(self.counter_label)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setWordWrap(True)
            hint_label.setStyleSheet("color: gray;")
            layout.addWidget(hint_label)

        self._update_counter()

    def _on_text_changed(self) -> None:
        self.section["data"]["content"] = self.text_edit.toPlainText()
        self._update_counter()
        self.on_change()

    def _update_counter(self) -> None:
        text = self.text_edit.toPlainText().strip()
        words = len(text.split()) if text else 0
        self.counter_label.setText(f"{len(text)} Zeichen · {words} Wörter")


# ---------------------------------------------------------------------------
# Interessen (Liste von Zeilen)
# ---------------------------------------------------------------------------


class InterestsEditor(QWidget):
    """Ein Interesse pro Zeile."""

    def __init__(self, resume, section: Dict[str, Any],
                 on_change: Callable[[], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.section = section
        self.on_change = on_change

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Interessen</h2>"))
        hint = QLabel("Ein Interesse pro Zeile:")
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        data = section.setdefault("data", {})
        items = data.setdefault("items", [])

        self.edit = QPlainTextEdit("\n".join(str(i) for i in items))
        self.edit.textChanged.connect(self._changed)
        layout.addWidget(self.edit)

    def _changed(self) -> None:
        lines = [ln.strip() for ln in self.edit.toPlainText().splitlines()]
        self.section["data"]["items"] = [ln for ln in lines if ln]
        self.on_change()


# ---------------------------------------------------------------------------
# Generischer Listen-Editor (Erfahrung, Ausbildung, Skills, …)
# ---------------------------------------------------------------------------


class EntryListEditor(QWidget):
    """
    Verwaltet eine Liste von dicts in `section["data"][list_key]`.

    Funktionen: Hinzufügen, Bearbeiten, Duplizieren, Löschen,
    nach oben/unten verschieben.
    """

    def __init__(self, resume, section: Dict[str, Any], heading: str,
                 stype: str, on_change: Callable[[], None],
                 empty_hint: str = "",
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.resume = resume
        self.section = section
        self.stype = stype
        self.on_change = on_change
        self.fields = FIELDS_BY_TYPE.get(stype, [])
        self.list_key = LIST_KEY_BY_TYPE.get(stype, "entries")
        self.summary_fn = SUMMARY_BUILDERS.get(stype, lambda e: str(e))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>{heading}</h2>"))

        if empty_hint:
            hint = QLabel(empty_hint)
            hint.setStyleSheet("color: gray;")
            hint.setWordWrap(True)
            layout.addWidget(hint)

        data = section.setdefault("data", {})
        data.setdefault(self.list_key, [])

        # Liste
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(lambda _: self.edit_entry())
        layout.addWidget(self.list_widget, 1)

        # Buttons Reihe 1
        btn_row1 = QHBoxLayout()
        btn_add = QPushButton("+ Hinzufügen")
        btn_add.clicked.connect(self.add_entry)
        btn_row1.addWidget(btn_add)

        btn_edit = QPushButton("Bearbeiten")
        btn_edit.clicked.connect(self.edit_entry)
        btn_row1.addWidget(btn_edit)

        btn_dup = QPushButton("Duplizieren")
        btn_dup.clicked.connect(self.duplicate_entry)
        btn_row1.addWidget(btn_dup)

        btn_del = QPushButton("Löschen")
        btn_del.clicked.connect(self.delete_entry)
        btn_row1.addWidget(btn_del)
        layout.addLayout(btn_row1)

        # Buttons Reihe 2
        btn_row2 = QHBoxLayout()
        btn_up = QPushButton("Nach oben")
        btn_up.clicked.connect(lambda checked=False: self.move_entry(-1))
        btn_row2.addWidget(btn_up)

        btn_down = QPushButton("Nach unten")
        btn_down.clicked.connect(lambda checked=False: self.move_entry(+1))
        btn_row2.addWidget(btn_down)
        btn_row2.addStretch(1)
        layout.addLayout(btn_row2)

        # Entf-Taste löscht den gewählten Eintrag
        from PySide6.QtCore import Qt as _Qt
        from PySide6.QtGui import QShortcut, QKeySequence
        self._del_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.list_widget)
        self._del_shortcut.setContext(_Qt.ShortcutContext.WidgetShortcut)
        self._del_shortcut.activated.connect(self.delete_entry)

        self.refresh()

    # -- Datenzugriff ---------------------------------------------------

    def _entries(self) -> List[Dict[str, Any]]:
        return self.section["data"][self.list_key]

    # -- Aktionen ---------------------------------------------------------

    def _selected_index(self) -> int:
        item = self.list_widget.currentItem()
        return self.list_widget.row(item) if item else -1

    def refresh(self) -> None:
        self.list_widget.clear()
        for entry in self._entries():
            item = QListWidgetItem(self.summary_fn(entry))
            self.list_widget.addItem(item)

    def add_entry(self) -> None:
        dlg = EntryEditDialog(self, ADD_LABELS.get(self.stype, "Neuer Eintrag"),
                              self.fields, {})
        if dlg.exec() != EntryEditDialog.DialogCode.Accepted:
            return
        values = dlg.get_values()
        if not any(v for v in values.values()):
            return
        entries = self._entries()
        entries.append(values)
        self.refresh()
        self.list_widget.setCurrentRow(len(entries) - 1)
        self.on_change()

    def edit_entry(self) -> None:
        idx = self._selected_index()
        if idx < 0:
            return
        entries = self._entries()
        dlg = EntryEditDialog(self, "Eintrag bearbeiten", self.fields, entries[idx])
        if dlg.exec() != EntryEditDialog.DialogCode.Accepted:
            return
        entries[idx].update(dlg.get_values())
        self.refresh()
        self.list_widget.setCurrentRow(idx)
        self.on_change()

    def duplicate_entry(self) -> None:
        idx = self._selected_index()
        if idx < 0:
            return
        import copy

        clone = copy.deepcopy(self._entries()[idx])
        entries = self._entries()
        entries.insert(idx + 1, clone)
        self.refresh()
        self.list_widget.setCurrentRow(idx + 1)
        self.on_change()

    def delete_entry(self) -> None:
        idx = self._selected_index()
        if idx < 0:
            return
        confirm = QMessageBox.question(
            self, "Löschen",
            "Diesen Eintrag wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        del self._entries()[idx]
        self.refresh()
        self.on_change()

    def move_entry(self, delta: int) -> None:
        idx = self._selected_index()
        new_idx = idx + delta
        entries = self._entries()
        if not (0 <= idx < len(entries)) or not (0 <= new_idx < len(entries)):
            return
        entries[idx], entries[new_idx] = entries[new_idx], entries[idx]
        self.refresh()
        self.list_widget.setCurrentRow(new_idx)
        self.on_change()


# ---------------------------------------------------------------------------
# Editor-Bereich (verwaltet alle Editoren in einem Stack)
# ---------------------------------------------------------------------------


from PySide6.QtWidgets import QStackedWidget  # noqa: E402


class EditorStack(QStackedWidget):
    """
    Verwaltet alle geöffneten Editoren. Jeder Abschnitt bekommt einen
    Editor (lazy erstellt). Bei neu geladenem Projekt werden alle
    Editoren neu aufgebaut.
    """

    def __init__(self, on_change: Callable[[], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.on_change = on_change
        self.resume = None
        self.personal_editor: Optional[PersonalEditor] = None
        self.section_editors: Dict[int, QWidget] = {}

        welcome = QWidget()
        wlay = QVBoxLayout(welcome)
        msg = QLabel(
            "<h2>Willkommen im Lebenslauf Studio</h2>"
            "<p>Wählen Sie links einen Abschnitt aus, um ihn zu bearbeiten.</p>"
        )
        msg.setProperty("cssClass", "welcome")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wlay.addWidget(msg)
        wlay.addStretch(1)
        self.welcome_page = self.addWidget(welcome)
        self.setCurrentIndex(self.welcome_page)

    # ------------------------------------------------------------------
    # Setup nach Laden eines Projekts
    # ------------------------------------------------------------------

    def set_resume(self, resume) -> None:
        self.resume = resume
        self.clear_editors()
        self.personal_editor = PersonalEditor(resume, self.on_change)
        idx = self.addWidget(self.personal_editor)
        self.section_editors[-1] = self.personal_editor  # Kennung: -1 = persönlich
        self._personal_index = idx
        # Anschreiben-Editor lazy, wird bei Bedarf erstellt
        self.cover_editor = None

    def clear_editors(self) -> None:
        while self.count() > 1:
            page = self.widget(self.count() - 1)
            self.removeWidget(page)
            page.deleteLater()
        self.section_editors = {}
        self.personal_editor = None
        self.cover_editor = None

    # ------------------------------------------------------------------
    # Anzeige
    # ------------------------------------------------------------------

    def show_personal(self) -> None:
        if self.personal_editor is not None:
            self.setCurrentWidget(self.personal_editor)

    def show_cover_letter(self) -> None:
        if self.cover_editor is None:
            from .cover_letter_editor import CoverLetterEditor
            self.cover_editor = CoverLetterEditor(self.resume, self.on_change)
            self.addWidget(self.cover_editor)
            self.section_editors[-2] = self.cover_editor
        elif getattr(self.cover_editor, "_resume_id", None) != id(self.resume):
            # Nur bei neu geladenem Projekt neu binden – sonst bliebe der
            # Editor auf dem alten (verwaisten) Resume-Objekt. Bei normalem
            # Tab-Wechsel NICHT neu laden (Cursor/Undo bleiben erhalten).
            try:
                self.cover_editor.bind(self.resume)
            except Exception:
                pass
        self.setCurrentWidget(self.cover_editor)

    def show_section(self, index: int, section: Optional[Dict[str, Any]]) -> None:
        if self.resume is None or section is None:
            return
        # Cache-Schlüssel ist die Objekt-Identität (id), NICHT der Index:
        # nach Hinzufügen/Verschieben zeigen Index-Keys auf falsche Abschnitte.
        key = id(section)
        editor = self.section_editors.get(key)
        if editor is None:
            editor = self._create_section_editor(index, section)
            if editor is None:
                return
            self.addWidget(editor)
            self.section_editors[key] = editor
        self.setCurrentWidget(editor)

    def _create_section_editor(self, index: int, section: Dict[str, Any]) -> Optional[QWidget]:
        stype = section.get("type", "")
        title = str(section.get("title") or "")

        if stype == "profil":
            return TextSectionEditor(
                self.resume, section, title, self.on_change,
                placeholder="Beschreiben Sie kurz Ihre berufliche Identität, Stärken und Ziele …",
                hint="Tipp: 3–5 Sätze. Vermeiden Sie Floskeln und konkretisieren Sie mit Zahlen.",
            )

        if stype == "eigener_abschnitt":
            return TextSectionEditor(
                self.resume, section, title, self.on_change,
                placeholder="Inhalt dieses Abschnitts …",
            )

        if stype == "interessen":
            return InterestsEditor(self.resume, section, self.on_change)

        if stype in FIELDS_BY_TYPE:
            hints = {
                "berufserfahrung": "Fügen Sie Ihre Positionen hinzu. Beginnen Sie mit der aktuellsten.",
                "ausbildung": "Schule, Studium, Ausbildungsplätze – in chronologischer Reihenfolge.",
                "kenntnisse": "Gruppieren Sie Kenntnisse über Kategorien (z. B. Programmiersprachen).",
                "sprachen": "Sprachniveau nach CEFR wählen (A1–C2 bzw. Muttersprache).",
            }
            return EntryListEditor(
                self.resume, section, title, stype, self.on_change,
                empty_hint=hints.get(stype, ""),
            )

        # Unbekannter Typ -> Texteditor als Fallback
        return TextSectionEditor(self.resume, section, title, self.on_change)

    def refresh_all(self) -> None:
        """Nach Projekt-Laden: alle offenen Editoren aktualisieren."""
        if self.personal_editor is not None:
            self.personal_editor.refresh()
        if getattr(self, "cover_editor", None) is not None:
            try:
                self.cover_editor.refresh()
            except Exception:
                pass
