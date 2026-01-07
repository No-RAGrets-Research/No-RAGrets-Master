import os
import glob
import json
import pathlib
from docling.document_converter import DocumentConverter


def parse_pdfs(input_dir="data/papers_pdf", output_dir="data/parsed_json", skip_existing=True):
    """
    Parse all PDFs in input_dir into structured JSON files using Docling.

    Args:
        input_dir (str): Path to folder containing PDF files.
        output_dir (str): Path to folder where JSON files will be saved.
        skip_existing (bool): If True, skip files already parsed.
    """
    # === Path preparation ===
    os.makedirs(output_dir, exist_ok=True)

    # === Initialize Docling converter ===
    converter = DocumentConverter()

    # === Find all PDF files ===
    pdf_paths = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))
    print(f"Found {len(pdf_paths)} PDFs in {input_dir}")

    success, failed, skipped = 0, 0, 0

    for pdf_path in pdf_paths:
        name = pathlib.Path(pdf_path).stem
        json_path = os.path.join(output_dir, f"{name}.json")

        # === Skip already parsed files ===
        if skip_existing and os.path.exists(json_path):
            print(f"[Skip] {name} already parsed.")
            skipped += 1
            continue

        try:
            # === Convert PDF ===
            result = converter.convert(pdf_path)
            doc = result.document

            # === Export JSON ===
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(doc.export_to_dict(), f, ensure_ascii=False, indent=2)

            print(f"[✅ OK] {name}")
            success += 1

        except Exception as e:
            print(f"[❌ FAIL] {name}: {e}")
            failed += 1
            continue

    # === Results summary ===
    print("\n==================== SUMMARY ====================")
    print(f"Successfully parsed: {success}")
    print(f"Skipped (already done): {skipped}")
    print(f"Failed: {failed}")
    print(f"Output folder: {output_dir}")
    print("=================================================")


# Allow running this file directly
if __name__ == "__main__":
    parse_pdfs()
