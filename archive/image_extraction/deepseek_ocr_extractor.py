from transformers import AutoModel, AutoTokenizer
import torch
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import sys
import json
import os
import time
import warnings

def check_model_compatibility():
    """Check if DeepSeek OCR model is compatible with current transformers version."""
    try:
        # Try to import the specific component that's failing
        from transformers.models.llama.modeling_llama import LlamaFlashAttention2
        return True, None
    except ImportError as e:
        return False, str(e)

def get_compatible_model_info():
    """Get information about compatible model alternatives."""
    return {
        "recommended_transformers_version": "4.36.0 - 4.40.0",
        "current_issue": "LlamaFlashAttention2 import error",
        "alternative_models": [
            "microsoft/trocr-large-printed",
            "microsoft/trocr-base-printed", 
            "PaddlePaddle/PaddleOCR",
            "tesseract (fallback)"
        ],
        "suggested_fix": "pip install transformers==4.38.0"
    }

def extract_with_deepseek_ocr(pdf_path: str, out_dir: str, 
                            dpi: int = 300,
                            base_size: int = 1024,
                            image_size: int = 640,
                            use_gpu: bool = True) -> dict:
    """
    Extract text and structure from PDF using DeepSeek OCR model.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    
    print("DeepSeek OCR Extraction")
    print("=" * 50)
    
    # Set up device
    if use_gpu and torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = '0'
        device = 'cuda'
        print("Using GPU for OCR processing")
    else:
        device = 'cpu'
        print("Using CPU for OCR processing")
    
    # Load model and tokenizer with fallback strategies
    model_name = 'deepseek-ai/DeepSeek-OCR'
    
    try:
        print("Loading DeepSeek OCR model...")
        
        # Try multiple loading strategies
        model = None
        tokenizer = None
        
        # Strategy 1: Try with recommended settings
        try:
            print("Attempting standard loading...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            
            if device == 'cuda':
                model = AutoModel.from_pretrained(
                    model_name, 
                    trust_remote_code=True, 
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
            else:
                model = AutoModel.from_pretrained(
                    model_name, 
                    trust_remote_code=True,
                    torch_dtype=torch.float32
                )
                model = model.to(device)
            
            model = model.eval()
            print("Model loaded successfully!")
            
        except Exception as e1:
            print(f"Standard loading failed: {e1}")
            
            # Strategy 2: Try without flash attention
            try:
                print("Attempting loading without flash attention...")
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                model = AutoModel.from_pretrained(
                    model_name, 
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                    attn_implementation="eager"
                )
                model = model.to(device).eval()
                print("Model loaded with eager attention!")
                
            except Exception as e2:
                print(f"Eager attention loading failed: {e2}")
                
                # Strategy 3: Try with minimal options
                try:
                    print("Attempting minimal loading...")
                    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                    model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
                    model = model.to(device).eval()
                    print("Model loaded with minimal options!")
                    
                except Exception as e3:
                    print(f"All loading strategies failed")
                    raise e3
            
    except Exception as e:
        return {"error": f"Failed to load model: {e}"}
    
    # Convert PDF to images
    print(f"Converting PDF to images at {dpi} DPI...")
    pages = convert_from_path(pdf_path, dpi=dpi)
    print(f"Converted {len(pages)} pages")
    
    results = {
        "method": "DeepSeek OCR",
        "pages_processed": 0,
        "total_pages": len(pages),
        "processing_time": 0,
        "extracted_content": {
            "full_text": "",
            "structured_markdown": "",
            "tables": [],
            "metadata": {}
        },
        "per_page_results": [],
        "output_files": []
    }
    
    full_document_text = []
    full_document_markdown = []
    all_tables = []
    
    # Process each page
    for page_num, page_image in enumerate(pages):
        print(f"Processing page {page_num + 1}/{len(pages)}...")
        
        # Save page image temporarily
        temp_image_path = Path(out_dir, f"temp_page_{page_num+1:03d}.jpg")
        page_image.save(temp_image_path, "JPEG", quality=95)
        
        try:
            page_results = {}
            
            # Basic OCR extraction
            basic_prompt = "<image>\nFree OCR. "
            basic_output_dir = Path(out_dir, f"page_{page_num+1:03d}_basic")
            basic_output_dir.mkdir(exist_ok=True)
            
            basic_result = model.infer(
                tokenizer, 
                prompt=basic_prompt,
                image_file=str(temp_image_path),
                output_path=str(basic_output_dir),
                base_size=base_size,
                image_size=image_size,
                crop_mode=True,
                save_results=True,
                test_compress=True
            )
            page_results["basic_ocr"] = basic_result
            if basic_result:
                full_document_text.append(f"--- Page {page_num + 1} ---\n{basic_result}\n")
            
            # Markdown conversion
            markdown_prompt = "<image>\n<|grounding|>Convert the document to markdown. "
            markdown_output_dir = Path(out_dir, f"page_{page_num+1:03d}_markdown")
            markdown_output_dir.mkdir(exist_ok=True)
            
            markdown_result = model.infer(
                tokenizer,
                prompt=markdown_prompt,
                image_file=str(temp_image_path),
                output_path=str(markdown_output_dir),
                base_size=base_size,
                image_size=image_size,
                crop_mode=True,
                save_results=True,
                test_compress=True
            )
            page_results["markdown"] = markdown_result
            if markdown_result:
                full_document_markdown.append(f"# Page {page_num + 1}\n\n{markdown_result}\n\n---\n\n")
            
            # Table extraction
            table_prompt = "<image>\n<|grounding|>Extract all tables and convert to markdown format. "
            table_output_dir = Path(out_dir, f"page_{page_num+1:03d}_tables")
            table_output_dir.mkdir(exist_ok=True)
            
            table_result = model.infer(
                tokenizer,
                prompt=table_prompt,
                image_file=str(temp_image_path),
                output_path=str(table_output_dir),
                base_size=base_size,
                image_size=image_size,
                crop_mode=True,
                save_results=True,
                test_compress=True
            )
            page_results["tables"] = table_result
            if table_result and table_result.strip():
                all_tables.append({
                    "page": page_num + 1,
                    "content": table_result
                })
            
            # Store page results
            page_result = {
                "page": page_num + 1,
                "success": True,
                "content": page_results
            }
            results["per_page_results"].append(page_result)
            results["pages_processed"] += 1
            
            print(f"  Page {page_num + 1} completed successfully")
            
        except Exception as e:
            print(f"  Error processing page {page_num + 1}: {e}")
            error_result = {
                "page": page_num + 1,
                "success": False,
                "error": str(e)
            }
            results["per_page_results"].append(error_result)
        
        finally:
            # Clean up temporary image
            if temp_image_path.exists():
                temp_image_path.unlink()
    
    # Compile final results
    results["extracted_content"]["full_text"] = "\n".join(full_document_text)
    results["extracted_content"]["structured_markdown"] = "\n".join(full_document_markdown)
    results["extracted_content"]["tables"] = all_tables
    results["processing_time"] = time.time() - start_time
    
    # Save consolidated outputs
    save_consolidated_outputs(results, out_dir)
    
    return results

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
    
    # 3. Tables file
    if results["extracted_content"]["tables"]:
        tables_path = Path(out_dir, "extracted_tables.md")
        with open(tables_path, 'w', encoding='utf-8') as f:
            f.write("# Extracted Tables\n\n")
            for table in results["extracted_content"]["tables"]:
                f.write(f"## Page {table['page']}\n\n")
                f.write(table["content"])
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
    print(f"Success rate: {results['pages_processed']/results['total_pages']*100:.1f}%")
    print(f"Output files: {len(results['output_files'])}")
    
    print("\nOutput files:")
    for file_path in results['output_files']:
        print(f"  {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deepseek_ocr_extractor.py <pdf_path> [output_dir] [dpi] [use_gpu]")
        print("Example: python deepseek_ocr_extractor.py 'paper.pdf' deepseek_results 300 True")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "deepseek_ocr_results"
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    use_gpu = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else True
    
    results = extract_with_deepseek_ocr(pdf_path, out_dir, dpi, use_gpu=use_gpu)
    print_extraction_summary(results)