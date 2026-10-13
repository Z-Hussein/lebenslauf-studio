# Lebenslauf Studio

> Lokale Desktop-Anwendung zum Erstellen professioneller deutscher
> Lebensläufe und Bewerbungsanschreiben – mit Live-Vorschau und
> hochwertigem PDF-Export.

**Alle Daten bleiben ausschließlich auf Ihrem Computer.** Keine Cloud, kein
Login, keine Internetverbindung erforderlich.

📖 **Ausführliche Anleitungen:** siehe [`docs/`](docs/) (Installation,
Erste Schritte, Anschreiben, Vorlagen, PDF-Export, Projekte, FAQ).

---

## Funktionen

- Persönliche Daten inkl. optionalem Bewerbungsfoto (JPG/PNG)
- **Anschreiben-Editor** nach DIN 5008 (Empfänger, Datum, Betreff, Anrede, Text, Grußformel, Anlagen)
- Profil, Berufserfahrung, Ausbildung, Kenntnisse (mit Level-Balken im Terminal-Stil), Sprachen und viele weitere Abschnitte
- Eigene Abschnitte mit frei wählbarem Titel
- Abschnitte hinzufügen, verschieben (Buttons oder Drag & Drop), duplizieren und löschen (Entf-Taste)
- 13 Vorlagen: **Modern**, **Classic**, **Minimal**, **Professional**, **Creative**, **ZH Modern/Classic/Creative/Tech/Executive**, **Swiss**, **Nordic**, **Terminal**
- Design-Einstellungen: Akzentfarbe, **Hintergrundfarbe**, Schriftart (11 Schriften, inkl. Inter), Schriftgröße, Zeilenabstand, Seitenränder, Kontakt-Kürzel, Zertifikats-Anhang
- **App-Farbschema:** Hell / Dunkel / System (Menü *Ansicht*); Fenstergröße und Panel-Aufteilung werden gespeichert
- Live-Vorschau der A4-Seiten mit Seitennavigation und Zoom (Einpassen/+/−)
- PDF-Export in A4 mit korrekten Umlauten, eingebetteten Schriftarten und automatischem Sonderzeichen-Fallback (keine □-Kästchen); Warnungen bei fehlenden Dateien/Zeichen im Export-Dialog
- Projekte als JSON speichern (atomar, mit `.bak`-Sicherung), öffnen und wiederverwenden

## Installation

Python 3.11+ wird benötigt: https://www.python.org/downloads/

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Starten

```bash
python main.py
```

Beim Start können Sie wählen:

- **Leeren Lebenslauf erstellen** – frisches Projekt mit Standardabschnitten
- **Beispiel-Lebenslauf laden** – vollständiger fiktiver Lebenslauf (`examples/example_resume.json`)
- **Bestehendes Projekt öffnen** – zuvor gespeicherte JSON-Projektdatei laden

## Projektstruktur

```
lebenslauf_studio/
│
├── main.py                  # Startpunkt
├── requirements.txt         # Abhängigkeiten
├── README.md
│
├── app/
│   ├── models/
│   │   ├── resume.py        # Resume-Datenmodell + Abschnittsverwaltung
│   │   └── section.py       # Abschnittstypen & Eintrags-Klassen
│   │
│   ├── ui/
│   │   ├── main_window.py   # Hauptfenster
│   │   ├── sidebar.py       # Vorlagen- & Abschnittsverwaltung
│   │   ├── editor.py        # Editoren für alle Abschnitte
│   │   ├── preview.py       # Live-Vorschau (A4-Seiten)
│   │   ├── dialogs.py       # Dialoge (Start, Eingabe, Design)
│   │   └── widgets/
│   │
│   ├── templates/
│   │   ├── base.py          # TemplateStyle-Basis
│   │   ├── modern.py        # Modern – blau, einspaltig, ATS-freundlich
│   │   ├── classic.py       # Classic – traditionell deutsch (Serif)
│   │   ├── minimal.py       # Minimal – schwarz/weiß, ATS-freundlich
│   │   ├── professional.py  # Professional – Überschriftenbalken
│   │   └── creative.py      # Creative – Akzentfarbe, mehr Design
│   │
│   ├── pdf/
│   │   └── generator.py     # ReportLab-PDF-Erzeugung
│   │
│   ├── storage/
│   │   └── project_manager.py  # JSON laden/speichern
│   │
│   └── utils/
│       └── helpers.py       # Hilfsfunktionen
│
├── assets/
│   ├── icons/
│   └── fonts/
│
└── examples/
    └── example_resume.json  # Beispieldaten
```

## Verwendung

1. **Abschnitt links auswählen** → Formular erscheint in der Mitte
2. Daten eintragen – die **Vorschau rechts aktualisiert sich automatisch**
3. Über **+ Abschnitt hinzufügen** neue Abschnitte ergänzen
4. Reihenfolge per **Drag & Drop** oder ↑/↓-Buttons ändern
5. Vorlage oben in der Sidebar wechseln
6. Über **Datei → PDF exportieren** den Lebenslauf speichern

### Bewerbungsfoto

Im Bereich *Persönliche Daten* über **Foto auswählen** hinzufügen
(Formate: JPG, JPEG, PNG). Das Foto erscheint je nach Vorlage im Kopfbereich.
Ohne Foto bleibt das Layout intakt.

### Hintergrundfarbe

Über **🎨 Design-Einstellungen → Hintergrund** lässt sich die Seitenfarbe
des PDFs bei **jeder Vorlage** frei wählen (z. B. Creme `#FAF6EC`,
Dunkelblau `#1A1A2E` oder Weiß für *Terminal*).
Leer lassen = automatisch (Weiß, bzw. Dunkel bei *Terminal*); der
**Auto**-Button setzt zurück.
Die Textfarben passen sich automatisch an: dunkler Grund → heller Text
(inkl. Aufhellung einer zu dunklen Akzentfarbe), heller Grund → dunkler
Text. Die Live-Vorschau zeigt die Farbe sofort.

## PDF-Export

- Format A4
- Automatische Seitenumbrüche bei mehrseitigen Lebensläufen
- Deutsche Umlaute werden korrekt dargestellt
- Text bleibt maschinenlesbar (**ATS-freundlich** bei Modern, Minimal,
  Professional und Classic)

## JSON-Projekte

Der komplette Lebenslauf (Daten, Vorlage, Design-Einstellungen) wird als
JSON gespeichert:

- **Datei → Speichern / Speichern unter**
- **Datei → Öffnen**

Die Dateien lassen sich versionieren, kopieren und auf anderen Rechnern
öffnen.

## Vorlagen

| Vorlage | Stil | Besonderheit |
|---|---|---|
| **Modern** | Einspaltig, blaue Akzente | ATS-freundlich, viel Weißraum |
| **Classic** | Traditionell deutsch, Serifenschrift | Zentrierter Kopf, klare Datumsangaben |
| **Minimal** | Schwarz/weiß | Maximale Lesbarkeit, ATS-freundlich |
| **Professional** | Business-Stil | Dunkle Überschriftenbalken, zweispaltiger Kontaktblock |
| **Creative** | Mehr Design | Akzentfarbe, farbiger Kopfbereich |
| **ZH Modern/Classic/Creative/Tech/Executive** | Nachbau z-hussein.com | Zentrierter Header, Skills-Grid |
| **Swiss** | Schweizer Raster | Streng, Helvetica, roter Akzent |
| **Nordic** | Skandinavisch hell | Luftig, blassblau |
| **Terminal** | Terminal-Fenster (Stil 3) | Dunkel, JetBrains Mono, Shell-Kommandos, Level-Balken. **Nicht ATS-geeignet.** |

### Terminal-Stil

Der Stil `Terminal` ist ein Nachbau des Mockups `Terminal style/` (FiSi-CV, 794×1123):

- Dunkles Fenster (`#0C0B09`) mit Rahmen, Titelleiste (3 Punkte + `name@terminal: ~/lebenslauf`)
- Schrift **JetBrains Mono** (wird in `assets/fonts/` mitgeliefert; als Ersatz dient Consolas/Courier)
- Abschnitte als Kommandos: `$ whoami`, `$ cat profil.md`, `$ git log --graph erfahrung`, `$ cat skills.yaml`, `$ ls -l …`, `$ echo $KONTAKT`, Cursor `$ █` am Ende
- **Level-Balken:** Trage bei einer Kenntnis im Feld *Level* eine Prozentzahl ein (z. B. `80 %`), dann erscheint automatisch ein `./level --top`-Block mit Block-Balken (`████████░░`)
- **Akzentfarbe:** Über *Design-Einstellungen → Akzentfarbe* umschaltbar wie im Mockup (`#FFB454` orange, `#5CFF8A` grün, `#7DD3FC` blau, `#FF7AA2` pink)
- Beispielprojekt: `examples/example_terminal.json` (FiSi-A zubi-Daten, 1 Seite)
- Hinweis: Durch den dunklen Hintergrund ist dieser Stil **nicht ATS-geeignet** – für Online-Bewerbungsportale eine helle Vorlage (Modern/Minimal) wählen.

## Fehlerbehebung

**App startet nicht / `ModuleNotFoundError`**
Virtuelle Umgebung aktiviert? `pip install -r requirements.txt` ausgeführt?

**Umlaute falsch dargestellt**
Sollte nicht auftreten – bitte Projekt neu laden und erneut exportieren.

**PDF kann nicht gespeichert werden**
Ist die Zieldatei evtl. in einem PDF-Reader geöffnet? Datei schließen und
erneut exportieren.

**Foto erscheint nicht im PDF**
Pfad prüfen (Datei darf nach dem Auswählen nicht verschoben/gelöscht werden).
Unterstützte Formate: JPG, JPEG, PNG.

**Vorschau bleibt leer**
Bei sehr großen Projekten einen Moment warten; die Vorschau baut sich
automatisch auf. Bei anhaltenden Problemen das Projekt speichern, App neu
starten und Projekt erneut öffnen.

## Autor & Lizenz

Entwickelt von **[Z-Hussein](https://github.com/z-hussein)** —
Repo: [github.com/z-hussein/lebenslauf-studio](https://github.com/z-hussein/lebenslauf-studio)

Lizenz: [MIT](LICENSE) · Technik: Python · PySide6 · ReportLab · Pillow · pypdfium2 · fonttools

Fehler gefunden oder Idee? Bitte ein [Issue auf GitHub](https://github.com/z-hussein/lebenslauf-studio/issues) öffnen.
