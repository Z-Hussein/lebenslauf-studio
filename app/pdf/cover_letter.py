"""
Anschreiben (Bewerbungsschreiben) nach DIN 5008.

Erzeugt Flowables für das Anschreiben und kümmert sich um
Briefkopf, Empfänger, Datum, Betreff, Anrede, Hauptteil, Grußformel
und Anlagen. Alle Regeln für ein deutsches Bewerbungsanschreiben
werden berücksichtigt.
"""

import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from ..utils.helpers import escape_xml, nl2br, safe_str

# Deutsche Monatsnamen
MONTHS_DE = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def format_date_de(raw: str, fallback_city: str = "") -> str:
    """Formatiert ISO-Datum nach '25. August 2026' oder gibt raw zurück."""
    s = safe_str(raw)
    if not s:
        # Heute als Fallback
        today = datetime.date.today()
        return f"{fallback_city + ', ' if fallback_city else ''}{today.day}. {MONTHS_DE[today.month]} {today.year}"
    # Versuche ISO zu parsen
    try:
        # akzeptiert YYYY-MM-DD, DD.MM.YYYY
        if "-" in s and len(s) >= 10:
            y, m, d = s[:10].split("-")
            return f"{int(d)}. {MONTHS_DE[int(m)]} {int(y)}"
        if "." in s:
            # bereits deutsches Format, zurückgeben
            return s
    except Exception:
        pass
    return s


def build_city_date(resume: Dict[str, Any] | Any) -> str:
    """Baut 'Ort, Datum' nach DIN 5008."""
    # resume kann Resume-Objekt oder dict sein
    if hasattr(resume, "cover_letter"):
        cl = resume.cover_letter
        p = resume.personal
    else:
        cl = resume.get("cover_letter", {})
        p = resume.get("personal", {})
    city_date = safe_str(cl.get("city_date", ""))
    if city_date:
        return city_date
    city = safe_str(cl.get("city") or p.get("city") or "")
    raw_date = safe_str(cl.get("date", ""))
    formatted = format_date_de(raw_date, "")
    if city and formatted and "," not in formatted:
        return f"{city}, {formatted}"
    if city and not raw_date:
        # heute mit Ort
        today = datetime.date.today()
        return f"{city}, {today.day}. {MONTHS_DE[today.month]} {today.year}"
    return formatted or city


def cover_letter_flowables(resume, builder) -> List[Any]:
    """
    Erzeugt die Flowables für das Anschreiben.
    Nutzt `builder` für Farben, Schriften und Breite.
    """
    cl = resume.cover_letter if hasattr(resume, "cover_letter") else resume.get("cover_letter", {})
    p = resume.personal if hasattr(resume, "personal") else resume.get("personal", {})
    if not cl.get("enabled"):
        return []

    story: List[Any] = []

    # Farben/Schriften vom Builder wiederverwenden
    primary = builder.primary
    secondary = builder.secondary
    f_reg = builder.f_reg
    f_bold = builder.f_bold
    content_width = builder.content_width

    # Lokale Styles für Brief
    sender_style = ParagraphStyle(
        "SenderLine", parent=builder.styles.get("small", ParagraphStyle("tmp")),
        fontName=f_reg, fontSize=7, leading=9, textColor=secondary, alignment=TA_LEFT, spaceAfter=2 * mm,
    )
    recipient_style = ParagraphStyle(
        "Recipient", parent=builder.styles["body"],
        fontName=f_reg, fontSize=10, leading=13, textColor=builder.text_col, spaceAfter=0,
    )
    date_style = ParagraphStyle(
        "Date", parent=builder.styles["small"],
        fontName=f_reg, fontSize=9, leading=11, textColor=secondary, alignment=TA_RIGHT,
    )
    subject_style = ParagraphStyle(
        "Subject", parent=builder.styles["body"],
        fontName=f_bold, fontSize=10.5, leading=13, textColor=builder.text_col,
        spaceBefore=6 * mm, spaceAfter=4 * mm,
    )
    salutation_style = ParagraphStyle(
        "Salutation", parent=builder.styles["body"],
        fontName=f_reg, fontSize=10, leading=14, spaceAfter=4 * mm,
    )
    body_style = ParagraphStyle(
        "BodyLetter", parent=builder.styles["body"],
        fontName=f_reg, fontSize=10, leading=14, alignment=TA_LEFT, spaceAfter=3 * mm,
    )
    closing_style = ParagraphStyle(
        "Closing", parent=body_style, spaceBefore=6 * mm, spaceAfter=0,
    )
    enclosure_style = ParagraphStyle(
        "Enclosure", parent=builder.styles["small"],
        fontName=f_reg, fontSize=8, leading=10, textColor=secondary, spaceBefore=8 * mm,
    )

    # ---- Absenderzeile (klein, über Falz) ----
    sender_extra = safe_str(cl.get("sender_extra", ""))
    if not sender_extra:
        # Automatisch aus persönlichen Daten
        parts = [safe_str(p.get("first_name") or p.get("name") or "").strip(),
                 safe_str(p.get("address") or ""), safe_str(p.get("postal_code") or ""), safe_str(p.get("city") or "")]
        # Voller Name statt first_name fallback
        full = ""
        if hasattr(resume, "full_name"):
            full = resume.full_name()
        else:
            full = safe_str(p.get("fullName") or "")
        name_part = full or safe_str(p.get("first_name") or "")
        addr = " · ".join([x for x in [name_part, safe_str(p.get("address")), safe_str(p.get("postal_code")) + " " + safe_str(p.get("city")).strip()] if x.strip()])
        sender_extra = addr.strip(" ·")
    if sender_extra:
        story.append(Paragraph(escape_xml(sender_extra), sender_style))
        # dünne Linie darunter (DIN Falz-Hilfe)
        line = Table([[""]], colWidths=[content_width], rowHeights=[0.25])
        line.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#BBBBBB"))]))
        story.append(line)
        story.append(Spacer(1, 6 * mm))

    # ---- Empfänger ----
    rec_lines = []
    for key in ("recipient_company", "recipient_contact", "recipient_street", "recipient_postal_city"):
        v = safe_str(cl.get(key, ""))
        if v:
            # erlaubt Zeilenumbruch mit \n im Feld
            rec_lines.append(escape_xml(v).replace("\n", "<br/>"))
    if rec_lines:
        for line in rec_lines:
            story.append(Paragraph(line, recipient_style))
        story.append(Spacer(1, 8 * mm))

    # ---- Ort, Datum rechts ----
    city_date_text = build_city_date(resume)
    if city_date_text:
        story.append(Paragraph(escape_xml(city_date_text), date_style))
        story.append(Spacer(1, 8 * mm))

    # ---- Betreff ----
    subject = safe_str(cl.get("subject", ""))
    if subject:
        story.append(Paragraph(f"<b>{escape_xml(subject)}</b>", subject_style))

    # ---- Anrede ----
    salutation = safe_str(cl.get("salutation", ""))
    if salutation:
        story.append(Paragraph(escape_xml(salutation), salutation_style))

    # ---- Hauptteil (Absätze) ----
    body = safe_str(cl.get("body", ""))
    # Körper in Absätze nach Leerzeile splitten, sonst einfache Zeilenumbrüche
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paragraphs and body.strip():
        paragraphs = [body.strip()]
    for para in paragraphs:
        # Erhalte einfache Umbrüche innerhalb Absatzes
        html = nl2br(para)
        story.append(Paragraph(html, body_style))

    # ---- Grußformel + Unterschrift ----
    closing = safe_str(cl.get("closing", "Mit freundlichen Grüßen"))
    if closing:
        story.append(Paragraph(escape_xml(closing), closing_style))
        story.append(Spacer(1, 8 * mm))
        # Signatur-Name
        sig_name = ""
        if hasattr(resume, "full_name"):
            sig_name = resume.full_name()
        else:
            sig_name = safe_str(p.get("fullName") or "")
        if sig_name:
            story.append(Paragraph(escape_xml(sig_name), body_style))

    # ---- Anlagen ----
    enclosures = safe_str(cl.get("enclosures", ""))
    if enclosures:
        story.append(Paragraph(f"Anlagen: {escape_xml(enclosures)}", enclosure_style))

    return story
