"""Generate a donor acknowledgement PDF without treating it as a fiscal receipt."""

from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from ..models import AuditLog, Campaign, Donation, Organization


def _money(value) -> str:
    return f"${value:,.2f} MXN"


def _wrapped_lines(text: str, font: str, size: int, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and stringWidth(candidate, font, size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def build_donation_acknowledgement(
    donation: Donation,
    campaign: Campaign,
    organization: Organization,
    audit: AuditLog | None,
) -> bytes:
    """Return a deterministic PDF acknowledgement for a recorded donation."""

    output = BytesIO()
    anchor_labels = {
        "NOT_CONFIGURED": "No configurado",
        "PENDING": "Pendiente",
        "CONFIRMED": "Confirmado en Sepolia",
        "FAILED": "Fallido",
    }
    pdf = canvas.Canvas(output, pagesize=A4, invariant=1)
    width, height = A4
    green = HexColor("#0b5d4b")
    orange = HexColor("#e9a23b")
    gray = HexColor("#55645f")

    pdf.setTitle(f"Acuse de donación {donation.id}")
    pdf.setAuthor("DonationChain")
    pdf.setFillColor(green)
    pdf.rect(0, height - 125, width, 125, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(48, height - 65, "DonationChain")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(48, height - 88, "Transparencia y trazabilidad de donaciones")

    y = height - 165
    pdf.setFillColor(orange)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "ACUSE DE REGISTRO DE DONACIÓN")
    y -= 22
    pdf.setFillColor(gray)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        48,
        y,
        "Documento de demostración. No es recibo fiscal ni confirma un pago bancario.",
    )

    fields = [
        ("Folio", donation.id),
        ("Campaña", campaign.name),
        ("Organización", organization.legal_name),
        ("Donante", donation.donor_name),
        ("Cantidad registrada", _money(donation.amount)),
        ("Fecha de registro", donation.created_at.strftime("%d/%m/%Y %H:%M UTC")),
        ("Estado", "Registrada en DonationChain"),
    ]
    y -= 42
    for label, value in fields:
        pdf.setFillColor(gray)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(48, y, label.upper())
        pdf.setFillColorRGB(0.08, 0.12, 0.11)
        pdf.setFont("Helvetica", 11)
        lines = _wrapped_lines(str(value), "Helvetica", 11, width - 210)
        for index, line in enumerate(lines):
            pdf.drawString(175, y - (index * 14), line)
        y -= max(31, 14 * len(lines) + 12)

    pdf.setStrokeColor(HexColor("#dfe7e3"))
    pdf.line(48, y + 8, width - 48, y + 8)
    y -= 18
    pdf.setFillColor(green)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Evidencia criptográfica")
    y -= 25

    evidence = [
        ("Hash de auditoría", audit.entry_hash if audit else "No disponible"),
        (
            "Estado Blockchain",
            anchor_labels.get(audit.anchor_status.value, audit.anchor_status.value)
            if audit
            else "No disponible",
        ),
        (
            "Transacción",
            audit.blockchain_tx_hash if audit and audit.blockchain_tx_hash else "Pendiente",
        ),
    ]
    for label, value in evidence:
        pdf.setFillColor(gray)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(48, y, label.upper())
        pdf.setFillColorRGB(0.08, 0.12, 0.11)
        pdf.setFont("Courier", 7.5)
        for line in _wrapped_lines(str(value), "Courier", 7.5, width - 210):
            pdf.drawString(175, y, line)
            y -= 11
        y -= 13

    pdf.setFillColor(HexColor("#f2f6f4"))
    pdf.roundRect(48, 62, width - 96, 64, 8, fill=1, stroke=0)
    pdf.setFillColor(gray)
    pdf.setFont("Helvetica", 8.5)
    note = (
        "Este acuse demuestra que DonationChain registró la información indicada. "
        "La evidencia queda protegida por la cadena de auditoría y, cuando aparece una "
        "transacción, también por el Smart Contract desplegado en Ethereum Sepolia."
    )
    note_y = 108
    for line in _wrapped_lines(note, "Helvetica", 8.5, width - 125):
        pdf.drawString(62, note_y, line)
        note_y -= 12

    pdf.showPage()
    pdf.save()
    return output.getvalue()
