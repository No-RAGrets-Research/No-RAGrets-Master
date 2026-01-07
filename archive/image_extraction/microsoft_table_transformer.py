import torch
from transformers import DetrImageProcessor, TableTransformerForObjectDetection
from pdf2image import convert_from_path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys
import json

def extract_tables_microsoft_transformer(pdf_path: str, out_dir: str, 
                                       detection_threshold: float = 0.7,
                                       structure_threshold: float = 0.7,
                                       dpi: int = 300) -> dict:
    """
    Extract tables using Microsoft's Table Transformer models.
    
    Args:
        pdf_path: Path to PDF file
        out_dir: Output directory
        detection_threshold: Confidence threshold for table detection
        structure_threshold: Confidence threshold for structure recognition
        dpi: Resolution for PDF to image conversion
    
    Returns:
        Dictionary with extraction results
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    print("Loading Microsoft Table Transformer models...")
    print("=" * 60)
    
    # Load table detection model
    print("Loading table detection model...")
    detection_processor = DetrImageProcessor.from_pretrained("microsoft/table-transformer-detection")
    detection_model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")
    
    # Load table structure recognition model
    print("Loading table structure model...")
    structure_processor = DetrImageProcessor.from_pretrained("microsoft/table-transformer-structure-recognition")
    structure_model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-structure-recognition")
    
    print(f"Converting PDF to images at {dpi} DPI...")
    pages = convert_from_path(pdf_path, dpi=dpi)
    print(f"Converted {len(pages)} pages")
    
    results = {
        "tables_detected": 0,
        "tables_with_structure": 0,
        "output_files": [],
        "table_details": []
    }
    
    for page_num, page_image in enumerate(pages):
        print(f"\nProcessing page {page_num + 1}...")
        
        # Step 1: Detect tables on the page
        tables = detect_tables_on_page(page_image, detection_processor, detection_model, detection_threshold)
        
        if not tables:
            print(f"  No tables found on page {page_num + 1}")
            continue
        
        print(f"  Found {len(tables)} table(s) on page {page_num + 1}")
        results["tables_detected"] += len(tables)
        
        # Step 2: Process each detected table
        for table_idx, (table_bbox, table_score) in enumerate(tables):
            table_id = f"page{page_num+1:03d}_table{table_idx+1:02d}"
            print(f"    Processing table {table_id} (confidence: {table_score:.3f})")
            
            # Extract table region with padding
            table_crop = extract_table_region(page_image, table_bbox, padding=20)
            
            # Save raw table image
            table_image_path = Path(out_dir, f"{table_id}_raw.png")
            table_crop.save(table_image_path)
            results["output_files"].append(str(table_image_path))
            
            # Step 3: Analyze table structure
            structure_info = analyze_table_structure(
                table_crop, structure_processor, structure_model, structure_threshold
            )
            
            # Save annotated image with structure
            if structure_info["elements"]:
                annotated_image = draw_table_structure_annotations(table_crop, structure_info)
                annotated_path = Path(out_dir, f"{table_id}_annotated.png")
                annotated_image.save(annotated_path)
                results["output_files"].append(str(annotated_path))
                results["tables_with_structure"] += 1
                
                print(f"      Structure: {structure_info['summary']}")
            else:
                print(f"      No structure detected above threshold {structure_threshold}")
            
            # Save table metadata
            table_detail = {
                "table_id": table_id,
                "page": page_num + 1,
                "detection_score": float(table_score),
                "bbox": [float(x) for x in table_bbox],
                "structure": structure_info,
                "files": {
                    "raw_image": str(table_image_path),
                    "annotated_image": str(annotated_path) if structure_info["elements"] else None
                }
            }
            results["table_details"].append(table_detail)
    
    # Save summary JSON
    summary_path = Path(out_dir, "table_extraction_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    results["output_files"].append(str(summary_path))
    
    return results

def detect_tables_on_page(page_image: Image.Image, processor, model, threshold: float) -> list:
    """Detect table bounding boxes on a page."""
    
    # Prepare inputs
    inputs = processor(images=page_image, return_tensors="pt")
    
    # Run detection
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Convert outputs to bounding boxes
    target_sizes = torch.tensor([page_image.size[::-1]])  # height, width
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]
    
    # Filter tables by confidence
    tables = []
    for score, box in zip(results["scores"], results["boxes"]):
        if score > threshold:
            tables.append((box.tolist(), float(score)))
    
    return tables

def extract_table_region(page_image: Image.Image, bbox: list, padding: int = 20) -> Image.Image:
    """Extract table region from page with padding."""
    x1, y1, x2, y2 = bbox
    
    # Add padding and ensure within image bounds
    x1 = max(0, int(x1) - padding)
    y1 = max(0, int(y1) - padding)
    x2 = min(page_image.width, int(x2) + padding)
    y2 = min(page_image.height, int(y2) + padding)
    
    return page_image.crop((x1, y1, x2, y2))

def analyze_table_structure(table_image: Image.Image, processor, model, threshold: float) -> dict:
    """Analyze internal table structure (rows, columns, cells)."""
    
    # Prepare inputs
    inputs = processor(images=table_image, return_tensors="pt")
    
    # Run structure recognition
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Convert outputs
    target_sizes = torch.tensor([table_image.size[::-1]])
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]
    
    # Microsoft Table Transformer structure labels
    structure_labels = {
        0: "table",
        1: "table column",
        2: "table row", 
        3: "table column header",
        4: "table projected row header",
        5: "table spanning cell"
    }
    
    # Organize detected elements
    elements = {
        "columns": [],
        "rows": [],
        "column_headers": [],
        "row_headers": [],
        "spanning_cells": [],
        "table_boundary": []
    }
    
    for score, label_id, box in zip(results["scores"], results["labels"], results["boxes"]):
        if score > threshold:
            label = structure_labels.get(label_id.item(), f"unknown_{label_id.item()}")
            element = {
                "type": label,
                "confidence": float(score),
                "bbox": [float(x) for x in box.tolist()]
            }
            
            # Categorize elements
            if "column header" in label:
                elements["column_headers"].append(element)
            elif "row header" in label:
                elements["row_headers"].append(element)
            elif "column" in label:
                elements["columns"].append(element)
            elif "row" in label:
                elements["rows"].append(element)
            elif "spanning" in label:
                elements["spanning_cells"].append(element)
            elif label == "table":
                elements["table_boundary"].append(element)
    
    # Create summary
    summary = {
        "columns": len(elements["columns"]),
        "rows": len(elements["rows"]),
        "column_headers": len(elements["column_headers"]),
        "row_headers": len(elements["row_headers"]),
        "spanning_cells": len(elements["spanning_cells"])
    }
    
    return {
        "elements": elements,
        "summary": summary,
        "total_elements": sum(len(v) if isinstance(v, list) else 0 for v in elements.values())
    }

def draw_table_structure_annotations(table_image: Image.Image, structure_info: dict) -> Image.Image:
    """Draw colored annotations showing detected table structure."""
    
    # Create annotated copy
    annotated = table_image.copy()
    draw = ImageDraw.Draw(annotated)
    
    # Color scheme for different elements
    colors = {
        "columns": "blue",
        "rows": "red", 
        "column_headers": "green",
        "row_headers": "orange",
        "spanning_cells": "purple",
        "table_boundary": "black"
    }
    
    line_widths = {
        "columns": 2,
        "rows": 2,
        "column_headers": 3,
        "row_headers": 3,
        "spanning_cells": 2,
        "table_boundary": 4
    }
    
    # Draw each type of element
    for element_type, elements in structure_info["elements"].items():
        color = colors.get(element_type, "gray")
        width = line_widths.get(element_type, 2)
        
        for element in elements:
            bbox = element["bbox"]
            x1, y1, x2, y2 = bbox
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
            
            # Add label
            try:
                font = ImageFont.load_default()
                label = f"{element['type']}: {element['confidence']:.2f}"
                draw.text((x1, y1-15), label, fill=color, font=font)
            except:
                # Fallback if font loading fails
                pass
    
    return annotated

def print_extraction_summary(results: dict):
    """Print a formatted summary of extraction results."""
    print("\n" + "="*60)
    print("TABLE EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total tables detected: {results['tables_detected']}")
    print(f"Tables with structure: {results['tables_with_structure']}")
    print(f"Output files created: {len(results['output_files'])}")
    
    if results['table_details']:
        print("\nDETAILED RESULTS:")
        print("-" * 40)
        for table in results['table_details']:
            print(f"{table['table_id']}:")
            print(f"   Page: {table['page']}")
            print(f"   Detection confidence: {table['detection_score']:.3f}")
            if table['structure']['summary']:
                summary = table['structure']['summary']
                print(f"   Structure: {summary['rows']} rows, {summary['columns']} cols")
                if summary['column_headers'] > 0:
                    print(f"   Headers: {summary['column_headers']} column headers")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python microsoft_table_transformer.py <pdf_path> [output_dir] [detection_threshold] [structure_threshold] [dpi]")
        print()
        print("Examples:")
        print("  python microsoft_table_transformer.py 'paper.pdf'")
        print("  python microsoft_table_transformer.py 'paper.pdf' tables 0.8 0.7 300")
        print()
        print("Parameters:")
        print("  detection_threshold: 0.0-1.0 (default: 0.7) - confidence for table detection")
        print("  structure_threshold: 0.0-1.0 (default: 0.7) - confidence for structure elements")
        print("  dpi: 150-600 (default: 300) - image resolution")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "microsoft_table_extraction"
    detection_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
    structure_threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.7
    dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 300
    
    print(f"Microsoft Table Transformer Extraction")
    print(f"PDF: {pdf_path}")
    print(f"Output: {out_dir}")
    print(f"Detection threshold: {detection_threshold}")
    print(f"Structure threshold: {structure_threshold}")
    print(f"DPI: {dpi}")
    
    try:
        results = extract_tables_microsoft_transformer(
            pdf_path, out_dir, detection_threshold, structure_threshold, dpi
        )
        print_extraction_summary(results)
        
        print("\nOutput files:")
        for file_path in results['output_files']:
            print(f"  {file_path}")
            
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)