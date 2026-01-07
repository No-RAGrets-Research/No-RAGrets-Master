# Simple figure extractor using basic computer vision
# pip install pdf2image pillow opencv-python
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import sys

def extract_figures_with_cv(pdf_path: str, out_dir: str, min_area: int = 10000) -> list[str]:
    """Extract figures from PDF using basic computer vision techniques."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, dpi=200)
    
    out_files = []
    for i, pil_img in enumerate(pages):
        # Convert PIL to OpenCV format
        img_array = np.array(pil_img.convert("RGB"))
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and aspect ratio to find potential figures
        figure_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                
                # Filter by aspect ratio and size to find likely figures
                if 0.3 < aspect_ratio < 3.0 and w > 100 and h > 100:
                    # Extract the region
                    margin = 10  # Add small margin
                    x1 = max(0, x - margin)
                    y1 = max(0, y - margin)
                    x2 = min(img_array.shape[1], x + w + margin)
                    y2 = min(img_array.shape[0], y + h + margin)
                    
                    crop = img_array[y1:y2, x1:x2]
                    
                    if crop.size > 0:
                        figure_count += 1
                        crop_img = Image.fromarray(crop)
                        fpath = Path(out_dir, f"page{i+1:03d}_fig{figure_count:02d}_cv.png")
                        crop_img.save(fpath.as_posix())
                        out_files.append(fpath.as_posix())
    
    return out_files

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python cv_image_extractor.py <pdf_path> [output_dir]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else "extracted_figures_cv"
    files = extract_figures_with_cv(pdf_path, out_dir)
    print(f"Extracted {len(files)} potential figures to {out_dir}")