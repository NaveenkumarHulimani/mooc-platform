from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas


def build_certificate_pdf(name: str, course_title: str, score: int, cert_id: str, issued_at) -> BytesIO:
    buffer = BytesIO()
    page_size = landscape(letter)
    width, height = page_size
    c = canvas.Canvas(buffer, pagesize=page_size)

    ink = HexColor("#1a1200")
    amber = HexColor("#c98a2c")  # print-safe darker amber (screen amber #ffb454 is too light on white)

    c.setFillColor(HexColor("#fffaf0"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    c.setStrokeColor(amber)
    c.setLineWidth(6)
    c.rect(24, 24, width - 48, height - 48)
    c.setLineWidth(1.5)
    c.rect(34, 34, width - 68, height - 68)

    c.setFont("Helvetica-Bold", 34)
    c.setFillColor(ink)
    c.drawCentredString(width / 2, height - 110, "CERTIFICATE OF COMPLETION")

    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(width / 2, height - 160, "This certifies that")

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(amber)
    c.drawCentredString(width / 2, height - 205, name)

    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(
        width / 2,
        height - 245,
        f"has successfully completed all practice levels and passed the final exam for",
    )
    c.setFont("Helvetica-Bold", 17)
    c.setFillColor(ink)
    c.drawCentredString(width / 2, height - 268, course_title)

    c.setFont("Helvetica", 15)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(width / 2, height - 296, f"Exam Score: {score}%")

    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(width / 2, 70, f"Certificate ID: {cert_id}")
    c.drawCentredString(width / 2, 52, f"Issued on: {issued_at.strftime('%d %B %Y')}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
