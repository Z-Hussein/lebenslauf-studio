"""
Dialoge der Anwendung:

- StartDialog: Auswahl beim Programmstart (leer / Beispiel / Projekt öffnen)
- SectionPickerDialog: Abschnittstyp zum Hinzufügen auswählen
- EntryEditDialog: Generischer Formular-Dialog für Listeneinträge
- DesignSettingsDialog: Farben, Schrift, Größen, Ränder
"""

from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
 QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models.section import SECTION_TITLES, SectionType


# ---------------------------------------------------------------------------
# Kleine Feld-Spezifikation für generische Formulare
# ---------------------------------------------------------------------------

def field_line(key: str, label: str, placeholder: str = "") -> Dict[str, Any]:
    return {"kind": "line", "key": key, "label": label, "placeholder": placeholder}


def field_text(key: str, label: str, hint: str = "") -> Dict[str, Any]:
    return {"kind": "text", "key": key, "label": label, "hint": hint}


def field_check(key: str, label: str) -> Dict[str, Any]:
    return {"kind": "check", "key": key, "label": label}


def field_combo(key: str, label: str, options: List[str]) -> Dict[str, Any]:
    return {"kind": "combo", "key": key, "label": label, "options": options}


def field_lines(key: str, label: str, hint: str = "") -> Dict[str, Any]:
    """Mehrzeilig, wird als Liste von Zeilen interpretiert."""
    return {"kind": "lines", "key": key, "label": label, "hint": hint}


def field_file(key: str, label: str, filter_str: str = "Alle Dateien (*)") -> Dict[str, Any]:
    """Datei-Auswahl (z. B. für Zertifikat-Scan)."""
    return {"kind": "file", "key": key, "label": label, "filter": filter_str}


class EntryEditDialog(QDialog):
    """
    Generischer Dialog zum Bearbeiten eines Eintrags (dict) anhand
    einer Feldspezifikation. Liefert bei Annahme ein aktualisiertes dict.
    """

    def __init__(self, parent: Optional[QWidget], title: str,
                 fields: List[Dict[str, Any]], values: Dict[str, Any]) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.fields = fields
        self.widgets: Dict[str, QWidget] = {}

        form = QFormLayout(self)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        for spec in fields:
            key, kind = spec["key"], spec["kind"]
            value = values.get(key, "")

            if kind == "line":
                w = QLineEdit(str(value or ""))
                if spec.get("placeholder"):
                    w.setPlaceholderText(spec["placeholder"])
                form.addRow(spec["label"], w)
                self.widgets[key] = w

            elif kind == "text":
                w = QPlainTextEdit(str(value or ""))
                w.setFixedHeight(90)
                wrap = QWidget()
                lay = QVBoxLayout(wrap)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.addWidget(w)
                if spec.get("hint"):
                    lab = QLabel(spec["hint"])
                    lab.setStyleSheet("color: gray;")
                    lab.setWordWrap(True)
                    lay.addWidget(lab)
                form.addRow(spec["label"], wrap)
                self.widgets[key] = w

            elif kind == "lines":
                w = QPlainTextEdit("\n".join(value or []))
                w.setFixedHeight(110)
                wrap = QWidget()
                lay = QVBoxLayout(wrap)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.addWidget(w)
                hint = spec.get("hint") or "Ein Punkt pro Zeile"
                lab = QLabel(hint)
                lab.setStyleSheet("color: gray;")
                lay.addWidget(lab)
                form.addRow(spec["label"], wrap)
                self.widgets[key] = w

            elif kind == "check":
                w = QCheckBox()
                w.setChecked(bool(value))
                form.addRow(spec["label"], w)
                self.widgets[key] = w

            elif kind == "combo":
                w = QComboBox()
                w.addItems(spec["options"])
                w.setEditable(True)
                if value:
                    idx = w.findText(str(value))
                    if idx >= 0:
                        w.setCurrentIndex(idx)
                    else:
                        w.setCurrentText(str(value))
                form.addRow(spec["label"], w)
                self.widgets[key] = w

            elif kind == "file":
                wrap = QWidget()
                hlay = QHBoxLayout(wrap)
                hlay.setContentsMargins(0, 0, 0, 0)
                line = QLineEdit(str(value or ""))
                line.setPlaceholderText("Pfad zu Scan (JPG/PNG/PDF) – wird ans PDF angehängt")
                btn = QPushButton("…")
                btn.setFixedWidth(30)
                filt = spec.get("filter") or "Bilder/PDF (*.png *.jpg *.jpeg *.pdf);;Alle Dateien (*)"
                def _choose(checked=False, _line=line, _filt=filt):
                    p, _ = QFileDialog.getOpenFileName(self, "Datei wählen", "", _filt)
                    if p:
                        _line.setText(p)
                btn.clicked.connect(_choose)
                hlay.addWidget(line, 1)
                hlay.addWidget(btn)
                form.addRow(spec["label"], wrap)
                self.widgets[key] = line

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_values(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for spec in self.fields:
            key, kind = spec["key"], spec["kind"]
            w = self.widgets[key]
            if kind == "line":
                out[key] = w.text().strip()
            elif kind == "text":
                out[key] = w.toPlainText().strip()
            elif kind == "lines":
                lines = [ln.strip() for ln in w.toPlainText().splitlines()]
                out[key] = [ln for ln in lines if ln]
            elif kind == "check":
                out[key] = w.isChecked()
            elif kind == "combo":
                out[key] = w.currentText().strip()
            elif kind == "file":
                out[key] = w.text().strip()
        return out


# ---------------------------------------------------------------------------
# Abschnitt hinzufügen
# ---------------------------------------------------------------------------

_ADDABLE = [
    SectionType.PROFILE,
    SectionType.EXPERIENCE,
    SectionType.EDUCATION,
    SectionType.SKILLS,
    SectionType.LANGUAGES,
    SectionType.CERTIFICATES,
    SectionType.PROJECTS,
    SectionType.PRACTICA,
    SectionType.VOLUNTEER,
    SectionType.PUBLICATIONS,
    SectionType.AWARDS,
    SectionType.COURSES,
    SectionType.CONFERENCES,
    SectionType.INTERESTS,
    SectionType.REFERENCES,
]


class SectionPickerDialog(QDialog):
    """Auswahl eines Abschnittstyps (Standard oder eigener Abschnitt)."""

    def __init__(self, parent: Optional[QWidget], existing_types: set) -> None:
        super().__init__(parent)
        self.setWindowTitle("Abschnitt hinzufügen")
        self.setMinimumWidth(360)

        self.selected_type: Optional[SectionType] = None
        self.custom_title: str = ""

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Welchen Abschnitt möchten Sie hinzufügen?"))

        import math

        cols = 2
        count = len(_ADDABLE) + 1
        rows = math.ceil(count / cols)
        grid_row = 0
        grid_col = 0
        grid_widget = QWidget()
        from PySide6.QtWidgets import QGridLayout

        grid = QGridLayout(grid_widget)

        def make_button(text: str, stype: Optional[SectionType]) -> None:
            nonlocal grid_row, grid_col
            btn = QPushButton(text)
            btn.setMinimumHeight(34)
            btn.clicked.connect(lambda checked=False, _s=stype: self._choose(_s))
            grid.addWidget(btn, grid_row, grid_col)
            grid_col += 1
            if grid_col >= cols:
                grid_col = 0
                grid_row += 1

        for stype in _ADDABLE:
            already = stype.value in existing_types
            label = SECTION_TITLES.get(stype.value, stype.value.title())
            btn = QPushButton(label)
            btn.setMinimumHeight(34)
            btn.setEnabled(not already)
            btn.setToolTip("Bereits vorhanden" if already else "")
            btn.clicked.connect(lambda checked=False, s=stype: self._choose(s))
            grid.addWidget(btn, grid_row, grid_col)
            grid_col += 1
            if grid_col >= cols:
                grid_col = 0
                grid_row += 1

        make_button("+ Eigener Abschnitt …", None)

        lay.addWidget(grid_widget)

        cancel = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        cancel.rejected.connect(self.reject)
        lay.addWidget(cancel)

    def _choose(self, stype: Optional[SectionType]) -> None:
        if stype is None:
            dlg = NewCustomSectionDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            if not dlg.title.strip():
                return
            self.selected_type = SectionType.CUSTOM
            self.custom_title = dlg.title.strip()
        else:
            self.selected_type = stype
        self.accept()


class NewCustomSectionDialog(QDialog):
    """Titel für einen eigenen Abschnitt abfragen."""

    def __init__(self, parent: Optional[QWidget]) -> None:
        super().__init__(parent)
        self.setWindowTitle("Eigener Abschnitt")
        lay = QFormLayout(self)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("z. B. Berufliche Ziele, Verfügbarkeit …")
        lay.addRow("Titel:", self.edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addRow(buttons)
        self.edit.setFocus()

    @property
    def title(self) -> str:
        return self.edit.text().strip()


# ---------------------------------------------------------------------------
# Design-Einstellungen
# ---------------------------------------------------------------------------


class DesignSettingsDialog(QDialog):
    """Akzentfarbe, Schriftart, Schriftgröße, Ränder und Abstände."""

    FONTS = ["Helvetica", "Inter", "Times-Roman", "DejaVu Sans", "Liberation Sans", "Calibri", "Segoe UI", "Noto Sans", "Garamond", "JetBrains Mono", "Consolas"]

    def __init__(self, parent: Optional[QWidget], settings: Dict[str, Any],
                 default_background: str = "#FFFFFF") -> None:
        super().__init__(parent)
        self.setWindowTitle("Design-Einstellungen")
        self.setMinimumWidth(420)
        self.settings = settings
        # Vorlage-Standard für "Automatisch" (Terminal: dunkel, sonst Weiß)
        self._default_background = default_background or "#FFFFFF"

        self._accent = str(settings.get("primary_color", "#1F4E79"))

        form = QFormLayout(self)

        # Akzentfarbe
        color_row = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedHeight(28)
        self.color_btn.clicked.connect(self._pick_color)
        self._update_color_button()
        color_row.addWidget(self.color_btn, 1)
        color_wrap = QWidget()
        color_wrap.setLayout(color_row)
        form.addRow("Akzentfarbe:", color_wrap)

        # Hintergrundfarbe ("" = automatisch je Vorlage)
        self._background = str(settings.get("background_color") or "")
        bg_row = QHBoxLayout()
        self.bg_btn = QPushButton()
        self.bg_btn.setFixedHeight(28)
        self.bg_btn.clicked.connect(self._pick_bg_color)
        self._update_bg_button()
        bg_row.addWidget(self.bg_btn, 1)
        self.bg_reset_btn = QPushButton("Auto")
        self.bg_reset_btn.setFixedWidth(70)
        self.bg_reset_btn.setToolTip("Hintergrund auf Vorlagen-Standard zurücksetzen")
        self.bg_reset_btn.clicked.connect(self._reset_bg_color)
        bg_row.addWidget(self.bg_reset_btn)
        bg_wrap = QWidget()
        bg_wrap.setLayout(bg_row)
        form.addRow("Hintergrund:", bg_wrap)
        bg_hint = QLabel("Leer = automatisch (Weiß, bzw. Dunkel bei Terminal). Textfarben passen sich dem Hintergrund an.")
        bg_hint.setWordWrap(True)
        bg_hint.setStyleSheet("color: gray; font-size: 10px;")
        form.addRow("", bg_hint)

        # Schriftart
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.FONTS)
        cur = str(settings.get("font", "Helvetica"))
        idx = self.font_combo.findText(cur)
        self.font_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("Schriftart:", self.font_combo)

        # Icons aktivieren
        self.icons_check = QCheckBox("Kontakt-Kürzel im PDF anzeigen (z. B. Tel., E-Mail:)")
        self.icons_check.setChecked(bool(settings.get("icons_enabled", False)))
        form.addRow("", self.icons_check)

        # Zertifikats-Anhang
        self.certs_check = QCheckBox("Zertifikats-Scans als Anhang ans PDF hängen")
        self.certs_check.setChecked(bool(settings.get("include_certificates_appendix", True)))
        form.addRow("", self.certs_check)

        # Schriftgröße
        from PySide6.QtWidgets import QDoubleSpinBox

        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(7.0, 14.0)
        self.size_spin.setSingleStep(0.5)
        self.size_spin.setValue(float(settings.get("font_size", 10)))
        form.addRow("Schriftgröße:", self.size_spin)

        # Zeilenabstand
        self.line_spin = QDoubleSpinBox()
        self.line_spin.setRange(1.0, 2.0)
        self.line_spin.setSingleStep(0.05)
        self.line_spin.setValue(float(settings.get("line_spacing", 1.2)))
        form.addRow("Zeilenabstand:", self.line_spin)

        # Abstand zwischen Abschnitten
        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(3.0, 24.0)
        self.gap_spin.setSingleStep(1.0)
        self.gap_spin.setValue(float(settings.get("section_spacing", 8)))
        form.addRow("Abschnittsabstand:", self.gap_spin)

        # Seitenränder
        margin_row = QHBoxLayout()
        self.margins: Dict[str, QDoubleSpinBox] = {}
        for key, label in (
            ("margin_left", "Links"),
            ("margin_right", "Rechts"),
            ("margin_top", "Oben"),
            ("margin_bottom", "Unten"),
        ):
            spin = QDoubleSpinBox()
            spin.setRange(10.0, 35.0)
            spin.setValue(float(settings.get(key, 18)))
            spin.setSuffix(" mm")
            self.margins[key] = spin
            box = QWidget()
            bl = QVBoxLayout(box)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.addWidget(QLabel(label))
            bl.addWidget(spin)
            margin_row.addWidget(box)
        margin_wrap = QWidget()
        margin_wrap.setLayout(margin_row)
        form.addRow("Seitenränder:", margin_wrap)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _pick_color(self) -> None:
        initial = QColor(self._accent)
        color = QColorDialog.getColor(initial, self, "Akzentfarbe wählen")
        if color.isValid():
            self._accent = color.name()
            self._update_color_button()

    def _update_color_button(self) -> None:
        self.color_btn.setText(f"Akzentfarbe: {self._accent}")
        self.color_btn.setStyleSheet(
            f"background-color: {self._accent}; color: white;"
            f"border-radius: 4px; padding: 4px;"
        )

    def _effective_bg(self) -> str:
        from ..utils.helpers import hex_or
        if self._background:
            return hex_or(self._background, self._default_background)
        return self._default_background

    def _pick_bg_color(self) -> None:
        initial = QColor(self._effective_bg())
        color = QColorDialog.getColor(initial, self, "Hintergrundfarbe wählen")
        if color.isValid():
            self._background = color.name()
            self._update_bg_button()

    def _reset_bg_color(self) -> None:
        self._background = ""
        self._update_bg_button()

    def _update_bg_button(self) -> None:
        from ..utils.helpers import is_dark_color
        eff = self._effective_bg()
        fg = "white" if is_dark_color(eff) else "black"
        label = f"Hintergrund: {eff}" if self._background else f"Automatisch: {eff}"
        self.bg_btn.setText(label)
        self.bg_btn.setStyleSheet(
            f"background-color: {eff}; color: {fg};"
            f"border-radius: 4px; padding: 4px; border: 1px solid #999999;"
        )

    def apply_to_settings(self) -> None:
        s = self.settings
        s["primary_color"] = self._accent
        s["background_color"] = self._background
        s["font"] = self.font_combo.currentText()
        s["icons_enabled"] = bool(self.icons_check.isChecked())
        s["include_certificates_appendix"] = bool(self.certs_check.isChecked())
        s["font_size"] = float(self.size_spin.value())
        s["line_spacing"] = float(self.line_spin.value())
        s["section_spacing"] = float(self.gap_spin.value())
        for key, spin in self.margins.items():
            s[key] = float(spin.value())


# ---------------------------------------------------------------------------
# Startdialog
# ---------------------------------------------------------------------------


class StartDialog(QDialog):
    """Wird beim Start angezeigt: leeren Lebenslauf oder Beispiel laden."""

    RESULT_EMPTY = "empty"
    RESULT_EXAMPLE = "example"
    RESULT_OPEN = "open"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Lebenslauf Studio – Willkommen")
        self.setMinimumWidth(420)
        self.choice: str = self.RESULT_EMPTY

        lay = QVBoxLayout(self)
        title = QLabel("<h2>Willkommen im Lebenslauf Studio</h2>")
        sub = QLabel("Wie möchten Sie beginnen?")
        lay.addWidget(title)
        lay.addWidget(sub)

        btn_empty = QPushButton("Leeren Lebenslauf erstellen")
        btn_example = QPushButton("Beispiel-Lebenslauf laden")
        btn_open = QPushButton("Bestehendes Projekt öffnen …")

        btn_empty.setMinimumHeight(40)
        btn_example.setMinimumHeight(40)
        btn_open.setMinimumHeight(40)

        btn_empty.clicked.connect(lambda checked=False: self._done(self.RESULT_EMPTY))
        btn_example.clicked.connect(lambda checked=False: self._done(self.RESULT_EXAMPLE))
        btn_open.clicked.connect(lambda checked=False: self._done(self.RESULT_OPEN))

        lay.addWidget(btn_empty)
        lay.addWidget(btn_example)
        lay.addWidget(btn_open)

    def _done(self, choice: str) -> None:
        self.choice = choice
        self.accept()
