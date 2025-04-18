from fpdf import FPDF
import tempfile

def create_pdf(text: str) -> bytes:
    text = clean_text(text)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in text.splitlines():
        pdf.multi_cell(0, 10, line)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        return tmp.read()

def clean_text(text: str) -> str:
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "•": "*", "✓": "✔", "\u00a0": " "
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text