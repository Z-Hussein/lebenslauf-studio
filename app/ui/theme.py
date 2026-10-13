"""
Zentrales App-Theme (QSS): Hell/Dunkel/System.

Statt verstreuter Inline-Styles liegt das Erscheinungsbild hier an einem
Ort. `apply_theme()` wird beim Start und bei Menü-Wechsel aufgerufen,
die Wahl wird per QSettings gespeichert.
"""

from typing import Literal

ThemeScheme = Literal["system", "light", "dark"]

SETTINGS_KEY = "ui/theme"

LIGHT_QSS = """
QMainWindow, QWidget { font-size: 13px; }
QMenuBar { padding: 2px; }
QStatusBar { font-size: 12px; }
QPushButton { padding: 5px 12px; border-radius: 5px; }
QPushButton:disabled { opacity: 0.55; }
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    padding: 5px; border-radius: 5px;
}
QListWidget { border-radius: 6px; padding: 3px; }
QListWidget::item { padding: 5px 6px; border-radius: 4px; }
QSplitter::handle { width: 2px; }
QSplitter::handle:hover { background: #1F4E79; }
QToolTip { padding: 4px; }
QLabel[cssClass="caption"] { letter-spacing: 1px; font-size: 11px; }
QLabel[cssClass="hint"] { font-size: 11px; }
QLabel[cssClass="welcome"] { font-size: 14px; }
"""

DARK_QSS = """
* { font-size: 13px; }
QWidget { background-color: #232629; color: #E8E6E1; }
QMainWindow { background-color: #232629; }
QMenuBar { background-color: #2D3033; padding: 2px; }
QMenuBar::item:selected { background-color: #3A3E42; border-radius: 4px; }
QMenu { background-color: #2D3033; border: 1px solid #45494D; }
QMenu::item:selected { background-color: #1F4E79; }
QStatusBar { background-color: #2D3033; font-size: 12px; }
QPushButton { background-color: #3A3E42; border: 1px solid #4A4F54; padding: 5px 12px; border-radius: 5px; }
QPushButton:hover { background-color: #454A4F; border-color: #1F4E79; }
QPushButton:pressed { background-color: #1F4E79; }
QPushButton:disabled { color: #8A8F94; }
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1B1D1F; border: 1px solid #45494D; padding: 5px; border-radius: 5px;
    selection-background-color: #1F4E79;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border-color: #1F4E79; }
QListWidget { background-color: #1B1D1F; border: 1px solid #45494D; border-radius: 6px; padding: 3px; }
QListWidget::item:selected { background-color: #1F4E79; border-radius: 4px; }
QListWidget::item { padding: 5px 6px; border-radius: 4px; }
QComboBox QAbstractItemView { background-color: #2D3033; selection-background-color: #1F4E79; }
QScrollBar:vertical, QScrollBar:horizontal { background: #2D3033; border: none; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #4A4F54; border-radius: 4px; min-height: 24px; min-width: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QSplitter::handle { background: #2D3033; width: 2px; }
QSplitter::handle:hover { background: #1F4E79; }
QTabWidget::pane { border: 1px solid #45494D; }
QTabBar::tab { background: #2D3033; padding: 6px 12px; border-top-left-radius: 5px; border-top-right-radius: 5px; }
QTabBar::tab:selected { background: #3A3E42; }
QToolTip { background-color: #2D3033; color: #E8E6E1; border: 1px solid #4A4F54; padding: 4px; }
QCheckBox, QLabel { background: transparent; }
QDialogButtonBox QPushButton { min-width: 80px; }
"""


def resolve_scheme(scheme: ThemeScheme) -> str:
    """Löst 'system' anhand des OS-Farbschemas auf -> 'light'/'dark'."""
    if scheme in ("light", "dark"):
        return scheme
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        hints = QApplication.instance().styleHints() if QApplication.instance() else None
        if hints is not None:
            return "dark" if hints.colorScheme() == Qt.ColorScheme.Dark else "light"
    except Exception:
        pass
    return "light"


def qss_for(scheme: ThemeScheme) -> str:
    """Gibt das passende Stylesheet zurück ('' für hell/System-hell)."""
    return DARK_QSS if resolve_scheme(scheme) == "dark" else LIGHT_QSS


def apply_theme(app, scheme: ThemeScheme) -> str:
    """Wendet das Theme auf die QApplication an. Gibt 'light'/'dark' zurück."""
    resolved = resolve_scheme(scheme)
    app.setStyleSheet(DARK_QSS if resolved == "dark" else LIGHT_QSS)
    return resolved
