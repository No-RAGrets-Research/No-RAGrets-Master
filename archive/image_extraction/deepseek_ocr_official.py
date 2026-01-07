from transformers import AutoModel, AutoTokenizer
import torch
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import sys
import json
import os
import time

def extract_with_deepseek_ocr_official(pdf_path: str, out_dir: str, 
                                      dpi: int = 300,
                                      base_size: int = 1024,
                                      image_size: int = 640,
                                      use_gpu: bool = True) -> dict:
    """
    Extract text and structure from PDF using DeepSeek OCR model (official API).
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    
    print("DeepSeek OCR Extraction (Official API)")
    print("=" * 50)
    
    # Set up device
    if use_gpu and torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = '0'
        device = 'cuda'
        print("Using GPU for OCR processing")
    else:
        device = 'cpu'
        print("Using CPU for OCR processing")
    
    # Load model and tokenizer using exact official format
    model_name = 'deepseek-ai/DeepSeek-OCR'
    
    try:
        print("Loading DeepSeek OCR model...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        if device == 'cuda':
            model = AutoModel.from_pretrained(
                model_name, 
                _attn_implementation='flash_attention_2', 
                trust_remote_code=True, 
                use_safetensors=True
            )
            model = model.eval().cuda().to(torch.bfloat16)
        else:
            # For CPU, avoid flash attention and bfloat16
            model = AutoModel.from_pretrained(
                model_name, 
                trust_remote_code=True, 
                use_safetensors=True
            )
            model = model.eval()
        
        print("Model loaded successfully!")
        
        # Convert PDF to images
        print(f"Converting PDF to images (DPI: {dpi})...")
        pages = convert_from_path(pdf_path, dpi=dpi)
        print(f"Converted {len(pages)} pages")
        
        results = {
            "method": "DeepSeek OCR (Official)",
            "pages_processed": 0,
            "total_pages": len(pages),
            "processing_time": 0,
            "extracted_content": {
                "full_text": "",
                "structured_markdown": "",
                "tables": [],
                "metadata": {
                    "model": model_name,
                    "dpi": dpi,
                    "base_size": base_size,
                    "image_size": image_size,
                    "device": device
                }
            },
            "per_page_results": [],
            "output_files": []
        }
        
        full_text_parts = []
        markdown_parts = []
        
        # Create temporary image directory
        temp_img_dir = Path(out_dir, "temp_images")
        temp_img_dir.mkdir(exist_ok=True)
        
        # Process each page
        for page_num, page_image in enumerate(pages, 1):
            print(f"Processing page {page_num}/{len(pages)}...")
            
            try:
                # Save image temporarily
                temp_image_path = temp_img_dir / f"page_{page_num:03d}.jpg"
                page_image.save(temp_image_path, 'JPEG', quality=95)
                
                # Try different prompts for better extraction
                prompts = [
                    "<image>\n<|grounding|>Convert the document to markdown. ",
                    "<image>\nFree OCR. ",
                    "<image>\n<|grounding|>Extract all text and tables from this document page. "
                ]
                
                best_result = ""
                best_length = 0
                
                for prompt in prompts:
                    try:
                        # Use official DeepSeek OCR API
                        page_output_dir = Path(out_dir, f"page_{page_num:03d}_output")
                        page_output_dir.mkdir(exist_ok=True)
                        
                        res = model.infer(
                            tokenizer, 
                            prompt=prompt, 
                            image_file=str(temp_image_path), 
                            output_path=str(page_output_dir), 
                            base_size=base_size, 
                            image_size=image_size, 
                            crop_mode=True, 
                            save_results=True, 
                            test_compress=True
                        )
                        
                        # Extract text from result
                        if res and len(str(res)) > best_length:
                            best_result = str(res)
                            best_length = len(best_result)
                            
                    except Exception as e:
                        print(f"Prompt '{prompt[:30]}...' failed: {e}")
                        continue
                
                if best_result:
                    page_text = best_result
                    full_text_parts.append(f"=== PAGE {page_num} ===\n{page_text}\n")
                    markdown_parts.append(f"## Page {page_num}\n\n{page_text}\n")
                    
                    # Detect tables in the extracted text
                    tables_on_page = detect_tables_in_text(page_text, page_num)
                    results["extracted_content"]["tables"].extend(tables_on_page)
                    
                    page_result = {
                        "page": page_num,
                        "success": True,
                        "content": {
                            "text_extracted": True,
                            "text_length": len(page_text),
                            "tables_detected": len(tables_on_page)
                        }
                    }
                    results["pages_processed"] += 1
                else:
                    page_result = {
                        "page": page_num,
                        "success": False,
                        "error": "No text extracted from any prompt"
                    }
                
                results["per_page_results"].append(page_result)
                
                # Clean up temporary image
                if temp_image_path.exists():
                    temp_image_path.unlink()
                
            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                page_result = {
                    "page": page_num,
                    "success": False,
                    "error": str(e)
                }
                results["per_page_results"].append(page_result)
        
        # Clean up temporary directory
        if temp_img_dir.exists():
            temp_img_dir.rmdir()
        
        # Combine all text
        results["extracted_content"]["full_text"] = "\n".join(full_text_parts)
        results["extracted_content"]["structured_markdown"] = "# Document Content\n\n" + "\n".join(markdown_parts)
        
        results["processing_time"] = time.time() - start_time
        
        # Save consolidated outputs
        save_consolidated_outputs(results, out_dir)
        
        return results
        
    except Exception as e:
        return {"error": f"Failed to load model: {e}"}

def detect_tables_in_text(text: str, page_num: int) -> list:
    """Detect tables in extracted text."""
    tables = []
    lines = text.split('\n')
    
    # Look for markdown table patterns
    table_lines = []
    in_table = False
    
    for line in lines:
        # Markdown table detection
        if '|' in line and line.count('|') >= 2:
            table_lines.append(line)
            in_table = True
        elif in_table and line.strip() == '':
            # End of table
            if len(table_lines) >= 2:  # At least header + separator
                table_text = '\n'.join(table_lines)
                tables.append({
                    "table_id": len(tables) + 1,
                    "page": page_num,
                    "confidence": 0.9,
                    "markdown": table_text,
                    "method": "deepseek_ocr_markdown"
                })
            table_lines = []
            in_table = False
        elif in_table:
            table_lines.append(line)
    
    # Check for remaining table at end
    if len(table_lines) >= 2:
        table_text = '\n'.join(table_lines)
        tables.append({
            "table_id": len(tables) + 1,
            "page": page_num,
            "confidence": 0.9,
            "markdown": table_text,
            "method": "deepseek_ocr_markdown"
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
                f.write(f"## Table {table['table_id']} (Page {table['page']})\n\n")
                f.write(f"**Method:** {table['method']}\n")
                f.write(f"**Confidence:** {table['confidence']}\n\n")
                f.write(table["markdown"])
                f.write("\n\n---\n\n")
        results["output_files"].append(str(tables_path))
    
    # 4. Summary JSON
    summary_path = Path(out_dir, "extraction_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    results["output_files"].append(str(summary_path))

def print_extraction_summary(results: dict):
    """Print a formatted summary of extraction results."""
    print("\n" + "="*50)
    print("DEEPSEEK OCR EXTRACTION SUMMARY")
    print("="*50)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"Method: {results['method']}")
    print(f"Pages processed: {results['pages_processed']}/{results['total_pages']}")
    print(f"Processing time: {results['processing_time']:.1f} seconds")
    print(f"Tables found: {len(results['extracted_content']['tables'])}")
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
        print("Usage: python deepseek_ocr_official.py <pdf_path> [output_dir]")
        print("Example: python deepseek_ocr_official.py 'paper.pdf' deepseek_results")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "deepseek_official_results"
    
    results = extract_with_deepseek_ocr_official(pdf_path, out_dir)
    print_extraction_summary(results)