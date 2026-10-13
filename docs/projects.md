# Projekte speichern & verwalten

Ein Projekt (`.json`) enthält **alles**: Daten, Abschnitte + Reihenfolge,
Vorlage, Design, Anschreiben, Foto- und Scan-**Pfade**.

## Speichern / Öffnen

- **Datei → Speichern** (`Strg+S`), **Speichern unter** (`Strg+Umschalt+S`)
- **Datei → Öffnen** (`Strg+O`)
- `*` im Fenstertitel = ungespeicherte Änderungen (beim Schließen wirst du
  gefragt)
- Gespeichert wird **atomar**: erst Temp-Datei, dann Umbenennen – ein
  Absturz hinterlässt keine kaputte Datei. Die vorherige Version bleibt
  als `dateiname.json.bak` daneben liegen.

## Wichtig: Fotos & Scans sind Verweise, kein Inhalt

Foto und Zertifikat-Scans werden **nicht** in die `.json` kopiert, nur
ihre Pfade. Beachte daher:

1. Dateien nach dem Auswählen **nicht verschieben/umbenennen/löschen**,
   sonst fehlen sie im PDF (Export meldet das als Hinweis).
2. Für Weitergabe/Backup: `.json` **plus** Bilddateien zusammen kopieren
   (z. B. alles in einen Bewerbungs-Ordner legen *bevor* du auswählst).
3. Absolute Pfade: Auf einem anderen PC mit anderem Benutzernamen musst
   du Foto/Scans einmal neu auswählen.

## Beispiele

- `examples/example_resume.json` – Max Mustermann (Modern + Anschreiben)
- `examples/example_terminal.json` – FiSi-Beispiel im Terminal-Stil
- Beide nutzen **erfundene** Daten und können gefahrlos überschrieben
  werden (per Git jederzeit wiederherstellbar).

## Mehrere Bewerbungen verwalten

Empfohlen: pro Stelle eine Kopie, z. B. `Bewerbung_FirmaA.json`,
darin nur Anschreiben (Empfänger, Betreff, Text) anpassen – Lebenslauf
bleibt gleich. Export dann als `…_Bewerbung.pdf` daneben speichern.

Weiter: [PDF-Export](export.md) · [FAQ](faq.md)
