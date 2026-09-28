import fitz  # pymupdf

from pdf_generator import PDFGenerator, hex_to_rgb, safe_filename


def spans(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return [s for page in doc for b in page.get_text("dict")["blocks"]
            for line in b.get("lines", []) for s in line["spans"]]


def test_hex_to_rgb():
    assert hex_to_rgb("#000000") == (0, 0, 0)
    assert hex_to_rgb("87CEEB") == (135, 206, 235)


def test_safe_filename():
    assert safe_filename("My Report!") == "My-Report.pdf"
    assert safe_filename("Ödev Raporu") == "Ödev-Raporu.pdf"
    assert safe_filename("   ") == "document.pdf"


def test_text_is_black_by_default():
    pdf = PDFGenerator()
    pdf.add_text("Hello from line 1")
    found = [s for s in spans(pdf.to_bytes()) if s["text"] == "Hello from line 1"]
    assert found and found[0]["color"] == 0x000000


def test_title_and_turkish_text_survive():
    pdf = PDFGenerator()
    pdf.add_title("Rapor")
    pdf.add_text("Çalışma günü ağır geçti")
    texts = [s["text"] for s in spans(pdf.to_bytes())]
    assert "Rapor" in texts and "Çalışma günü ağır geçti" in texts


def test_empty_table_is_left_out():
    pdf = PDFGenerator()
    assert pdf.add_table([["", "", ""], ["", " ", ""]], [40, 40, 40]) is False
    assert pdf.add_table([["a", "", ""], ["", "", ""]], [40, 40, 40]) is True


def test_table_border_choice_is_honoured():
    def rect_count(border):
        pdf = PDFGenerator()
        pdf.add_table([["a", "b", "c"]], [40, 40, 40], border=border)
        doc = fitz.open(stream=pdf.to_bytes(), filetype="pdf")
        return len(doc[0].get_drawings())
    assert rect_count(True) > 0
    assert rect_count(False) == 0


def test_blank_extra_lines_are_skipped():
    pdf = PDFGenerator()
    pdf.add_multiple_texts(["one", "", "  ", "two"])
    assert [s["text"] for s in spans(pdf.to_bytes())] == ["one", "two"]
