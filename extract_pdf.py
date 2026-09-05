import subprocess
from pypdf import PdfReader

input_pdf = "input.pdf"
ocr_pdf = "output_ocr.pdf"

# Step 1: Run OCR on the image-based PDF
subprocess.run([
    "ocrmypdf",
    input_pdf,
    ocr_pdf
], check=True)

# Step 2: Extract the OCR text using pypdf
reader = PdfReader(ocr_pdf)

text = ""

for i, page in enumerate(reader.pages):
    page_text = page.extract_text() or ""
    text += f"\n--- Page {i + 1} ---\n"
    text += page_text

print(text)