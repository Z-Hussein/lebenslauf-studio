#!/usr/bin/env python3
"""
Lebenslauf Studio – Startpunkt der Anwendung.

Startet die lokale Desktop-GUI (PySide6). Alle Daten bleiben lokal.
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main() -> int:
    # High-DPI-Rendering aktivieren (Windows)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Lebenslauf Studio")
    app.setOrganizationName("LebenslaufStudio")
    app.setApplicationDisplayName("Lebenslauf Studio")

    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Gespeichertes Farbschema anwenden (Hell/Dunkel/System)
    from PySide6.QtCore import QSettings
    from app.ui.theme import SETTINGS_KEY, apply_theme
    stored = QSettings().value(SETTINGS_KEY, "system")
    if stored not in ("system", "light", "dark"):
        stored = "system"
    apply_theme(app, stored)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
