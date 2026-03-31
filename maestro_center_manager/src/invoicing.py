from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm as unit_mm
import os

class InvoiceGenerator:
    def __init__(self, paper_width_mm=80):
        self.paper_width = paper_width_mm * unit_mm
        self.margin = 5 * unit_mm
        self.content_width = self.paper_width - (2 * self.margin)

    def generate_receipt(self, filename, student_name, items, total, paid, previous_debt, date):
        # Items: list of (description, amount)
        # Estimate height: 60mm base + 10mm per item
        estimated_height = (60 + (len(items) * 10)) * unit_mm

        c = canvas.Canvas(filename, pagesize=(self.paper_width, estimated_height))
        y = estimated_height - self.margin

        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.paper_width / 2.0, y, "Maestro Center Manager")
        y -= 20

        c.setFont("Helvetica", 10)
        c.drawCentredString(self.paper_width / 2.0, y, "Thermal Receipt")
        y -= 20

        c.drawString(self.margin, y, f"Date: {date}")
        y -= 15
        c.drawString(self.margin, y, f"Student: {student_name}")
        y -= 20

        c.line(self.margin, y + 5, self.paper_width - self.margin, y + 5)
        c.drawString(self.margin, y, "Description")
        c.drawRightString(self.paper_width - self.margin, y, "Amount")
        y -= 15

        c.setFont("Helvetica", 9)
        for desc, amount in items:
            c.drawString(self.margin, y, desc)
            c.drawRightString(self.paper_width - self.margin, y, f"{amount:.2f}")
            y -= 12

        c.line(self.margin, y + 5, self.paper_width - self.margin, y + 5)
        y -= 15

        c.setFont("Helvetica", 10)
        c.drawString(self.margin, y, "Total Amount:")
        c.drawRightString(self.paper_width - self.margin, y, f"{total:.2f}")
        y -= 12

        c.drawString(self.margin, y, "Paid Amount:")
        c.drawRightString(self.paper_width - self.margin, y, f"{paid:.2f}")
        y -= 12

        c.drawString(self.margin, y, "Previous Debt:")
        c.drawRightString(self.paper_width - self.margin, y, f"{previous_debt:.2f}")
        y -= 12

        current_debt = (total + previous_debt) - paid
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.margin, y, "Current Debt:")
        c.drawRightString(self.paper_width - self.margin, y, f"{current_debt:.2f}")
        y -= 20

        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(self.paper_width / 2.0, y, "Thank you for your trust!")

        c.save()
        return filename

if __name__ == "__main__":
    ig = InvoiceGenerator(80)
    ig.generate_receipt("test_receipt.pdf", "John Doe", [("Oct Fee", 500), ("Math Book", 150)], 650, 600, 100, "2023-10-27")
    print("Test receipt generated.")
