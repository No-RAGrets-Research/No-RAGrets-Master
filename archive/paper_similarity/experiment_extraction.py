from pathlib import Path
from docling.document_converter import DocumentConverter
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_all_papers_to_json():
    """Extract structured data from all papers using Docling"""
    
    # Find all files
    literature_folder = Path("UCSC NLP Project - CB Literature")
    pdf_files = list(literature_folder.glob("*.pdf"))
    docx_files = list(literature_folder.glob("*.docx"))
    all_files = pdf_files + docx_files
    
    print(f"Found {len(pdf_files)} PDFs and {len(docx_files)} DOCX files")
    print("Extracting structured data from all papers using Docling...")
    
    # Initialize Docling converter
    converter = DocumentConverter()
    
    # Create output directory for individual JSON files
    output_dir = Path("paper_json_data")
    output_dir.mkdir(exist_ok=True)
    
    papers_data = {}
    successful_count = 0
    
    for i, file_path in enumerate(all_files):
        print(f"\n{i+1}/{len(all_files)} Processing: {file_path.name}")
        
        try:
            # Convert document using Docling
            result = converter.convert(file_path)
            
            # Get text content and create simple chunks
            document_text = result.document.export_to_markdown()
            
            # Create chunks by splitting on double newlines (paragraphs)
            raw_chunks = document_text.split('\n\n')
            chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip() and len(chunk.strip()) > 20]
            
            paper_data = {
                'filename': file_path.name,
                'markdown': document_text,
                'chunks': chunks,
                'markdown_length': len(document_text),
                'chunks_count': len(chunks),
                'extraction_method': 'docling'
            }
            
            # Save individual paper to its own JSON file
            safe_filename = file_path.stem.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('&', 'and')
            individual_json_file = output_dir / f"{safe_filename}.json"
            
            with open(individual_json_file, 'w', encoding='utf-8') as f:
                json.dump(paper_data, f, indent=2, ensure_ascii=False)
            
            papers_data[file_path.name] = paper_data
            successful_count += 1
            
            print(f"   ✓ Extracted {len(chunks)} chunks, {len(document_text)} chars")
            print(f"   ✓ Saved to {individual_json_file}")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            error_data = {
                'filename': file_path.name,
                'error': str(e)
            }
            papers_data[file_path.name] = error_data
            
            # Still save error info to individual file
            safe_filename = file_path.stem.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('&', 'and')
            individual_json_file = output_dir / f"{safe_filename}_ERROR.json"
            
            with open(individual_json_file, 'w') as f:
                json.dump(error_data, f, indent=2)
    
    # Also save summary to main JSON file
    summary_file = "papers_extraction_summary.json"
    summary_data = {
        'total_files': len(all_files),
        'successful': successful_count,
        'failed': len(all_files) - successful_count,
        'individual_files_location': str(output_dir),
        'file_list': list(papers_data.keys()),
        'extraction_method': 'docling'
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\n✓ Saved individual JSON files to {output_dir}/ folder")
    print(f"✓ Saved extraction summary to {summary_file}")
    print(f"✓ Successfully processed {len([p for p in papers_data.values() if 'error' not in p])} papers")
    
    return papers_data

if __name__ == "__main__":
    # Extract all papers to structured JSON
    papers_data = extract_all_papers_to_json()
    
    # Show summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    
    successful = [name for name, data in papers_data.items() if 'error' not in data]
    failed = [name for name, data in papers_data.items() if 'error' in data]
    
    print(f"Successful: {len(successful)} papers")
    print(f"Failed: {len(failed)} papers")
    
    if successful:
        print(f"\nExample chunks from first paper ({successful[0]}):")
        first_paper = papers_data[successful[0]]
        for i, chunk in enumerate(first_paper['chunks'][:3]):
            chunk_preview = str(chunk)[:100] + "..." if len(str(chunk)) > 100 else str(chunk)
            print(f"  Chunk {i+1}: {chunk_preview}")
    
    print(f"\nNext step: Use granite_analyzer.py to analyze the JSON data!")