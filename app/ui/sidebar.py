"""
Sidebar: Vorlagenauswahl, Abschnittsliste (mit Drag & Drop) und
Abschnittsverwaltung (Hinzufügen, Verschieben, Duplizieren, Löschen)
sowie Zugriff auf die Design-Einstellungen.
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..models.section import SECTION_TITLES
from ..templates import TEMPLATE_ORDER, get_template
from .dialogs import DesignSettingsDialog, SectionPickerDialog

PERSONAL_ID = -1  # Kennung für den festen Eintrag "Persönliche Daten"
COVER_ID = -2  # Anschreiben


class SidebarWidget(QWidget):
    """Linke Seitenleiste des Hauptfensters."""

    section_selected = Signal(int)          # Index in resume.sections bzw. PERSONAL_ID
    sections_reordered = Signal()           # nach Drag & Drop
    template_changed = Signal(str)          # neuer Vorlagenname
    design_changed = Signal()               # Design-Einstellungen übernommen
    add_section_requested = Signal(object, str)  # (SectionType, Titel für eigene Abschnitte)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.resume = None
        self._loading = False  # verhindert Signale beim Wiederaufbau

        self.setFixedWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 4, 8)

        # ------------------------------------------------------------------
        # Vorlagen
        # ------------------------------------------------------------------
        cap = QLabel("VORLAGE")
        cap.setProperty("cssClass", "caption")
        layout.addWidget(cap)

        self.template_combo = QComboBox()
        for name in TEMPLATE_ORDER:
            style = get_template(name)
            self.template_combo.addItem(name)
            self.template_combo.setItemData(
                self.template_combo.count() - 1, style.description, Qt.ItemDataRole.ToolTipRole
            )
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        layout.addWidget(self.template_combo)

        self.template_desc = QLabel("")
        self.template_desc.setWordWrap(True)
        self.template_desc.setProperty("cssClass", "hint")
        layout.addWidget(self.template_desc)

        layout.addSpacing(12)

        # ------------------------------------------------------------------
        # Abschnitte
        # ------------------------------------------------------------------
        cap2 = QLabel("ABSCHNITTE")
        cap2.setProperty("cssClass", "caption")
        layout.addWidget(cap2)

        hint = QLabel("Reihenfolge = Reihenfolge im PDF. Per Drag & Drop verschiebbar.")
        hint.setWordWrap(True)
        hint.setProperty("cssClass", "hint")
        layout.addWidget(hint)

        self.section_list = QListWidget()
        self.section_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.section_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.section_list.itemSelectionChanged.connect(self._on_selection)
        self.section_list.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.section_list, 1)

        # Kontextmenü der Liste
        self.section_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.section_list.customContextMenuRequested.connect(self._show_context_menu)

        # Buttons (System-Icons statt Emoji: robust bei allen Fonts/HiDPI)
        from PySide6.QtWidgets import QApplication as _QApp
        _style = _QApp.instance().style() if _QApp.instance() else self.style()

        def _icon(name: str):
            try:
                from PySide6.QtWidgets import QStyle
                return _style.standardIcon(getattr(QStyle.StandardPixmap, name))
            except Exception:
                from PySide6.QtGui import QIcon
                return QIcon()

        btn_row = QHBoxLayout()
        self.btn_up = QPushButton(_icon("SP_ArrowUp"), "")
        self.btn_up.setToolTip("Abschnitt nach oben verschieben")
        self.btn_up.setStatusTip("Abschnitt nach oben verschieben")
        self.btn_up.clicked.connect(lambda checked=False: self.move_current(-1))
        self.btn_down = QPushButton(_icon("SP_ArrowDown"), "")
        self.btn_down.setToolTip("Abschnitt nach unten verschieben")
        self.btn_down.setStatusTip("Abschnitt nach unten verschieben")
        self.btn_down.clicked.connect(lambda checked=False: self.move_current(+1))
        btn_row.addWidget(self.btn_up)
        btn_row.addWidget(self.btn_down)

        self.btn_dup = QPushButton(_icon("SP_FileIcon"), "Duplizieren")
        self.btn_dup.setToolTip("Abschnitt duplizieren (nur eigene Abschnitte)")
        self.btn_dup.setStatusTip("Abschnitt duplizieren")
        self.btn_dup.clicked.connect(self.duplicate_current)
        btn_row.addWidget(self.btn_dup)
        layout.addLayout(btn_row)

        btn_row2 = QHBoxLayout()
        self.btn_delete = QPushButton(_icon("SP_TrashIcon"), "Löschen")
        self.btn_delete.setToolTip("Ausgewählten Abschnitt löschen")
        self.btn_delete.setStatusTip("Ausgewählten Abschnitt löschen")
        self.btn_delete.clicked.connect(self.delete_current)
        btn_row2.addWidget(self.btn_delete)
        layout.addLayout(btn_row2)

        self.btn_add = QPushButton(_icon("SP_FileDialogNewFolder"), "+ Abschnitt hinzufügen")
        self.btn_add.setMinimumHeight(34)
        self.btn_add.setToolTip("Neuen Abschnitt ans Ende der Liste anfügen")
        self.btn_add.setStatusTip("Neuen Abschnitt hinzufügen")
        self.btn_add.clicked.connect(self._open_picker)
        layout.addWidget(self.btn_add)

        # Entf-Taste löscht den gewählten Abschnitt
        from PySide6.QtCore import Qt as _Qt
        from PySide6.QtGui import QShortcut, QKeySequence
        self._del_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.section_list)
        self._del_shortcut.setContext(_Qt.ShortcutContext.WidgetShortcut)
        self._del_shortcut.activated.connect(self.delete_current)

        layout.addSpacing(12)

        # ------------------------------------------------------------------
        # Design-Einstellungen
        # ------------------------------------------------------------------
        self.btn_design = QPushButton(_icon("SP_ComputerIcon"), "Design-Einstellungen")
        self.btn_design.setMinimumHeight(32)
        self.btn_design.setToolTip("Akzent-/Hintergrundfarbe, Schrift, Ränder und Abstände")
        self.btn_design.setStatusTip("Design-Einstellungen öffnen")
        self.btn_design.clicked.connect(self.open_design_settings)
        layout.addWidget(self.btn_design)
        layout.addStretch(0)

    # ------------------------------------------------------------------
    # Modell-Anbindung
    # ------------------------------------------------------------------

    def set_resume(self, resume) -> None:
        self.resume = resume
        self.rebuild()

    def rebuild(self) -> None:
        """Liste aus dem Modell neu aufbauen (Auswahl bleibt per Index erhalten)."""
        if self.resume is None:
            return
        self._loading = True
        try:
            # Auswahl anhand der gespeicherten Kennung merken (nicht per Typ,
            # da doppelte Typen sonst die falsche Zeile wiederherstellen).
            prev_row = self.section_list.currentRow()
            prev_data = (
                self.section_list.item(prev_row).data(Qt.ItemDataRole.UserRole)
                if 0 <= prev_row < self.section_list.count()
                else PERSONAL_ID
            )
            self.section_list.clear()

            personal_item = QListWidgetItem("Persönliche Daten")
            personal_item.setData(Qt.ItemDataRole.UserRole, PERSONAL_ID)
            self.section_list.addItem(personal_item)

            # Anschreiben als fester Eintrag (nicht verschiebbar)
            cover_item = QListWidgetItem("Anschreiben")
            cover_item.setData(Qt.ItemDataRole.UserRole, COVER_ID)
            # Grau wenn deaktiviert, fett wenn aktiv
            is_enabled = bool(self.resume.cover_letter.get("enabled"))
            cover_item.setForeground(Qt.GlobalColor.darkGreen if is_enabled else Qt.GlobalColor.gray)
            # Nicht per Drag & Drop verschiebbar
            cover_item.setFlags(cover_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            self.section_list.addItem(cover_item)

            for i, section in enumerate(self.resume.sections):
                stype = str(section.get("type", ""))
                title = str(section.get("title") or SECTION_TITLES.get(stype, "Abschnitt"))
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, i)
                if not _section_has_content(section):
                    item.setForeground(Qt.GlobalColor.gray)
                self.section_list.addItem(item)

            # Auswahl wiederherstellen: gleiche Kennung suchen, sonst
            # nächstgelegene Zeile (eingeklemmt auf gültigen Bereich).
            restored = None
            if isinstance(prev_data, int):
                for r in range(self.section_list.count()):
                    if self.section_list.item(r).data(Qt.ItemDataRole.UserRole) == prev_data:
                        # Index-Kennungen alterner Abschnitte sind nach
                        # Umbau ungültig -> nur feste IDs übernehmen.
                        if prev_data in (PERSONAL_ID, COVER_ID):
                            restored = r
                        break
            if restored is None:
                if prev_data in (PERSONAL_ID, COVER_ID):
                    restored = 0 if prev_data == PERSONAL_ID else 1
                else:
                    restored = min(max(prev_row, 0), self.section_list.count() - 1)
            self.section_list.setCurrentRow(max(0, restored))

            # Vorlage anzeigen
            idx = self.template_combo.findText(self.resume.template)
            self.template_combo.setCurrentIndex(max(0, idx))
            style = get_template(self.resume.template)
            self.template_desc.setText(style.description)
        finally:
            self._loading = False

    def current_index(self) -> int:
        """Gibt den aktuellen Abschnittsindex zurück (-1 = Persönlich, -2 = Anschreiben)."""
        row = self.section_list.currentRow()
        if row < 0:
            return PERSONAL_ID
        data = self.section_list.item(row).data(Qt.ItemDataRole.UserRole)
        if data in (PERSONAL_ID, COVER_ID):
            return int(data)
        return int(data)

    # ------------------------------------------------------------------
    # Signale
    # ------------------------------------------------------------------

    def _on_template_changed(self, name: str) -> None:
        if self._loading or self.resume is None:
            return
        self.resume.template = name
        style = get_template(name)
        self.template_desc.setText(style.description)
        self.template_changed.emit(name)

    def _on_selection(self) -> None:
        if self._loading:
            return
        self.section_selected.emit(self.current_index())

    def _on_rows_moved(self, *args) -> None:
        """Nach Drag & Drop: Reihenfolge ins Modell übernehmen."""
        if self._loading or self.resume is None:
            return
        order = []
        for row in range(self.section_list.count()):
            data = self.section_list.item(row).data(Qt.ItemDataRole.UserRole)
            if data in (PERSONAL_ID, COVER_ID):
                continue
            order.append(int(data))
        # Persönliche Daten + Anschreiben bleiben immer oben; Rest in Widget-Reihenfolge
        new_sections = [self.resume.sections[i] for i in order]
        self.resume.sections[:] = new_sections
        self.sections_reordered.emit()

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        act_edit_up = QAction("Nach oben verschieben", menu)
        act_edit_up.triggered.connect(lambda: self.move_current(-1))
        act_edit_down = QAction("Nach unten verschieben", menu)
        act_edit_down.triggered.connect(lambda: self.move_current(+1))
        act_dup = QAction("Duplizieren", menu)
        act_dup.triggered.connect(self.duplicate_current)
        act_del = QAction("Löschen", menu)
        act_del.triggered.connect(self.delete_current)
        for a in (act_edit_up, act_edit_down):
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(act_dup)
        menu.addAction(act_del)
        menu.exec(self.section_list.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Aktionen
    # ------------------------------------------------------------------

    def move_current(self, delta: int) -> None:
        row = self.section_list.currentRow()
        if self.resume is None:
            return
        data = self.section_list.item(row).data(Qt.ItemDataRole.UserRole) if row >= 0 else None
        if data in (PERSONAL_ID, COVER_ID):
            return
        index = int(data)
        if self.resume.move_section(index, delta):
            self.rebuild()
            self.sections_reordered.emit()

    def duplicate_current(self) -> None:
        row = self.section_list.currentRow()
        if self.resume is None:
            return
        data = self.section_list.item(row).data(Qt.ItemDataRole.UserRole) if row >= 0 else None
        if data in (PERSONAL_ID, COVER_ID):
            QMessageBox.information(
                self, "Duplizieren",
                "Persönliche Daten / Anschreiben können nicht dupliziert werden.\n"
                "Wählen Sie einen normalen Abschnitt aus."
            )
            return
        index = int(data)
        result = self.resume.duplicate_section(index)
        if result is None:
            QMessageBox.information(
                self, "Duplizieren",
                "Standardabschnitte können nicht doppelt vorkommen.\n"
                "Nur eigene Abschnitte können dupliziert werden."
            )
            return
        self.rebuild()
        self.sections_reordered.emit()

    def delete_current(self) -> None:
        row = self.section_list.currentRow()
        if self.resume is None:
            return
        data = self.section_list.item(row).data(Qt.ItemDataRole.UserRole) if row >= 0 else None
        if data in (PERSONAL_ID, COVER_ID):
            QMessageBox.information(
                self, "Löschen",
                "Persönliche Daten / Anschreiben können nicht gelöscht werden."
            )
            return
        index = int(data)
        confirm = QMessageBox.question(
            self, "Abschnitt löschen",
            f'Abschnitt "{self.resume.sections[index].get("title")}" wirklich löschen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.resume.remove_section(index)
        self.rebuild()
        self.sections_reordered.emit()

    def _open_picker(self) -> None:
        existing = {s.get("type") for s in self.resume.sections} if self.resume else set()
        dlg = SectionPickerDialog(self, existing)
        if dlg.exec() != SectionPickerDialog.DialogCode.Accepted:
            return
        if dlg.selected_type is not None:
            # Titel wird mit übergeben (kein "letzter Eintrag"-Raten im Empfänger)
            self.add_section_requested.emit(dlg.selected_type, dlg.custom_title or "")

    def open_design_settings(self) -> None:
        if self.resume is None:
            return
        # Vorlagen-Standard für "Automatisch": Terminal dunkel, sonst Weiß
        style = get_template(self.resume.template)
        if getattr(style, "dark_mode", False):
            default_bg = getattr(style, "page_background", "#0C0B09") or "#0C0B09"
        else:
            default_bg = "#FFFFFF"
        dlg = DesignSettingsDialog(self, self.resume.settings, default_background=default_bg)
        if dlg.exec() != DesignSettingsDialog.DialogCode.Accepted:
            return
        dlg.apply_to_settings()
        self.design_changed.emit()


# ---------------------------------------------------------------------------
# Hilfsfunktion
# ---------------------------------------------------------------------------


def _section_has_content(section: dict) -> bool:
    """Prüft grob, ob ein Abschnitt Inhalt hat (für graue Darstellung)."""
    data = section.get("data") or {}
    if data.get("content"):
        return True
    for key in ("entries", "skills", "languages"):
        if data.get(key):
            return True
    if data.get("items"):
        return True
    return False
