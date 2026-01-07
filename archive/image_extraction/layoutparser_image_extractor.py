# pip install layoutparser[layoutmodels] pdf2image pillow
# Also install poppler for pdf2image (OS package manager).
import layoutparser as lp
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import sys

def extract_figures_with_layoutparser(pdf_path: str, out_dir: str, score_thr: float = 0.5) -> list[str]:
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Use EfficientDet model (the only one available in this installation)
    print("Loading EfficientDet layout model...")
    model = lp.EfficientDetLayoutModel(
        config_path="lp://PubLayNet/tf_efficientdet_d1/config",
        label_map={0:"Text",1:"Title",2:"List",3:"Table",4:"Figure"},
        device="cpu",
    )

    # 2) Rasterize PDF pages to images
    print("Converting PDF pages to images...")
    pages = convert_from_path(pdf_path, dpi=200)

    out_files = []
    for i, pil_img in enumerate(pages):
        print(f"Processing page {i+1}/{len(pages)}...")
        image = pil_img.convert("RGB")
        layout = model.detect(image)

        # 3) Keep only "Figure" blocks with score above threshold
        figures = [b for b in layout if b.type == "Figure" and b.score >= score_thr]
        print(f"  Found {len(figures)} figures on page {i+1}")
        
        for j, fig in enumerate(figures):
            x1, y1, x2, y2 = map(int, fig.block.coordinates)
            crop = image.crop((x1, y1, x2, y2))
            fpath = Path(out_dir, f"page{i+1:03d}_fig{j+1:02d}.png")
            crop.save(fpath.as_posix())
            out_files.append(fpath.as_posix())
            print(f"  Saved figure {j+1} (score: {fig.score:.3f})")

    return out_files

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python layoutparser_image_extractor.py <pdf_path> [output_dir] [score_threshold]")
        print("  score_threshold: confidence threshold (0.0-1.0, default: 0.5)")
        sys.exit(1)
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) >= 3 else "extracted_figures"
    score_thr = float(sys.argv[3]) if len(sys.argv) == 4 else 0.5
    
    print(f"Using confidence threshold: {score_thr}")
    files = extract_figures_with_layoutparser(pdf_path, out_dir, score_thr)
    print(f"Extracted {len(files)} figures to {out_dir}")

# usage:
# files = extract_figures_with_layoutparser("paper.pdf", "out_figs")
# print(files)
