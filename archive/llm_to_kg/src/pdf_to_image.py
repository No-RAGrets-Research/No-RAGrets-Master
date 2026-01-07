import fitz  # PyMuPDF
import re
import os
import json
from pathlib import Path

DATA_DIR = Path("data")
PDF_DIR = DATA_DIR / "papers_pdf"
IMG_DIR = DATA_DIR / "images"

def extract_figures_with_captions(pdf_path, output_dir, distance_threshold=800):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    results = []

    for page_index, page in enumerate(doc):
        text_blocks = page.get_text("blocks")

        # Step 1: 提取图像xref和bbox（新方法）
        image_info = []
        for img in page.get_image_info(xrefs=True):  # ✅ PyMuPDF 1.24+
            xref = img["xref"]
            bbox = fitz.Rect(img["bbox"]) if "bbox" in img else None
            if bbox:
                image_info.append({
                    "xref": xref,
                    "bbox": bbox
                })

        # Step 2: 找出caption
        captions = []
        for block in text_blocks:
            text = block[4].strip()
            if re.search(r'(Figure|Fig\.|Table)\s*\d+', text, re.IGNORECASE):
                captions.append({"text": text, "rect": fitz.Rect(block[:4])})

        # Step 3: 匹配caption与图片
        for img in image_info:   # ✅ 修正这里
            xref = img["xref"]
            bbox = img["bbox"]

            nearest = None
            nearest_dist = float("inf")

            for cap in captions:
                cap_center = (cap["rect"].y0 + cap["rect"].y1) / 2
                img_center = (bbox.y0 + bbox.y1) / 2
                dist = abs(img_center - cap_center)

                if dist < nearest_dist:
                    nearest = cap
                    nearest_dist = dist

            if nearest and nearest_dist < distance_threshold:
                print(f"[DEBUG] Page {page_index+1}: matched caption '{nearest['text'][:60]}' "
                      f"(dist={nearest_dist:.1f}) for image bbox={bbox}")

                try:
                    image = doc.extract_image(xref)
                except Exception as e:
                    print(f"⚠️  Skipping image xref={xref} ({e})")
                    continue

                img_bytes = image["image"]
                img_ext = image["ext"]
                img_name = f"page{page_index+1}_fig{len(results)+1}.{img_ext}"
                img_path = os.path.join(output_dir, img_name)
                with open(img_path, "wb") as f:
                    f.write(img_bytes)

                results.append({
                    "page": page_index + 1,
                    "caption": nearest["text"],
                    "image_path": img_path
                })

    # Step 4: 保存结果
    json_path = Path(output_dir) / "figures_metadata.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ {pdf_path.name}: Extracted {len(results)} figures with captions.")
    return results


def process_all_pdfs():
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDFs found in data/papers_pdf/")
        return

    all_metadata = {}
    for pdf_file in pdf_files:
        paper_name = pdf_file.stem
        output_dir = IMG_DIR / paper_name
        figures = extract_figures_with_captions(pdf_file, output_dir)
        all_metadata[paper_name] = figures

    metadata_path = IMG_DIR / "all_figures_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)
    print(f"📁 Saved combined metadata to {metadata_path}")


if __name__ == "__main__":
    process_all_pdfs()
