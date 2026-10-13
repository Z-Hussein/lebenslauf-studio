"""
Hauptfenster des Lebenslauf Studio.

Verbindet Sidebar (Vorlagen & Abschnitte), Editorbereich und Live-Vorschau
und stellt die Dateiaktionen bereit (Neu, Öffnen, Speichern, PDF-Export).
"""

import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..models.section import SECTION_TITLES, SectionType
from ..storage.project_manager import PROJECT_FILTER, ProjectManager
from ..pdf.generator import generate_pdf
from ..utils.helpers import EXAMPLES_DIR, safe_str
from .dialogs import StartDialog
from .editor import EditorStack
from .preview import PreviewWidget
from .sidebar import COVER_ID, PERSONAL_ID, SidebarWidget


class MainWindow(QMainWindow):
    """Zentrales Anwendungsfenster."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lebenslauf Studio")
        self.resize(1400, 850)

        self.project_manager = ProjectManager()
        self.resume = self.project_manager.new_project()

        self._build_menu()
        self._build_ui()

        # Fenster-/Splitter-Geometrie wiederherstellen
        from PySide6.QtCore import QSettings
        saved_geo = QSettings().value("ui/geometry")
        if saved_geo is not None:
            try:
                self.restoreGeometry(saved_geo)
            except Exception:
                pass
        saved_split = QSettings().value("ui/splitter")
        if saved_split is not None:
            try:
                self.splitter.restoreState(saved_split)
            except Exception:
                pass

        # Vorschau initial erzeugen
        self.preview.set_resume(self.resume)
        self.sidebar.set_resume(self.resume)
        self.editor_stack.set_resume(self.resume)
        self._update_title()

        self.statusBar().showMessage("Bereit.")

        # Startdialog anzeigen
        QTimer_singleShot_start(self)

    # ------------------------------------------------------------------
    # UI-Aufbau
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&Datei")

        act_new = QAction("&Neu", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self.action_new)
        file_menu.addAction(act_new)

        act_open = QAction("Ö&ffnen …", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.action_open)
        file_menu.addAction(act_open)

        act_save = QAction("&Speichern", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self.action_save)
        file_menu.addAction(act_save)

        act_save_as = QAction("Speichern &unter …", self)
        act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        act_save_as.triggered.connect(lambda: self.action_save(force_dialog=True))
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_pdf = QAction("Bewerbung exportieren (Lebenslauf + Anschreiben + Zertifikate) …", self)
        act_pdf.setShortcut("Ctrl+E")
        act_pdf.triggered.connect(self.action_export_pdf)
        file_menu.addAction(act_pdf)

        act_pdf_cv = QAction("Nur Lebenslauf exportieren …", self)
        act_pdf_cv.triggered.connect(lambda: self.action_export_pdf(mode="cv_only"))
        file_menu.addAction(act_pdf_cv)

        act_pdf_cl = QAction("Nur Anschreiben exportieren …", self)
        act_pdf_cl.triggered.connect(lambda: self.action_export_pdf(mode="cover_only"))
        file_menu.addAction(act_pdf_cl)

        file_menu.addSeparator()

        act_quit = QAction("&Beenden", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = menu.addMenu("&Ansicht")
        from PySide6.QtGui import QActionGroup
        from .theme import SETTINGS_KEY, apply_theme
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_actions = {}
        for key, label in (("system", "&System"), ("light", "&Hell"), ("dark", "&Dunkel")):
            act = QAction(label, self, checkable=True)
            act.triggered.connect(lambda checked=False, k=key: self._set_theme(k))
            self._theme_group.addAction(act)
            view_menu.addAction(act)
            self._theme_actions[key] = act
        from PySide6.QtCore import QSettings
        stored = QSettings().value(SETTINGS_KEY, "system")
        if stored not in self._theme_actions:
            stored = "system"
        self._theme_actions[stored].setChecked(True)

        help_menu = menu.addMenu("&Hilfe")
        act_about = QAction("Ü&ber", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _set_theme(self, scheme: str) -> None:
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QApplication
        from .theme import SETTINGS_KEY, apply_theme
        QSettings().setValue(SETTINGS_KEY, scheme)
        apply_theme(QApplication.instance(), scheme)
        self.statusBar().showMessage(
            {"system": "Farbschema: System", "light": "Farbschema: Hell",
             "dark": "Farbschema: Dunkel"}[scheme], 3000
        )

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        # Links: Sidebar
        self.sidebar = SidebarWidget()
        splitter.addWidget(self.sidebar)

        # Mitte: Editoren
        self.editor_stack = EditorStack(on_change=self._on_data_changed)
        splitter.addWidget(self.editor_stack)

        # Rechts: Live-Vorschau
        preview_container = QWidget()
        pv_layout = QVBoxLayout(preview_container)
        pv_layout.setContentsMargins(0, 0, 0, 0)
        self.preview = PreviewWidget()
        pv_layout.addWidget(self.preview)
        splitter.addWidget(preview_container)

        splitter.setSizes([250, 520, 600])
        splitter.setStretchFactor(1, 1)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(2, False)
        self.splitter = splitter

        self.setCentralWidget(central)

        # Statusleiste
        status = QStatusBar()
        self.setStatusBar(status)
        self.path_label = QLabel("")
        status.addPermanentWidget(self.path_label)

        # Signale verbinden
        self.sidebar.section_selected.connect(self._on_section_selected)
        self.sidebar.sections_reordered.connect(self._on_data_changed)
        self.sidebar.template_changed.connect(lambda _: self._on_data_changed())
        self.sidebar.design_changed.connect(self._on_design_changed)
        self.sidebar.add_section_requested.connect(self._on_add_section)

    # ------------------------------------------------------------------
    # Reaktion auf Änderungen
    # ------------------------------------------------------------------

    def _on_data_changed(self) -> None:
        """Wird bei jeder Inhaltsänderung aufgerufen."""
        self.project_manager.dirty = True
        self.preview.schedule_update()
        self._update_title()

    def _on_design_changed(self) -> None:
        self._on_data_changed()
        self.statusBar().showMessage("Design-Einstellungen übernommen.", 3000)

    def _on_section_selected(self, index: int) -> None:
        # Kein Sidebar-Rebuild hier: Der würde Auswahl/Scrollposition
        # zurücksetzen und kann Auswahl-Schleifen auslösen.
        if index == PERSONAL_ID:
            self.editor_stack.show_personal()
        elif index == COVER_ID:
            self.editor_stack.show_cover_letter()
        elif 0 <= index < len(self.resume.sections):
            self.editor_stack.show_section(index, self.resume.sections[index])

    def _on_add_section(self, stype, custom_title: str = "") -> None:
        title = custom_title.strip() if stype == SectionType.CUSTOM else ""
        if not title:
            title = SECTION_TITLES.get(stype.value, stype.value.title())
        index = self.resume.add_section(stype, title)
        self.sidebar.rebuild()
        row = index + 2  # + Personal + Anschreiben
        self.sidebar.section_list.setCurrentRow(row)
        self.editor_stack.show_section(index, self.resume.sections[index])
        self._on_data_changed()

    def _update_title(self) -> None:
        name = self.resume.full_name()
        base = "Lebenslauf Studio"
        if name:
            base += f" – {name}"
        star = "*" if self.project_manager.dirty else ""
        self.setWindowTitle(f"{star}{base}")

    # ------------------------------------------------------------------
    # Datei-Aktionen
    # ------------------------------------------------------------------

    def action_new(self) -> None:
        if not self._confirm_discard():
            return
        self.resume = self.project_manager.new_project()
        self._after_project_replaced()
        self.statusBar().showMessage("Neues Projekt erstellt.", 3000)

    def action_open(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Projekt öffnen", "", PROJECT_FILTER
        )
        if not path:
            return
        try:
            self.resume = self.project_manager.load(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self, "Fehler beim Öffnen",
                "Das Projekt konnte nicht geöffnet werden.\n\n"
                "Bitte prüfen Sie, ob es sich um eine gültige "
                "Lebenslauf-Projektdatei handelt.",
            )
            return
        self._after_project_replaced()
        self.statusBar().showMessage(f"Projekt geladen: {os.path.basename(path)}", 4000)

    def action_save(self, force_dialog: bool = False) -> bool:
        try:
            if force_dialog or not self.project_manager.current_path:
                suggested = _suggest_filename(self.resume)
                path, _ = QFileDialog.getSaveFileName(
                    self, "Projekt speichern", suggested, PROJECT_FILTER
                )
                if not path:
                    return False
                if not path.lower().endswith(".json"):
                    path += ".json"
                self.project_manager.save(self.resume, path)
            else:
                self.project_manager.save(self.resume)
        except Exception:  # noqa: BLE001
            QMessageBox.critical(
                self, "Fehler beim Speichern",
                "Das Projekt konnte nicht gespeichert werden.\n"
                "Bitte überprüfen Sie den Speicherort und die Schreibrechte."
            )
            return False
        self._update_title()
        self.path_label.setText(self.project_manager.display_name())
        self.statusBar().showMessage("Projekt erfolgreich gespeichert.", 4000)
        return True

    def action_export_pdf(self, mode: str = "full") -> None:
        """
        mode: full = Lebenslauf + Anschreiben (falls aktiviert) + Zertifikate
              cv_only = nur Lebenslauf
              cover_only = nur Anschreiben
        """
        if mode == "cover_only" and not self.resume.cover_letter.get("enabled"):
            QMessageBox.information(self, "Kein Anschreiben", "Anschreiben ist deaktiviert.\nBitte im Bereich „Anschreiben“ aktivieren und ausfüllen.")
            return
        # Dateiname je nach Modus
        suffix = {"full": "_Bewerbung", "cv_only": "_Lebenslauf", "cover_only": "_Anschreiben"}.get(mode, "")
        base = _suggest_filename(self.resume, extension=".pdf")
        if suffix:
            root, ext = os.path.splitext(base)
            base = root + suffix + ext
        dlg_title = {"full": "Bewerbung als PDF speichern", "cv_only": "Lebenslauf als PDF speichern", "cover_only": "Anschreiben als PDF speichern"}.get(mode, "PDF speichern")
        path, _ = QFileDialog.getSaveFileName(self, dlg_title, base, "PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        # Auf einer KOPIE arbeiten: Das Live-Modell darf durch Modus-Umschaltung
        # (Anschreiben/Zertifikate an-aus) nie verändert werden.
        import copy
        export_resume = copy.deepcopy(self.resume)
        warnings: list = []
        try:
            if mode == "cv_only":
                export_resume.cover_letter["enabled"] = False
                export_resume.settings["include_certificates_appendix"] = False
                generate_pdf(export_resume, path, warnings_out=warnings)
            elif mode == "cover_only":
                from ..pdf.generator import render_cover_pdf_bytes
                with open(path, "wb") as fh:
                    fh.write(render_cover_pdf_bytes(export_resume))
            else:
                generate_pdf(export_resume, path, warnings_out=warnings)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self, "PDF konnte nicht erstellt werden",
                f"Die PDF-Datei konnte nicht erstellt werden.\n\nFehler: {exc}\n\nBitte überprüfen Sie die eingegebenen Daten und ob die Datei nicht gerade in einem anderen Programm geöffnet ist.",
            )
            return
        if warnings:
            self.statusBar().showMessage(
                f"PDF exportiert mit {len(warnings)} Hinweis(en): {path}", 8000
            )
            box = QMessageBox(self)
            box.setWindowTitle("PDF erstellt – mit Hinweisen")
            box.setIcon(QMessageBox.Icon.Warning)
            box.setText(f"PDF erfolgreich gespeichert:\n{path}\n\nBitte prüfen:")
            box.setDetailedText("\n\n".join(warnings))
            box.setStandardButtons(QMessageBox.StandardButton.Ok)
            box.exec()
        else:
            self.statusBar().showMessage(f"PDF exportiert: {path}", 5000)
            QMessageBox.information(self, "PDF erstellt", f"PDF erfolgreich gespeichert:\n{path}")

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------

    def _after_project_replaced(self) -> None:
        self.preview.set_resume(self.resume)
        self.sidebar.set_resume(self.resume)
        self.editor_stack.set_resume(self.resume)
        self.sidebar.rebuild()
        self.editor_stack.refresh_all()
        self.path_label.setText(self.project_manager.display_name())
        self._update_title()
        self.preview.schedule_update()

    def _confirm_discard(self) -> bool:
        if not self.project_manager.dirty:
            return True
        answer = QMessageBox.question(
            self, "Ungespeicherte Änderungen",
            "Es gibt ungespeicherte Änderungen.\nMöchten Sie sie zuerst speichern?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.action_save()
        return answer == QMessageBox.StandardButton.Discard

    def _show_about(self) -> None:
        from .. import __author__, __homepage__, __version__
        QMessageBox.information(
            self, "Über Lebenslauf Studio",
            f"<h3>Lebenslauf Studio {__version__}</h3>"
            "<p>Lokale App zum Erstellen professioneller deutscher "
            "Lebensläufe und Bewerbungsanschreiben mit PDF-Export.</p>"
            "<p>Alle Daten bleiben auf Ihrem Computer.</p>"
            f"<p>Entwickelt von {__author__}<br>"
            f'<a href="{__homepage__}">{__homepage__}</a></p>'
        )

    def run_start_flow(self) -> None:
        """Startauswahl: leer / Beispiel / bestehendes Projekt."""
        dlg = StartDialog(self)
        if dlg.exec() != StartDialog.DialogCode.Accepted:
            return
        if dlg.choice == StartDialog.RESULT_EXAMPLE:
            example_path = os.path.join(EXAMPLES_DIR, "example_resume.json")
            if os.path.exists(example_path):
                try:
                    self.resume = self.project_manager.load(example_path)
                    self._after_project_replaced()
                    self.statusBar().showMessage("Beispiel-Lebenslauf geladen.", 4000)
                    return
                except Exception:
                    pass
            self.statusBar().showMessage(
                "Beispieldatei nicht gefunden – leeres Projekt wurde erstellt.", 5000
            )
        elif dlg.choice == StartDialog.RESULT_OPEN:
            self.action_open()
            return
        # RESULT_EMPTY: nichts weiter zu tun

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt-Namenskonvention)
        if self._confirm_discard():
            try:
                from PySide6.QtCore import QSettings
                QSettings().setValue("ui/geometry", self.saveGeometry())
                QSettings().setValue("ui/splitter", self.splitter.saveState())
            except Exception:
                pass
            event.accept()
        else:
            event.ignore()


# ---------------------------------------------------------------------------
# Modulfunktionen
# ---------------------------------------------------------------------------


def _suggest_filename(resume, extension: str = ".json") -> str:
    name = safe_str(resume.full_name()).replace(" ", "_")
    base = f"Lebenslauf_{name}" if name else "Lebenslauf"
    documents = os.path.join(os.path.expanduser("~"), "Documents")
    if not os.path.isdir(documents):
        documents = os.path.expanduser("~")
    return os.path.join(documents, base + extension)


def QTimer_singleShot_start(window: MainWindow) -> None:
    """Startet den Begrüßungsdialog nach dem ersten Anzeigen des Fensters."""
    from PySide6.QtCore import QTimer

    QTimer.singleShot(120, window.run_start_flow)
