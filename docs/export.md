# PDF-Export

Menü *Datei*, drei Modi:

| Modus | Inhalt | Dateiname-Vorschlag |
|---|---|---|
| **Bewerbung exportieren** (`Strg+E`) | Anschreiben (falls aktiviert) + Lebenslauf + Zertifikats-Scans als Anhang | `…_Bewerbung.pdf` |
| **Nur Lebenslauf exportieren** | Nur der Lebenslauf | `…_Lebenslauf.pdf` |
| **Nur Anschreiben exportieren** | Nur das Anschreiben | `…_Anschreiben.pdf` |

Dein Projekt wird dabei **nicht** verändert (der Export arbeitet intern
auf einer Kopie).

## Qualität

- Format **A4**, automatische Seitenumbrüche, keine abgeschnittenen Texte
- Umlaute + Sonderzeichen (`– • → ✓ ★` …) korrekt; fehlende Glyphen
  werden ersatzweise dargestellt, sonst **nie** als □
- Text bleibt markier-/kopierbar (wichtig für ATS, siehe [Vorlagen](templates.md))
- Schriften werden eingebettet (wenn als Datei vorhanden)

## Zertifikats-Anhang

Bei einem Zertifikat **Scan anhängen** (JPG/PNG/PDF) wählen. Beim
*Bewerbungs-Export* hängt die App jeden Scan als eigene A4-Seite hinten
an. In der Liste steht dann `[PDF]` dahinter. Abschalten über
*Design-Einstellungen → Zertifikats-Scans als Anhang*.

## Warnungen verstehen

Nach dem Export kann ein Hinweis-Dialog erscheinen (**kein Fehler**,
das PDF ist trotzdem erstellt):

| Hinweis | Bedeutung & Lösung |
|---|---|
| *Bewerbungsfoto nicht gefunden* | Datei wurde verschoben/gelöscht → erneut auswählen (siehe [Projekte](projects.md)) |
| *Zertifikat-Datei nicht gefunden / nicht lesbar* | Gleiches Vorgehen wie beim Foto |
| *Zeichen … wurden entfernt* | Extrem seltene Sonderzeichen ohne Schrift-Glyphe → Zeichen ersetzen/we-glassen |

Der Dialog listet alles unter *Details* auf; die Statusleiste zeigt die
Anzahl.

## Typische Probleme

- **„Datei kann nicht geschrieben werden“** → PDF ist in einem Reader
  geöffnet → Reader schließen, erneut exportieren.
- **Export sieht anders aus als Vorschau** → Vorschau zeigt exakt den
  gleichen Stand; ggf. kurz warten (Vorschau baut verzögert auf).
- **Leere Abschnitte fehlen im PDF** → Absicht: leere Abschnitte werden
  ausgeblendet (Sidebar: graue Einträge).

Weiter: [Projekte](projects.md) · [FAQ](faq.md)
