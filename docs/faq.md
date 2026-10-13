# FAQ & Fehlerbehebung

## App startet nicht

- `ModuleNotFoundError: …` → virtuelle Umgebung **aktiviert**?
  (`installation.md`, Schritt 3) und `pip install -r requirements.txt`
  ausgeführt?
- Fenster erscheint nicht → anderes Fenster verdeckt es ggf.; in der
  Taskleiste nach *Lebenslauf Studio* suchen.

## Vorschau lädt / bleibt leer

- Normal: Aufbau ca. 0,5 s nach der letzten Eingabe (+ Renderzeit).
- Dauerhaft leer + Fehlermeldung → Eingaben prüfen (z. B. defektes
  Fotofile), Projekt speichern, App neu starten.
- Zoomen: rechts unten `−` / `%` / `+` / *Einpassen*; bei mehreren Seiten
  mit *Zurück/Weiter* blättern.

## PDF-Probleme

- **Datei gesperrt:** PDF im Reader schließen, erneut exportieren.
- **Foto/Scan fehlt im PDF:** Pfad prüfen (siehe [Projekte](projects.md));
  Formate: JPG, JPEG, PNG (Foto) + PDF (Scans).
- **Kästchen □ im PDF:** sollte nicht mehr vorkommen (Fallback-Schrift).
  Falls doch: Zeichen nennen → [Issue auf GitHub](https://github.com/z-hussein/lebenslauf-studio/issues).
- **Umbruch ungünstig:** Abschnittsabstand in den Design-Einstellungen
  verkleinern oder Text kürzen; Schriftgröße 7–14 pt möglich.

## Daten & Sicherheit

- **Wo sind meine Daten?** Nur lokal: Projekt-`.json`, exportierte PDFs,
  Einstellungen (Windows-Registry `LebenslaufStudio`). Kein Konto, keine
  Cloud, kein Netzwerkzugriff der App.
- **Aus Versehen überschrieben?** Neben jeder `.json` liegt eine
  `.bak`-Sicherung der vorherigen Version (Endung entfernen → öffnen).
- **Alte Projektdatei lädt nicht?** Fehlermeldung lesen: beschädigtes
  JSON vs. zu neue Version (dann App aktualisieren).

## Bedienung

- **Abschnitt weg?** Versehentlich gelöscht → es gibt kein Undo: Projekt
  **ohne Speichern** schließen (Änderungen verwerfen) oder `.bak` nutzen.
  Tipp: vor Umbauten *Speichern unter* mit neuem Namen.
- **Reihenfolge stimmt nicht mit PDF überein?** Sidebar-Reihenfolge =
  PDF-Reihenfolge (Anschreiben immer Seite 1, Persönliches immer Kopf).
- **Entf-Taste:** löscht Eintrag/Abschnitt (mit Rückfrage), wenn die Liste
  fokussiert ist.
- **App dunkel/hell:** Menü *Ansicht → System/Hell/Dunkel* (unabhängig
  vom PDF-Design).

## Sonstiges

- Eigene Schrift einbinden: `.ttf` nach `assets/fonts/` kopieren, App neu
  starten → in *Design-Einstellungen → Schriftart* wählbar.
- Eigenes Icon-Set oder neue Vorlage gewünscht? Siehe `app/templates/`
  (eine Datei pro Stil) → gern als Pull Request oder Issue vorschlagen.

Zurück: [Übersicht](index.md)
