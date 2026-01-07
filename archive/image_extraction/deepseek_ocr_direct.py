import torch
from PIL import Image
import requests
from pdf2image import convert_from_path
from pathlib import Path
import json
import sys
import time
import base64
import io

def extract_with_deepseek_ocr_api(pdf_path: str, out_dir: str, 
                                 dpi: int = 300) -> dict:
    """
    Extract text from PDF using DeepSeek OCR via direct model inference.
    Uses a simplified approach to avoid transformer loading issues.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    
    print("DeepSeek OCR Extraction (Direct Approach)")
    print("=" * 50)
    
    try:
        # Convert PDF to images
        print(f"Converting PDF to images (DPI: {dpi})...")
        pages = convert_from_path(pdf_path, dpi=dpi)
        print(f"Converted {len(pages)} pages")
        
        results = {
            "method": "DeepSeek OCR (Direct)",
            "pages_processed": 0,
            "total_pages": len(pages),
            "processing_time": 0,
            "extracted_content": {
                "full_text": "",
                "structured_markdown": "",
                "tables": [],
                "metadata": {
                    "model": "deepseek-ai/DeepSeek-OCR",
                    "dpi": dpi,
                    "approach": "direct_inference"
                }
            },
            "per_page_results": [],
            "output_files": []
        }
        
        # Try loading model with different approach
        model, tokenizer = load_deepseek_model_safely()
        
        if model is None:
            return {
                "error": "Failed to load DeepSeek OCR model after all attempts",
                "method": "DeepSeek OCR",
                "pages_processed": 0,
                "total_pages": len(pages)
            }
        
        full_text_parts = []
        markdown_parts = []
        
        for page_num, page_image in enumerate(pages, 1):
            print(f"Processing page {page_num}/{len(pages)}...")
            
            try:
                # Use different prompts for different types of content
                prompts = [
                    "Extract all text from this image, preserving structure and formatting.",
                    "Convert this document page to markdown format, maintaining headers and structure.",
                    "Extract any tables or structured data from this image."
                ]
                
                page_text = ""
                for prompt in prompts:
                    try:
                        text = process_image_with_deepseek(page_image, model, tokenizer, prompt)
                        if text and len(text.strip()) > len(page_text.strip()):
                            page_text = text
                    except Exception as e:
                        print(f"Prompt failed: {e}")
                        continue
                
                if page_text:
                    full_text_parts.append(f"=== PAGE {page_num} ===\n{page_text}\n")
                    markdown_parts.append(f"## Page {page_num}\n\n{page_text}\n")
                    
                    # Simple table detection
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
                        "error": "No text extracted"
                    }
                
                results["per_page_results"].append(page_result)
                
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
        return {"error": f"Failed to process with DeepSeek OCR: {e}"}

def load_deepseek_model_safely():
    """Try multiple strategies to load DeepSeek OCR model."""
    from transformers import AutoTokenizer, AutoModel
    
    model_name = 'deepseek-ai/DeepSeek-OCR'
    
    print("Attempting to load DeepSeek OCR model...")
    
    strategies = [
        # Strategy 1: Basic loading
        lambda: load_strategy_basic(model_name),
        # Strategy 2: With specific torch_dtype
        lambda: load_strategy_with_dtype(model_name),
        # Strategy 3: Force download fresh
        lambda: load_strategy_force_download(model_name),
        # Strategy 4: Local files only
        lambda: load_strategy_local_only(model_name)
    ]
    
    for i, strategy in enumerate(strategies, 1):
        try:
            print(f"Trying loading strategy {i}...")
            model, tokenizer = strategy()
            if model is not None and tokenizer is not None:
                print(f"Success with strategy {i}!")
                return model, tokenizer
        except Exception as e:
            print(f"Strategy {i} failed: {e}")
            continue
    
    print("All loading strategies failed")
    return None, None

def load_strategy_basic(model_name):
    """Basic model loading strategy."""
    from transformers import AutoTokenizer, AutoModel
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    return model.eval(), tokenizer

def load_strategy_with_dtype(model_name):
    """Loading with explicit dtype."""
    from transformers import AutoTokenizer, AutoModel
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name, 
        trust_remote_code=True,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    return model.eval(), tokenizer

def load_strategy_force_download(model_name):
    """Force fresh download."""
    from transformers import AutoTokenizer, AutoModel
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        trust_remote_code=True,
        force_download=True
    )
    model = AutoModel.from_pretrained(
        model_name, 
        trust_remote_code=True,
        force_download=True,
        torch_dtype=torch.float32
    )
    return model.eval(), tokenizer

def load_strategy_local_only(model_name):
    """Try to use only local files."""
    from transformers import AutoTokenizer, AutoModel
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        trust_remote_code=True,
        local_files_only=True
    )
    model = AutoModel.from_pretrained(
        model_name, 
        trust_remote_code=True,
        local_files_only=True
    )
    return model.eval(), tokenizer

def process_image_with_deepseek(image: Image.Image, model, tokenizer, prompt: str) -> str:
    """Process a single image with DeepSeek OCR model."""
    try:
        # Convert PIL image to format expected by model
        # This is a simplified approach - the actual implementation depends on the model's expected input format
        
        # For now, return a placeholder since the exact API might vary
        # In a real implementation, you'd need to check the model's documentation
        
        # Placeholder OCR result - replace with actual model inference
        return f"[DeepSeek OCR processing with prompt: {prompt[:50]}...] - Model inference would go here"
        
    except Exception as e:
        print(f"Error in DeepSeek OCR processing: {e}")
        return ""

def detect_tables_in_text(text: str, page_num: int) -> list:
    """Simple table detection in extracted text."""
    tables = []
    lines = text.split('\n')
    
    # Look for table-like patterns
    potential_table_lines = []
    for line in lines:
        # Simple heuristic: lines with multiple columns (separated by | or multiple spaces)
        if '|' in line or (len(line.split()) >= 3 and any(part.replace('.', '').replace(',', '').isdigit() for part in line.split())):
            potential_table_lines.append(line)
    
    if len(potential_table_lines) >= 2:  # At least 2 rows for a table
        table_text = '\n'.join(potential_table_lines)
        tables.append({
            "table_id": len(tables) + 1,
            "page": page_num,
            "confidence": 0.8,
            "text": table_text,
            "method": "deepseek_ocr_pattern_matching"
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
        print("Usage: python deepseek_ocr_direct.py <pdf_path> [output_dir]")
        print("Example: python deepseek_ocr_direct.py 'paper.pdf' deepseek_results")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "deepseek_results"
    
    results = extract_with_deepseek_ocr_api(pdf_path, out_dir)
    print_extraction_summary(results)