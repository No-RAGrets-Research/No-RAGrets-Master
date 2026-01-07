import fitz  # PyMuPDF
from pathlib import Path
import sys

def extract_embedded_images(pdf_path: str, out_dir: str) -> list[str]:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    seen = set()
    out_files = []
    for page in doc:
        for xref, *_ in page.get_images(full=True):
            if xref in seen: 
                continue
            seen.add(xref)
            pix = fitz.Pixmap(doc, xref)
            # ensure RGB
            if pix.alpha: pix = fitz.Pixmap(pix, 0)  
            fpath = Path(out_dir, f"img_{xref}.png")
            pix.save(fpath.as_posix())
            out_files.append(fpath.as_posix())
    return out_files

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python pymupdf_image_extractor.py <pdf_path> [output_dir]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else "extracted_images"
    files = extract_embedded_images(pdf_path, out_dir)
    print(f"Extracted {len(files)} images to {out_dir}")
