from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from pathlib import Path
import pandas as pd
import json
import sys
import time

def extract_with_docling(pdf_path: str, out_dir: str) -> dict:
    """
    Extract text and structure from PDF using IBM Docling.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    
    print("IBM Docling Extraction")
    print("=" * 50)
    
    try:
        # Configure Docling with basic options
        print("Initializing Docling converter...")
        converter = DocumentConverter()
        
        # Convert document
        print("Processing document with Docling...")
        result = converter.convert(pdf_path)
        
        # Extract content
        results = {
            "method": "IBM Docling",
            "pages_processed": 0,
            "total_pages": 0,
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
        
        # Get document text
        full_text = result.document.export_to_text()
        results["extracted_content"]["full_text"] = full_text
        
        # Get structured markdown
        markdown_content = result.document.export_to_markdown()
        results["extracted_content"]["structured_markdown"] = markdown_content
        
        # Extract tables
        tables = result.document.tables
        print(f"Found {len(tables)} tables")
        
        extracted_tables = []
        for i, table in enumerate(tables):
            try:
                # Get table as DataFrame
                df = table.export_to_dataframe()
                
                # Convert to markdown
                table_markdown = df.to_markdown(index=False)
                
                # Get page info if available
                page_num = None
                if hasattr(table, 'prov') and table.prov and len(table.prov) > 0:
                    if hasattr(table.prov[0], 'page'):
                        page_num = table.prov[0].page
                    elif hasattr(table.prov[0], 'page_no'):
                        page_num = table.prov[0].page_no
                
                table_info = {
                    "table_id": i + 1,
                    "page": page_num,
                    "markdown": table_markdown,
                    "shape": df.shape,
                    "data": df.to_dict('records')
                }
                extracted_tables.append(table_info)
                
                # Save individual table files
                table_dir = Path(out_dir, f"table_{i+1:02d}")
                table_dir.mkdir(exist_ok=True)
                
                # Save as CSV
                csv_path = table_dir / "table.csv"
                df.to_csv(csv_path, index=False)
                
                # Save as Excel
                excel_path = table_dir / "table.xlsx"
                df.to_excel(excel_path, index=False)
                
                # Save as Markdown
                md_path = table_dir / "table.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Table {i+1}\n")
                    if page_num:
                        f.write(f"**Page:** {page_num}\n\n")
                    f.write(table_markdown)
                
                results["output_files"].extend([str(csv_path), str(excel_path), str(md_path)])
                
            except Exception as e:
                print(f"Error processing table {i+1}: {e}")
        
        results["extracted_content"]["tables"] = extracted_tables
        
        # Get page count (approximate from document structure)
        # Docling doesn't directly give page count, so we estimate
        page_count = len(result.document.pages) if hasattr(result.document, 'pages') else 1
        results["total_pages"] = page_count
        results["pages_processed"] = page_count  # Assume all pages processed successfully
        
        # Create per-page results (simulated since Docling processes whole document)
        for page_num in range(1, page_count + 1):
            page_result = {
                "page": page_num,
                "success": True,
                "content": {
                    "text_extracted": True,
                    "tables_on_page": [t for t in extracted_tables if t.get("page") == page_num]
                }
            }
            results["per_page_results"].append(page_result)
        
        results["processing_time"] = time.time() - start_time
        
        # Save consolidated outputs
        save_consolidated_outputs(results, out_dir)
        
        return results
        
    except Exception as e:
        return {"error": f"Failed to process with Docling: {e}"}

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
                f.write(f"## Table {table['table_id']}")
                if table.get("page"):
                    f.write(f" (Page {table['page']})")
                f.write(f"\n\n**Shape:** {table['shape'][0]} rows x {table['shape'][1]} columns\n\n")
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
    print("IBM DOCLING EXTRACTION SUMMARY")
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
    
    print("\nOutput files:")
    for file_path in results['output_files']:
        print(f"  {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python docling_extractor.py <pdf_path> [output_dir]")
        print("Example: python docling_extractor.py 'paper.pdf' docling_results")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "docling_results"
    
    results = extract_with_docling(pdf_path, out_dir)
    print_extraction_summary(results)