# Vorlagen

13 Stile, oben in der Sidebar wählbar. Die Abschnittsreihenfolge aus der
Sidebar gilt für **alle** Vorlagen.

## ATS – was bedeutet das?

**ATS** (Applicant Tracking System) liest PDFs maschinell aus. Dafür muss
der Text als einfacher, einspaltiger Fließtext extrahierbar sein – ohne
Text in Bildern, Icons oder Grafiken. Faustregel:

- **Online-Portal / E-Mail an HR-Software → ATS-Vorlage** (Modern, Minimal,
  Classic, Professional, ZH Tech …)
- **Persönlich / als PDF-Anhang an Menschen → freie Wahl** (Creative,
  Terminal …)

## Die Stile

| Vorlage | Charakter | ATS? |
|---|---|---|
| Modern | Blau, viel Weißraum, Linie unter Titel | ✅ |
| Classic | Konservativ deutsch, Serifenschrift, zentriert | ✅ |
| Minimal | Schwarz/weiß, maximale Lesbarkeit | ✅ |
| Professional | Dunkle Titelbalken, Kontakt zweispaltig | ✅ |
| Creative | Farbiger Kopfbereich, mehr Design | ⚠️ eher nein |
| ZH Modern / Tech | Zentriert, pink/blau, Skills-Grid (Nachbau z-hussein.com) | ✅ |
| ZH Classic / Executive | Seriös, Times, dunkelblau / schwarz-gold | ✅ |
| ZH Creative | Rot/violett/orange, ausdrucksstark | ⚠️ eher nein |
| Swiss | Strenges Raster, roter Akzent | ✅ |
| Nordic | Hell, luftig, blassblau | ✅ |
| Terminal | Dunkles Fenster, JetBrains Mono, Shell-Kommandos | ❌ nein |

## Farben & Hintergrund

*Design-Einstellungen → Akzentfarbe* färbt Titel, Linien und Balken.
*Hintergrund* färbt die ganze Seite (z. B. Creme `#FAF6EC`, Navy
`#1A1A2E`); **Auto** (Standard) = Weiß, bzw. Dunkel bei Terminal.
Bei dunklem Grund werden Text und notfalls die Akzentfarbe automatisch
aufgehellt – alles bleibt lesbar. Terminal wechselt bei hellem Grund
auf dunklen Text (Fenster-Chrome bleibt dunkel).

## Schriften

10 Schriften eingebaut (Helvetica, Times, DejaVu Sans, Liberation Sans,
Calibri, Segoe UI, Noto Sans, Garamond, **JetBrains Mono**, Consolas).
Für ATS: Helvetica/Calibri (bewährter Standard). Eigene `.ttf` nach
`assets/fonts/` legen → nach Neustart wählbar. Sonderzeichen
(`– • → ✓ ★`, Umlaute) werden notfalls automatisch in einer
Ersatzschrift dargestellt – **keine □-Kästchen**.

## Terminal-Spezialitäten

- Level-Feld mit `%` (z. B. `80 %`) → `./level --top`-Balken
  (`████████░░`, halb `▌` bei z. B. 75 %)
- Akzent wie im Mockup umschaltbar: `#FFB454` orange, `#5CFF8A` grün,
  `#7DD3FC` blau, `#FF7AA2` pink
- Kontakt kommt automatisch als `$ echo $KONTAKT`-Block ans Ende
- Beispiel: `examples/example_terminal.json`

Weiter: [PDF-Export](export.md) · [Erste Schritte](getting-started.md)
