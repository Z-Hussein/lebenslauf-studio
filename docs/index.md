# Lebenslauf Studio – Benutzerhandbuch

Willkommen! Diese Anleitungen führen dich durch Installation, Bedienung
und alle Funktionen der App.

## Inhalt

1. [Installation](installation.md) – Python, virtuelle Umgebung und Pakete
   einrichten (Windows, Linux, macOS)
2. [Erste Schritte](getting-started.md) – in 10 Minuten zum ersten
   Lebenslauf: Daten eintragen, Abschnitte verwalten, Vorlage wählen
3. [Anschreiben](cover-letter.md) – Bewerbungsanschreiben nach DIN 5008
   schreiben (alle Regeln erklärt)
4. [Vorlagen](templates.md) – alle 13 Vorlagen im Überblick, ATS-Hinweise,
   Farben und Schriften
5. [PDF-Export](export.md) – Export-Modi, Zertifikats-Anhang, Warnungen
   verstehen
6. [Projekte speichern & verwalten](projects.md) – JSON-Projekte, `.bak`,
   Fotos/Zertifikate und Dateipfade
7. [FAQ & Fehlerbehebung](faq.md) – häufige Fragen und Lösungen

## Kurzfassung für Eilige

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  |  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Beim Start **Beispiel-Lebenslauf laden** wählen, links durch die
Abschnitte klicken, rechts die Live-Vorschau prüfen, dann
*Datei → Bewerbung exportieren*. Details stehen in den Kapiteln oben.

## App-Überblick

| Bereich | Was du dort machst |
|---|---|
| Sidebar (links) | Vorlage wählen, Abschnitte per Drag & Drop sortieren, hinzufügen/duplizieren/löschen, Design öffnen |
| Editor (Mitte) | Ausgewählten Abschnitt ausfüllen (Formulare, Listen, Texte) |
| Vorschau (rechts) | A4-Seiten live sehen, blättern, zoomen |
| Menü *Datei* | Neu / Öffnen / Speichern / PDF exportieren |
| Menü *Ansicht* | App-Farbschema Hell / Dunkel / System |
