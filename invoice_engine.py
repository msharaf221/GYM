"""
Maestro ERP - Invoice Engine
Generates professional PDF receipts using reportlab.
"""

import os
import subprocess
import sys
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False


INVOICES_DIR = "invoices"


def ensure_invoices_dir():
    if not os.path.exists(INVOICES_DIR):
        os.makedirs(INVOICES_DIR)


def reshape_arabic(text):
    """Reshape Arabic text for proper PDF rendering."""
    if not text:
        return ""
    if HAS_ARABIC:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    return str(text)


def generate_invoice(student_name, group_name, amount_paid, remaining_debt,
                     invoice_number=None, logo_path=None):
    """
    Generate a PDF invoice/receipt.
    Returns the file path of the generated PDF.
    """
    if not HAS_REPORTLAB:
        return None

    ensure_invoices_dir()

    now = datetime.now()
    if invoice_number is None:
        invoice_number = now.strftime("%Y%m%d%H%M%S")

    filename = os.path.join(INVOICES_DIR, f"invoice_{invoice_number}.pdf")

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Header background
    c.setFillColorRGB(0.12, 0.12, 0.18)
    c.rect(0, height - 120, width, 120, fill=True, stroke=False)

    # Title
    c.setFillColorRGB(0.0, 0.75, 0.85)
    c.setFont("Helvetica-Bold", 28)
    title = reshape_arabic("Maestro ERP")
    c.drawCentredString(width / 2, height - 50, title)

    c.setFillColorRGB(0.8, 0.8, 0.8)
    c.setFont("Helvetica", 14)
    subtitle = reshape_arabic("ايصال دفع")
    c.drawCentredString(width / 2, height - 80, subtitle)

    c.setFont("Helvetica", 10)
    inv_text = reshape_arabic(f"رقم الايصال: {invoice_number}")
    c.drawCentredString(width / 2, height - 100, inv_text)

    # Body
    y = height - 160
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)

    fields = [
        ("اسم الطالب", student_name),
        ("المجموعة", group_name),
        ("المبلغ المدفوع", f"{amount_paid:.2f} جنيه"),
        ("المبلغ المتبقي", f"{remaining_debt:.2f} جنيه"),
        ("التاريخ", now.strftime("%Y-%m-%d")),
        ("الوقت", now.strftime("%H:%M:%S")),
    ]

    for label, value in fields:
        c.setFont("Helvetica-Bold", 12)
        label_text = reshape_arabic(label)
        value_text = reshape_arabic(str(value))

        # Draw label on right, value on left (RTL style)
        c.drawRightString(width - 60, y, label_text)
        c.setFont("Helvetica", 12)
        c.drawRightString(width - 200, y, value_text)

        # Separator line
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(60, y - 8, width - 60, y - 8)
        y -= 35

    # Footer
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.setFont("Helvetica", 9)
    footer = reshape_arabic("تم الانشاء بواسطة Maestro ERP - نظام ادارة المراكز التعليمية")
    c.drawCentredString(width / 2, 40, footer)

    c.save()
    return filename


def open_pdf(filepath):
    """Open PDF file with the default system viewer."""
    if not filepath or not os.path.exists(filepath):
        return
    try:
        if sys.platform == "win32":
            os.startfile(filepath)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception:
        pass
