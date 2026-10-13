# Anschreiben nach DIN 5008

Die App führt dich durch alle Pflicht- und Kür-Bestandteile eines
deutschen Bewerbungsanschreibens. Öffne links den Eintrag **Anschreiben**,
aktiviere *„Anschreiben in PDF einschließen“* und fülle die Felder aus.
Die Vorschau zeigt das Anschreiben als **Seite 1**.

## Die Regeln im Überblick (was die App automatisch richtig macht)

| Element | Regel (DIN 5008) | In der App |
|---|---|---|
| Absender | Kleine einzeilige Anschrift oben (für Fensterumschlag) | Wird automatisch aus deinen Daten gebildet |
| Empfänger | Links: Firma, Kontakt, Straße, PLZ Ort | 4 Felder, Kontakt darf 2 Zeilen haben |
| Ort/Datum | Rechtsbündig, z. B. *Berlin, 25. August 2026* | Aus *Ort* + *Datum*; oder *Ort, Datum (manuell)* überschreibt |
| Betreff | Fett, sagt Stelle + Quelle (+ Kennziffer) | Freies Feld, z. B. *Bewerbung als … (m/w/d) – Kennziffer … – Ihre Anzeige vom … auf …* |
| Anrede | Mit Komma, dann Leerzeile | Auswahl oder frei, z. B. *Sehr geehrte Frau Schneider,* |
| Text | 3–4 Absätze: Einstieg, Qualifikation, Motivation/Schluss | Mehrzeiliges Feld (Leerzeile = neuer Absatz) |
| Grußformel | Z. B. *Mit freundlichen Grüßen* + Unterschriftsabstand + Name | Name kommt automatisch aus deinen Daten |
| Anlagen | Unter der Unterschrift | Freies Feld, z. B. *Lebenslauf, Zeugnisse, Zertifikate* |

## Datum richtig eingeben

- `2026-08-25` → wird zu **25. August 2026** (mit Ort davor: *Berlin, 25. August 2026*)
- Bereits deutsches Format (`25. August 2026`) bleibt wie getippt
- **Leer lassen** → automatisch *Ort, heutiges Datum* beim Export
- Komplett manuell? Feld *Ort, Datum (manuell)* nutzen

## Guter Inhalt (Kurzratgeber)

1. **Einstieg (2–3 Sätze):** Auf welche Stelle beziehst du dich, warum
   genau dieses Unternehmen? Keine Floskeln („hiermit bewerbe ich mich“
   nur mit Bezug erweitern).
2. **Hauptteil:** 2–3 Erfolge mit **Zahlen** (%, €, Teamgröße, Zeiträume),
   die zur Anzeige passen. Lieber belegen als behaupten.
3. **Schluss:** Eintrittstermin + ggf. Gehaltsvorstellung nennen,
   Gesprächswunsch formulieren, Kontaktdaten aktuell halten.
4. **Länge:** Eine Seite. Passt es nicht? Text kürzen statt Schrift
   verkleinern (kleinste sinnvolle Größe in der App: 7 pt).

> Beispiel zum Abgucken: `examples/example_resume.json` enthält ein
> komplettes Muster-Anschreiben (Firma, Kennziffer, 4 Absätze, Anlagen).

## Export

- *Datei → Bewerbung exportieren*: Anschreiben + Lebenslauf + Scans in
  **einem** PDF
- *Datei → Nur Anschreiben exportieren*: nur das Anschreiben
- Deaktiviert? Dann erscheint es weder in Vorschau noch Export.

Weiter: [PDF-Export](export.md) · [FAQ](faq.md)
