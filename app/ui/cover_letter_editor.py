"""
Anschreiben-Editor nach DIN 5008.

Bietet alle Felder für ein deutsches Bewerbungsanschreiben mit
Live-Vorschau-Anbindung und Hilfetexten zu den Bewerbungsregeln.
"""

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..utils.helpers import safe_str


SALUTATIONS = [
    "Sehr geehrte Damen und Herren,",
    "Sehr geehrte Frau",
    "Sehr geehrter Herr",
    "Guten Tag,",
]


class CoverLetterEditor(QWidget):
    """Formular für das Bewerbungsanschreiben."""

    def __init__(self, resume, on_change: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self.resume = resume
        self.on_change = on_change
        # Sperre: während _load() darf _save() NICHT schreiben (sonst
        # würden die setText-Aufrufe das Modell mit leeren Feldern überschreiben)
        self._loading = False
        self._resume_id = id(resume)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        lay = QVBoxLayout(content)
        scroll.setWidget(content)

        title = QLabel("<h2>Anschreiben (Bewerbung)</h2>")
        hint = QLabel(
            "DIN 5008: Absender oben klein, Empfänger links, Datum rechts, Betreff fett, Anrede, "
            "3–4 Absätze (Einleitung, Hauptteil, Motivation, Schluss), Grußformel und Anlagen. "
            "Max. 1 Seite."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray;")
        lay.addWidget(title)
        lay.addWidget(hint)

        self.enabled_check = QCheckBox("Anschreiben in PDF einschließen (vor dem Lebenslauf)")
        self.enabled_check.toggled.connect(self._save)
        lay.addWidget(self.enabled_check)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addLayout(form)

        # Empfänger
        form.addRow(QLabel("<b>Empfänger (Firma)</b>"))
        self.recipient_company = QLineEdit()
        self.recipient_company.setPlaceholderText("z. B. Musterfirma GmbH")
        form.addRow("Firma:", self.recipient_company)

        self.recipient_contact = QLineEdit()
        self.recipient_contact.setPlaceholderText("z. B. Frau Maria Schmidt – Personalabteilung")
        form.addRow("Kontakt:", self.recipient_contact)

        self.recipient_street = QLineEdit()
        self.recipient_street.setPlaceholderText("Straße Hausnr.")
        form.addRow("Straße:", self.recipient_street)

        self.recipient_postal_city = QLineEdit()
        self.recipient_postal_city.setPlaceholderText("PLZ Ort")
        form.addRow("PLZ/Ort:", self.recipient_postal_city)

        # Datum/Ort
        form.addRow(QLabel("<b>Datum & Ort</b>"))
        self.city = QLineEdit()
        self.city.setPlaceholderText("z. B. Berlin")
        form.addRow("Ort:", self.city)

        self.date = QLineEdit()
        self.date.setPlaceholderText("z. B. 2026-08-25 oder 25. August 2026 (leer = heute)")
        form.addRow("Datum:", self.date)

        self.city_date = QLineEdit()
        self.city_date.setPlaceholderText("Überschreibt Ort+Datum, z. B. Berlin, 25. August 2026")
        form.addRow("Ort, Datum (manuell):", self.city_date)

        # Betreff
        self.subject = QLineEdit()
        self.subject.setPlaceholderText("z. B. Bewerbung als Projektmanager (m/w/d)")
        form.addRow("Betreff:", self.subject)

        # Anrede
        self.salutation_combo = QComboBox()
        self.salutation_combo.setEditable(True)
        self.salutation_combo.addItems(SALUTATIONS)
        form.addRow("Anrede:", self.salutation_combo)

        # Hauptteil
        form.addRow(QLabel("<b>Anschreiben-Text</b>"))
        self.body = QPlainTextEdit()
        self.body.setPlaceholderText(
            "Einleitung (Bezug zur Stelle)…\n\nHauptteil (Erfahrungen, Erfolge, Bezug zur Firma)…\n\nSchluss (Verfügbarkeit, Gesprächswunsch)…"
        )
        self.body.setMinimumHeight(220)
        lay.addWidget(self.body)

        # Grußformel
        self.closing = QLineEdit()
        self.closing.setPlaceholderText("z. B. Mit freundlichen Grüßen")
        form.addRow("Grußformel:", self.closing)

        # Anlagen
        self.enclosures = QLineEdit()
        self.enclosures.setPlaceholderText("z. B. Lebenslauf, Zeugnisse")
        form.addRow("Anlagen:", self.enclosures)

        # Verbinde Signale
        for w in (self.recipient_company, self.recipient_contact, self.recipient_street,
                  self.recipient_postal_city, self.city, self.date, self.city_date,
                  self.subject, self.closing, self.enclosures):
            w.textChanged.connect(self._save)
        self.salutation_combo.currentTextChanged.connect(self._save)
        self.salutation_combo.editTextChanged.connect(self._save)
        self.body.textChanged.connect(self._save)

        lay.addStretch(1)

    def bind(self, resume) -> None:
        """Bindet ein (ggf. neu geladenes) Resume und lädt dessen Daten."""
        self.resume = resume
        self._resume_id = id(resume)
        self._load()

    def _load(self) -> None:
        self._loading = True
        try:
            cl = self.resume.cover_letter
            self.enabled_check.setChecked(bool(cl.get("enabled")))
            self.recipient_company.setText(str(cl.get("recipient_company") or ""))
            self.recipient_contact.setText(str(cl.get("recipient_contact") or ""))
            self.recipient_street.setText(str(cl.get("recipient_street") or ""))
            self.recipient_postal_city.setText(str(cl.get("recipient_postal_city") or ""))
            self.city.setText(str(cl.get("city") or self.resume.personal.get("city") or ""))
            self.date.setText(str(cl.get("date") or ""))
            self.city_date.setText(str(cl.get("city_date") or ""))
            self.subject.setText(str(cl.get("subject") or ""))
            # Anrede combo
            sal = str(cl.get("salutation") or "")
            idx = self.salutation_combo.findText(sal)
            if idx >= 0:
                self.salutation_combo.setCurrentIndex(idx)
            else:
                self.salutation_combo.setCurrentText(sal)
            self.body.setPlainText(str(cl.get("body") or ""))
            self.closing.setText(str(cl.get("closing") or ""))
            self.enclosures.setText(str(cl.get("enclosures") or ""))
        finally:
            self._loading = False

    def _save(self) -> None:
        # Während des Ladens keine Rückschreibung (würde Modell löschen)
        if self._loading:
            return
        cl = self.resume.cover_letter
        cl["enabled"] = bool(self.enabled_check.isChecked())
        cl["recipient_company"] = self.recipient_company.text().strip()
        cl["recipient_contact"] = self.recipient_contact.text().strip()
        cl["recipient_street"] = self.recipient_street.text().strip()
        cl["recipient_postal_city"] = self.recipient_postal_city.text().strip()
        cl["city"] = self.city.text().strip()
        cl["date"] = self.date.text().strip()
        cl["city_date"] = self.city_date.text().strip()
        cl["subject"] = self.subject.text().strip()
        cl["salutation"] = self.salutation_combo.currentText().strip()
        cl["body"] = self.body.toPlainText().strip()
        cl["closing"] = self.closing.text().strip()
        cl["enclosures"] = self.enclosures.text().strip()
        # Settings-Sync für Rückwärtskompatibilität
        self.resume.settings["include_cover_letter"] = bool(cl["enabled"])
        self.on_change()

    def refresh(self) -> None:
        self._load()
