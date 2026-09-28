"""The PDF builder behind the "Advanced PDF Creator" page.

It used to live inside app.py, which meant it could only be tried by clicking through
Streamlit. On its own it can be tested (tests/test_pdf_generator.py) and reused.
"""
import os
import re

from fpdf import FPDF

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def hex_to_rgb(hex_color):
    """'#1a2b3c' -> (26, 43, 60)"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def safe_filename(name, default="document"):
    """A document name turned into a file name: 'My Report!' -> 'My-Report.pdf'."""
    stem = re.sub(r"[^\w\-]+", "-", name.strip(), flags=re.UNICODE).strip("-")
    return f"{stem or default}.pdf"


class PDFGenerator(FPDF):
    """An A4 page with the bundled DejaVu fonts, which cover Turkish and most other languages."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.load_fonts()

    def load_fonts(self):
        """Registers DejaVu regular, bold and italic from fonts/."""
        self.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", os.path.join(FONT_DIR, "dejavu-sans-bold.ttf"))
        self.add_font("DejaVu", "I", os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf"))
        self.set_font("DejaVu", "", 12)

    def add_title(self, title, font_name="DejaVu", text_color=(0, 0, 0)):
        self.set_font(font_name, style="B", size=20)
        self.set_text_color(*text_color)
        self.multi_cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def add_text(self, text, font_name="DejaVu", font_size=12, font_style="", text_color=(0, 0, 0)):
        self.set_font(font_name, style=font_style, size=font_size)
        self.set_text_color(*text_color)
        # Line height follows the font size: a fixed 10 mm double-spaced small text.
        self.multi_cell(0, font_size * 0.5, text, new_x="LMARGIN", new_y="NEXT")

    def add_multiple_texts(self, text_list, font_name="DejaVu", font_size=12, font_style="", text_color=(0, 0, 0)):
        for text in text_list:
            if text.strip():
                self.add_text(text, font_name, font_size, font_style, text_color)
                self.ln(2)

    def add_image(self, image, x=10, y=None, w=100):
        """`image` can be a path or a PIL image, so uploads never touch the disk."""
        self.image(image, x=x, y=y, w=w)
        self.ln(4)

    def add_table(self, data, col_widths, border=True, text_color=(0, 0, 0)):
        """Adds the rows that have anything in them. Returns False when every cell is empty."""
        rows = [row for row in data if any(str(cell).strip() for cell in row)]
        if not rows:
            return False
        self.set_font("DejaVu", "", 11)
        self.set_text_color(*text_color)
        for row in rows:
            for i, item in enumerate(row):
                self.cell(col_widths[i], 10, str(item), border=1 if border else 0)
            self.ln()
        return True

    def to_bytes(self):
        return bytes(self.output())

    def save_pdf(self, filename):
        self.output(filename)
