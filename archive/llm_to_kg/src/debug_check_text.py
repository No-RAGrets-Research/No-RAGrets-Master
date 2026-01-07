import fitz, re
from pathlib import Path

pdf = fitz.open("data/papers_pdf/Copy of Hou et al. 1984.pdf")  # 换成任意一个
for i, page in enumerate(pdf):
    text = page.get_text("text")
    matches = re.findall(r'(Figure|Fig\.|Table)\s*\d+', text, re.IGNORECASE)
    if matches:
        print(f"Page {i+1}: found captions -> {matches}")
