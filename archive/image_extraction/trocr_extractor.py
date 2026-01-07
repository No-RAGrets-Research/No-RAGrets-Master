from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
from pdf2image import convert_from_path
from pathlib import Path
import json
import sys
import time
import cv2
import numpy as np

def extract_with_trocr(pdf_path: str, out_dir: str, 
                      dpi: int = 300,
                      use_gpu: bool = True) -> dict:
    """
    Extract text from PDF using Microsoft TrOCR model (more stable alternative to DeepSeek).
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    
    print("TrOCR Extraction")
    print("=" * 50)
    
    # Set up device
    if use_gpu and torch.cuda.is_available():
        device = 'cuda'
        print("Using GPU for OCR processing")
    else:
        device = 'cpu'
        print("Using CPU for OCR processing")
    
    try:
        print("Loading TrOCR model...")
        # Use Microsoft's TrOCR model - much more stable
        processor = TrOCRProcessor.from_pretrained('microsoft/trocr-large-printed')
        model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-large-printed')
        model.to(device)
        
        # Convert PDF to images
        print(f"Converting PDF to images (DPI: {dpi})...")
        pages = convert_from_path(pdf_path, dpi=dpi)
        print(f"Converted {len(pages)} pages")
        
        results = {
            "method": "Microsoft TrOCR",
            "pages_processed": 0,
            "total_pages": len(pages),
            "processing_time": 0,
            "extracted_content": {
                "full_text": "",
                "structured_markdown": "",
                "tables": [],
                "metadata": {
                    "model": "microsoft/trocr-large-printed",
                    "dpi": dpi,
                    "device": device
                }
            },
            "per_page_results": [],
            "output_files": []
        }
        
        full_text_parts = []
        markdown_parts = []
        
        for page_num, page_image in enumerate(pages, 1):
            print(f"Processing page {page_num}/{len(pages)}...")
            
            try:
                # Convert PIL to numpy array for preprocessing
                page_array = np.array(page_image)
                
                # Optional: preprocessing for better OCR results
                # Convert to grayscale
                if len(page_array.shape) == 3:
                    gray = cv2.cvtColor(page_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = page_array
                
                # Apply threshold to get binary image
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Convert back to PIL Image
                processed_image = Image.fromarray(binary)
                
                # Use original image for TrOCR (it handles preprocessing well)
                page_text = extract_text_from_image(page_image, processor, model, device)
                
                full_text_parts.append(f"=== PAGE {page_num} ===\n{page_text}\n")
                markdown_parts.append(f"## Page {page_num}\n\n{page_text}\n")
                
                # Simple table detection (basic pattern matching)
                tables_on_page = detect_simple_tables(page_text)
                
                page_result = {
                    "page": page_num,
                    "success": True,
                    "content": {
                        "text_extracted": True,
                        "text_length": len(page_text),
                        "tables_detected": len(tables_on_page)
                    }
                }
                
                results["per_page_results"].append(page_result)
                results["pages_processed"] += 1
                
            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                page_result = {
                    "page": page_num,
                    "success": False,
                    "error": str(e)
                }
                results["per_page_results"].append(page_result)
        
        # Combine all text
        results["extracted_content"]["full_text"] = "\n".join(full_text_parts)
        results["extracted_content"]["structured_markdown"] = "# Document Content\n\n" + "\n".join(markdown_parts)
        
        results["processing_time"] = time.time() - start_time
        
        # Save consolidated outputs
        save_consolidated_outputs(results, out_dir)
        
        return results
        
    except Exception as e:
        return {"error": f"Failed to process with TrOCR: {e}"}

def extract_text_from_image(image: Image.Image, processor, model, device: str) -> str:
    """Extract text from a single image using TrOCR."""
    try:
        # Process image
        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)
        
        # Generate text
        with torch.no_grad():
            generated_ids = model.generate(pixel_values, max_length=1000)
        
        # Decode text
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return generated_text.strip()
        
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""

def detect_simple_tables(text: str) -> list:
    """Simple table detection based on text patterns."""
    tables = []
    lines = text.split('\n')
    
    # Look for table-like patterns (multiple columns separated by spaces/tabs)
    table_lines = []
    for line in lines:
        # Simple heuristic: if line has multiple "columns" (3+ separated by significant whitespace)
        parts = line.split()
        if len(parts) >= 3:
            # Check if parts look like table data (contains numbers, short text, etc.)
            if any(part.replace('.', '').replace(',', '').isdigit() for part in parts):
                table_lines.append(line)
    
    # If we found table-like lines, group them
    if table_lines:
        table_text = '\n'.join(table_lines)
        tables.append({
            "table_id": 1,
            "confidence": 0.7,  # Simple detection, lower confidence
            "text": table_text,
            "method": "pattern_matching"
        })
    
    return tables

def save_consolidated_outputs(results: dict, out_dir: str):
    """Save consolidated output files for comparison."""
    
    # 1. Full text file
    full_text_path = Path(out_dir, "full_document_text.txt")
    with open(full_text_path, 'w', encoding='utf-8') as f:
        f.write(results["extracted_content"]["full_text"])
    results["output_files"].append(str(full_text_path))
    
    # 2. Structured markdown file
    markdown_path = Path(out_dir, "structured_document.md")
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(results["extracted_content"]["structured_markdown"])
    results["output_files"].append(str(markdown_path))
    
    # 3. Tables file (if any detected)
    if results["extracted_content"]["tables"]:
        tables_path = Path(out_dir, "extracted_tables.md")
        with open(tables_path, 'w', encoding='utf-8') as f:
            f.write("# Extracted Tables\n\n")
            for table in results["extracted_content"]["tables"]:
                f.write(f"## Table {table['table_id']}\n\n")
                f.write(f"**Method:** {table['method']}\n")
                f.write(f"**Confidence:** {table['confidence']}\n\n")
                f.write("```\n")
                f.write(table["text"])
                f.write("\n```\n\n---\n\n")
        results["output_files"].append(str(tables_path))
    
    # 4. Summary JSON
    summary_path = Path(out_dir, "extraction_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    results["output_files"].append(str(summary_path))

def print_extraction_summary(results: dict):
    """Print a formatted summary of extraction results."""
    print("\n" + "="*50)
    print("TROCR EXTRACTION SUMMARY")
    print("="*50)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"Method: {results['method']}")
    print(f"Pages processed: {results['pages_processed']}/{results['total_pages']}")
    print(f"Processing time: {results['processing_time']:.1f} seconds")
    if results['total_pages'] > 0:
        print(f"Success rate: {results['pages_processed']/results['total_pages']*100:.1f}%")
    print(f"Output files: {len(results['output_files'])}")
    
    # Character count
    total_chars = len(results['extracted_content']['full_text'])
    print(f"Total characters extracted: {total_chars:,}")
    
    print("\nOutput files:")
    for file_path in results['output_files']:
        print(f"  {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trocr_extractor.py <pdf_path> [output_dir]")
        print("Example: python trocr_extractor.py 'paper.pdf' trocr_results")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "trocr_results"
    
    results = extract_with_trocr(pdf_path, out_dir)
    print_extraction_summary(results)