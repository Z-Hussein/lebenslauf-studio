# Installation

## Voraussetzungen

- **Python 3.11 oder neuer** → <https://www.python.org/downloads/>
  (Windows: bei der Installation „Add python.exe to PATH“ anhaken)
- ca. 150 MB freier Speicher (abhängig von der Python-Installation)
- Keine Internetverbindung nötig – außer einmalig für `pip install`

Prüfen, ob Python da ist:

```bash
python --version   # sollte 3.11+ ausgeben
```

## Schritt für Schritt (empfohlen: virtuelle Umgebung)

```bash
# 1. In den Projektordner wechseln
cd lebenslauf-studio

# 2. Virtuelle Umgebung anlegen (einmalig)
python -m venv .venv

# 3. Umgebung aktivieren
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# 4. Abhängigkeiten installieren
pip install -r requirements.txt

# 5. Starten (Umgebung muss aktiviert sein)
python main.py
```

> Tipp Windows: Falls `Activate.ps1` blockiert wird, einmalig ausführen:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
> Alternativ direkt ohne Aktivieren starten:
> `.venv\Scripts\python.exe main.py`

## Was wird installiert?

| Paket | Wofür |
|---|---|
| PySide6 | Fenster, Buttons, Formulare (Desktop-Oberfläche) |
| reportlab | Erzeugt die PDF-Dateien |
| Pillow | Bilder (Foto, Zertifikat-Scans) |
| pypdfium2 | Rendert die Live-Vorschau |
| fonttools | Erkennt Sonderzeichen für den Schrift-Fallback |

Alle Pakete sind Open Source und laufen vollständig lokal.

## Schriften & Icons

Die App bringt eigene Schriften in `assets/fonts/` mit (u. a. JetBrains
Mono für den Terminal-Stil) und registriert zusätzlich Systemschriften.
Eigene `.ttf`-Dateien einfach in `assets/fonts/` legen – sie erscheinen
nach einem Neustart in *Design-Einstellungen → Schriftart*.

## Probleme bei der Installation?

- `python` nicht gefunden → Python neu installieren **mit PATH-Option**,
  Terminal neu öffnen.
- `pip install` schlägt fehl → `python -m pip install --upgrade pip`
  und erneut versuchen.
- `ModuleNotFoundError: PySide6` beim Start → die virtuelle Umgebung war
  nicht aktiviert (siehe Schritt 3) oder `pip install -r requirements.txt`
  lief in der falschen Umgebung.
- Sehr alte Rechner: Der erste Start kann einige Sekunden dauern (Schrift-
  Registrierung), danach geht es schneller.

Weiter: [Erste Schritte](getting-started.md)
