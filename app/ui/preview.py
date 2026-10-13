"""
Live-Vorschau: rendert die A4-Seiten des aktuellen Lebenslaufs.

Die PDF-Erzeugung läuft in einem Hintergrund-Thread (debounced),
damit die Oberfläche flüssig bleibt. Die Seiten werden mit pypdfium2
in Bilder gerendert und angezeigt. Navigation zwischen mehreren Seiten
wird unterstützt ("Seite X / Y").
"""

import threading
from typing import Optional

import pypdfium2 as pdfium
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..pdf.generator import render_pdf_bytes


def pil_to_qimage(pil_image) -> QImage:
    """Konvertiert ein PIL-Bild in ein eigenständiges QImage."""
    img = pil_image.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, img.width * 4, QImage.Format.Format_RGBA8888)
    return qimg.copy()  # Kopie, da der Puffer sonst ungültig wird


class PreviewWidget(QWidget):
    """Rechte Vorschaufläche des Hauptfensters."""

    #: wird nach erfolgreichem Neuaufbau gesendet (Anzahl Seiten)
    pages_changed = Signal(int)
    _pdf_ready = Signal(int, bytes)
    _pdf_error = Signal(int, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.resume = None

        self._pdf_doc: Optional[pdfium.PdfDocument] = None
        self._page_count: int = 0
        self._current_page: int = 0
        self._generation_id: int = 0  # nur das neueste Ergebnis verwenden
        self._zoom: float = 1.0       # manueller Zoomfaktor
        self._fit_width: bool = True  # Breite an Ansicht anpassen

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(8, 6, 8, 2)
        title = QLabel("<b>Live-Vorschau</b>")
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        # Scrollbereich für die Seitendarstellung
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setStyleSheet("background:#525659; border:none;")
        layout.addWidget(self.scroll, 1)

        self.page_label = QLabel("Vorschau wird erstellt …")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("color:white;")
        self.scroll.setWidget(self.page_label)

        # Fußleiste mit Navigation
        footer = QHBoxLayout()
        footer.setContentsMargins(8, 4, 8, 6)

        from PySide6.QtWidgets import QStyle
        _style = self.style()
        self.btn_prev = QPushButton(
            _style.standardIcon(QStyle.StandardPixmap.SP_ArrowLeft), "Zurück"
        )
        self.btn_prev.setEnabled(False)
        self.btn_prev.setToolTip("Vorherige Seite (Bild auf/ab geht auch)")
        self.btn_prev.clicked.connect(lambda checked=False: self._go_page(-1))
        footer.addWidget(self.btn_prev)

        self.page_info = QLabel("–")
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.addWidget(self.page_info, 1)

        self.btn_next = QPushButton(
            _style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight), "Weiter"
        )
        self.btn_next.setEnabled(False)
        self.btn_next.setToolTip("Nächste Seite")
        self.btn_next.clicked.connect(lambda checked=False: self._go_page(+1))
        footer.addWidget(self.btn_next)

        footer.addSpacing(12)

        # Zoom-Steuerung
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedWidth(32)
        self.btn_zoom_out.setToolTip("Verkleinern")
        self.btn_zoom_out.clicked.connect(lambda checked=False: self._change_zoom(0.8))
        footer.addWidget(self.btn_zoom_out)

        self.zoom_label = QLabel("Einpassen")
        self.zoom_label.setMinimumWidth(64)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.addWidget(self.zoom_label)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedWidth(32)
        self.btn_zoom_in.setToolTip("Vergrößern")
        self.btn_zoom_in.clicked.connect(lambda checked=False: self._change_zoom(1.25))
        footer.addWidget(self.btn_zoom_in)

        self.btn_fit = QPushButton("Einpassen")
        self.btn_fit.setToolTip("Seitenbreite an Fenster anpassen")
        self.btn_fit.setCheckable(True)
        self.btn_fit.setChecked(True)
        self.btn_fit.toggled.connect(self._set_fit_width)
        footer.addWidget(self.btn_fit)

        layout.addLayout(footer)

        # Debounce-Timer für Aktualisierungen
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(500)  # ms
        self._timer.timeout.connect(self._start_generation)

        # Thread-sichere Signale für Worker -> GUI
        self._pdf_ready.connect(self._apply_pdf)
        self._pdf_error.connect(self._show_error)

    # ------------------------------------------------------------------
    # Öffentliche API
    # ------------------------------------------------------------------

    def set_resume(self, resume) -> None:
        self.resume = resume

    def schedule_update(self) -> None:
        """Änderung registrieren – Vorschau wird kurz verzögert neu erzeugt."""
        if self.resume is None:
            return
        self._timer.start()

    # ------------------------------------------------------------------
    # Hintergrund-Generierung
    # ------------------------------------------------------------------

    def _start_generation(self) -> None:
        if self.resume is None:
            return
        self._generation_id += 1
        gen_id = self._generation_id
        # Snapshot des aktuellen Standes, damit der Worker nicht mit dem GUI-Thread kollidiert.
        # Schlägt die Kopie fehl, wird dieses Update übersprungen (lieber keine
        # Vorschau als ein Race auf dem geteilten Live-Objekt).
        try:
            from copy import deepcopy
            resume_snapshot = deepcopy(self.resume)
        except Exception:
            return

        def worker() -> None:
            try:
                data = render_pdf_bytes(resume_snapshot)
                self._pdf_ready.emit(gen_id, data)
            except Exception as exc:  # noqa: BLE001
                self._pdf_error.emit(gen_id, str(exc))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _apply_pdf(self, gen_id: int, data: bytes) -> None:
        if gen_id != self._generation_id or not data:
            return
        try:
            doc = pdfium.PdfDocument(data)
            if self._pdf_doc is not None:
                try:
                    self._pdf_doc.close()
                except Exception:
                    pass
            self._pdf_doc = doc
            self._page_count = len(doc)
            self._current_page = min(self._current_page, max(0, self._page_count - 1))
            self._render_current()
            self.pages_changed.emit(self._page_count)
        except Exception as exc:  # noqa: BLE001
            self._show_error(gen_id, str(exc))

    def _show_error(self, gen_id: int, message: str) -> None:
        if gen_id != self._generation_id:
            return
        self.page_label.setText(
            "Vorschau nicht möglich.\n\nBitte Eingaben prüfen.\n(Fehler: "
            + message[:120]
            + ")"
        )

    # ------------------------------------------------------------------
    # Rendering & Navigation
    # ------------------------------------------------------------------

    def _change_zoom(self, factor: float) -> None:
        self._zoom = min(3.0, max(0.4, self._zoom * factor))
        self._fit_width = False
        self.btn_fit.setChecked(False)
        self._update_zoom_label()
        self._render_current()

    def _set_fit_width(self, checked: bool) -> None:
        self._fit_width = checked
        self._update_zoom_label()
        self._render_current()

    def _update_zoom_label(self) -> None:
        if self._fit_width:
            self.zoom_label.setText("Einpassen")
        else:
            self.zoom_label.setText(f"{int(round(self._zoom * 100))} %")

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt-Namenskonvention)
        super().resizeEvent(event)
        # Im Einpassen-Modus reicht Neurendern (PDF liegt bereits vor)
        if self._fit_width and self._pdf_doc is not None:
            self._render_current()

    def _render_current(self) -> None:
        if self._pdf_doc is None or self._page_count == 0:
            return
        page_index = max(0, min(self._current_page, self._page_count - 1))
        try:
            page = self._pdf_doc[page_index]
            if self._fit_width:
                viewport_w = max(200, self.scroll.viewport().width() - 24)
                base_w = page.get_width()
                scale = (viewport_w / base_w) if base_w > 0 else 1.0
            else:
                base_w = page.get_width()
                scale = (760 / base_w if base_w > 0 else 1.0) * self._zoom
            scale = min(4.0, max(0.2, scale))
            bitmap = page.render(scale=scale)
            pil_img = bitmap.to_pil()
            page.close()
        except Exception as exc:  # noqa: BLE001
            self.page_label.setText(f"Seite kann nicht dargestellt werden.\n({exc})")
            return

        qimg = pil_to_qimage(pil_img)
        pix = QPixmap.fromImage(qimg)
        self.page_label.setPixmap(pix)
        self.page_label.resize(pix.size())

        self.page_info.setText(f"Seite {page_index + 1} / {self._page_count}")
        has_multi = self._page_count > 1
        self.btn_prev.setEnabled(has_multi and page_index > 0)
        self.btn_next.setEnabled(has_multi and page_index < self._page_count - 1)

    def _go_page(self, delta: int) -> None:
        new_page = self._current_page + delta
        if 0 <= new_page < self._page_count:
            self._current_page = new_page
            self._render_current()
