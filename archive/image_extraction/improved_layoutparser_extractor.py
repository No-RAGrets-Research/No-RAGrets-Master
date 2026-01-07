import layoutparser as lp
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import sys
import numpy as np

def extract_figures_improved_layoutparser(pdf_path: str, out_dir: str, 
                                        score_threshold: float = 0.3,
                                        dpi: int = 300,
                                        enable_nms: bool = True) -> list[str]:
    """
    Improved figure extraction with better settings and post-processing.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    # Use higher DPI to preserve more detail
    print(f"Converting PDF to images at {dpi} DPI...")
    pages = convert_from_path(pdf_path, dpi=dpi)
    
    # Load model with optimized settings
    model = lp.EfficientDetLayoutModel(
        config_path="lp://PubLayNet/tf_efficientdet_d1/config",
        label_map={0:"Text", 1:"Title", 2:"List", 3:"Table", 4:"Figure"},
        device="cpu"
    )
    
    out_files = []
    all_detections = []
    
    for page_num, pil_img in enumerate(pages):
        print(f"Processing page {page_num + 1}...")
        
        # Convert to numpy array for layoutparser
        img_array = np.array(pil_img)
        
        # Detect layout elements
        layout = model.detect(img_array)
        
        # Filter for figures with lower threshold - use direct filtering
        figures = [block for block in layout if block.type == "Figure"]
        
        # Apply custom filtering
        valid_figures = []
        for fig in figures:
            if fig.score >= score_threshold:
                # Additional size filtering
                width = fig.block.coordinates[2] - fig.block.coordinates[0]
                height = fig.block.coordinates[3] - fig.block.coordinates[1]
                area = width * height
                
                # Minimum size requirements (adjust as needed)
                if width > 50 and height > 50 and area > 5000:
                    valid_figures.append(fig)
                    all_detections.append((page_num, fig))
        
        # Extract valid figures
        for i, fig in enumerate(valid_figures):
            # Add padding around detected region
            padding = 10
            x1 = max(0, int(fig.block.coordinates[0]) - padding)
            y1 = max(0, int(fig.block.coordinates[1]) - padding)
            x2 = min(pil_img.width, int(fig.block.coordinates[2]) + padding)
            y2 = min(pil_img.height, int(fig.block.coordinates[3]) + padding)
            
            # Crop the figure
            crop = pil_img.crop((x1, y1, x2, y2))
            
            # Save with detailed filename
            score_str = f"{fig.score:.3f}"
            fpath = Path(out_dir, f"page{page_num+1:03d}_fig{i+1:02d}_score{score_str}_lp.png")
            crop.save(fpath.as_posix(), "PNG", quality=95)
            out_files.append(fpath.as_posix())
            
            print(f"  Found figure: {fpath.name} (score: {fig.score:.3f})")
    
    # Optional: Apply Non-Maximum Suppression to remove overlapping detections
    if enable_nms and len(all_detections) > 1:
        print("Applying overlap filtering...")
        filtered_files = apply_nms_to_files(out_files, all_detections, iou_threshold=0.5)
        # Remove overlapping files
        for file in set(out_files) - set(filtered_files):
            Path(file).unlink(missing_ok=True)
        out_files = filtered_files
    
    return out_files

def apply_nms_to_files(files: list, detections: list, iou_threshold: float = 0.5) -> list:
    """Simple overlap filtering for detected figures."""
    if len(files) <= 1:
        return files
    
    # Sort by confidence score (descending)
    sorted_detections = sorted(enumerate(detections), key=lambda x: x[1][1].score, reverse=True)
    
    keep = []
    for i, (file_idx, (page_num, detection)) in enumerate(sorted_detections):
        should_keep = True
        coords1 = detection.block.coordinates
        
        for kept_idx in keep:
            kept_page, kept_detection = detections[kept_idx]
            if kept_page == page_num:  # Same page
                coords2 = kept_detection.block.coordinates
                if calculate_iou(coords1, coords2) > iou_threshold:
                    should_keep = False
                    break
        
        if should_keep:
            keep.append(file_idx)
    
    return [files[i] for i in keep]

def calculate_iou(box1, box2):
    """Calculate Intersection over Union of two bounding boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    if x2 <= x1 or y2 <= y1:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python improved_layoutparser_extractor.py <pdf_path> [output_dir] [score_threshold] [dpi]")
        print("Example: python improved_layoutparser_extractor.py 'paper.pdf' figures 0.3 300")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_figures_improved"
    score_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    
    print(f"Extracting figures with threshold {score_threshold} at {dpi} DPI...")
    files = extract_figures_improved_layoutparser(pdf_path, out_dir, score_threshold, dpi)
    print(f"\nExtracted {len(files)} figures to {out_dir}")
    for f in files:
        print(f"  {f}")