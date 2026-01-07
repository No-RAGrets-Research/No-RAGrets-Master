#!/usr/bin/env python3
"""
Docling Experiment Script

This script tests Docling, an open-source document converter,
for extracting structured content from PDF documents.

Docling provides:
- Open-source document conversion
- Structure-aware parsing (headings, tables, figures)
- Multiple output formats (JSON, Markdown, etc.)
- No API costs - runs locally

Author: Generated for VLM experiments
Date: October 2024
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import time

# Add the src directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
except ImportError as e:
    print(f"Error importing Docling: {e}")
    print("Please install Docling: pip install docling")
    sys.exit(1)

def test_docling_conversion(pdf_path):
    """
    Test Docling document conversion
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        dict: Converted document data
    """
    
    print(f"Processing with Docling...")
    print(f"PDF path: {pdf_path}")
    
    # Configure pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False  # Disable OCR for faster processing
    pipeline_options.do_table_structure = True  # Enable table structure detection
    
    # Initialize converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: pipeline_options,
        }
    )
    
    # Convert document
    start_time = time.time()
    result = converter.convert(pdf_path)
    end_time = time.time()
    
    print(f"Conversion completed in {end_time - start_time:.2f} seconds")
    
    # Extract content
    document = result.document
    
    # Convert to dict for JSON serialization
    doc_dict = {
        "main_text": document.main_text,
        "metadata": {
            "page_count": len(document.pages),
            "title": getattr(document, 'title', 'Unknown'),
            "creation_time": datetime.now().isoformat()
        },
        "pages": []
    }
    
    # Process pages
    for i, page in enumerate(document.pages):
        page_dict = {
            "page_number": i + 1,
            "text": page.text if hasattr(page, 'text') else "",
            "elements": []
        }
        
        # Extract page elements if available
        if hasattr(page, 'elements'):
            for element in page.elements:
                element_dict = {
                    "type": str(type(element).__name__),
                    "text": getattr(element, 'text', ''),
                    "bbox": getattr(element, 'bbox', None)
                }
                page_dict["elements"].append(element_dict)
        
        doc_dict["pages"].append(page_dict)
    
    return doc_dict

def analyze_docling_response(response_data, output_file):
    """
    Analyze the Docling response and generate metrics
    
    Args:
        response_data (dict): Conversion result
        output_file (str): Path to save analysis
    """
    
    # Extract main text
    main_text = response_data.get('main_text', '')
    
    # Basic metrics
    char_count = len(main_text)
    word_count = len(main_text.split()) if main_text else 0
    page_count = response_data.get('metadata', {}).get('page_count', 0)
    
    # Count elements across all pages
    total_elements = 0
    element_types = {}
    
    for page in response_data.get('pages', []):
        elements = page.get('elements', [])
        total_elements += len(elements)
        
        for element in elements:
            element_type = element.get('type', 'Unknown')
            element_types[element_type] = element_types.get(element_type, 0) + 1
    
    # Estimate chunks (assuming average of 400 chars per chunk)
    estimated_chunks = char_count // 400 if char_count > 0 else 0
    
    analysis = f"""# Docling Conversion Analysis Report

## Overview
- **Total Characters**: {char_count:,}
- **Total Words**: {word_count:,}
- **Total Pages**: {page_count}
- **Estimated Chunks**: {estimated_chunks}
- **Total Elements**: {total_elements}

## Element Types Found
"""
    
    for element_type, count in sorted(element_types.items()):
        analysis += f"- **{element_type}**: {count}\n"
    
    analysis += f"""
## Key Features
- Open-source document conversion
- Structure-aware parsing
- Local processing (no API costs)
- Multiple output formats

## Cost Information
- Free and open-source
- No API limits or costs
- Runs entirely locally

## Sample Content Preview
```
{main_text[:500] if main_text else 'No main text extracted'}...
```

## Document Structure
- **Pages Processed**: {page_count}
- **Elements Extracted**: {total_elements}
- **Average Elements per Page**: {total_elements / page_count if page_count > 0 else 0:.1f}
"""
    
    with open(output_file, 'w') as f:
        f.write(analysis)
    
    print(f"Analysis saved to: {output_file}")
    print(f"Content length: {char_count:,} characters")
    print(f"Pages processed: {page_count}")
    print(f"Total elements: {total_elements}")

def main():
    """Main function to run the Docling experiment"""
    
    # Define paths
    script_dir = Path(__file__).parent
    pdf_path = script_dir / "papers" / "Baldo et al. 2024.pdf"
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name = pdf_path.stem
    
    output_json = script_dir / f"docling_output_{pdf_name}_{timestamp}.json"
    analysis_file = script_dir / f"docling_output_{pdf_name}_{timestamp}_analysis.md"
    
    try:
        print(f"Starting Docling experiment...")
        print(f"Processing: {pdf_path}")
        
        # Test Docling conversion
        response_data = test_docling_conversion(str(pdf_path))
        
        # Save response
        with open(output_json, 'w') as f:
            json.dump(response_data, f, indent=2)
        
        print(f"Response saved to: {output_json}")
        
        # Analyze response
        analyze_docling_response(response_data, analysis_file)
        
        print("\nDocling experiment completed successfully!")
        print("Check the generated files for detailed results.")
        
    except Exception as e:
        print(f"Error during experiment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()