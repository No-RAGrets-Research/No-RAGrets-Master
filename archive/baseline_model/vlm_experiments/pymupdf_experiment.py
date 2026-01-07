#!/usr/bin/env python3
"""
PyMuPDF Experiment Script

This script tests PyMuPDF (fitz) for baseline PDF text extraction.
PyMuPDF is currently used in the existing pipeline as the foundation
for document processing.

PyMuPDF provides:
- Fast and reliable PDF parsing
- Text extraction with layout preservation
- Image and figure detection
- Free and open-source

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
    from paper_parser.parser import PDFParser
except ImportError as e:
    print(f"Error importing PDFParser: {e}")
    print("Make sure the src/paper_parser module is available")
    sys.exit(1)

def test_pymupdf_extraction(pdf_path):
    """
    Test PyMuPDF extraction using existing parser
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        dict: Extracted document data
    """
    
    print(f"Processing with PyMuPDF (existing parser)...")
    print(f"PDF path: {pdf_path}")
    
    # Initialize parser
    parser = PDFParser()
    
    # Extract content
    start_time = time.time()
    
    try:
        # Use existing parser methods
        text_content = parser.extract_text(str(pdf_path))
        metadata = parser.get_metadata(str(pdf_path))
        
        end_time = time.time()
        print(f"Extraction completed in {end_time - start_time:.2f} seconds")
        
        # Structure the response similar to other experiments
        response_data = {
            "content": text_content,
            "metadata": {
                "file_path": str(pdf_path),
                "extraction_method": "PyMuPDF (fitz)",
                "processing_time": end_time - start_time,
                "timestamp": datetime.now().isoformat(),
                **metadata
            },
            "parser_info": {
                "library": "PyMuPDF",
                "method": "Existing baseline parser",
                "features": [
                    "Text extraction",
                    "Layout preservation", 
                    "Metadata extraction",
                    "Fast processing"
                ]
            }
        }
        
        return response_data
        
    except Exception as e:
        print(f"Error during PyMuPDF extraction: {e}")
        raise

def analyze_pymupdf_response(response_data, output_file):
    """
    Analyze the PyMuPDF response and generate metrics
    
    Args:
        response_data (dict): Extraction result
        output_file (str): Path to save analysis
    """
    
    # Extract content
    content = response_data.get('content', '')
    metadata = response_data.get('metadata', {})
    
    # Basic metrics
    char_count = len(content)
    word_count = len(content.split()) if content else 0
    line_count = len(content.split('\n')) if content else 0
    
    # Processing info
    processing_time = metadata.get('processing_time', 0)
    page_count = metadata.get('page_count', 0)
    
    # Estimate chunks (assuming average of 400 chars per chunk)
    estimated_chunks = char_count // 400 if char_count > 0 else 0
    
    # Content analysis
    figures_mentioned = content.lower().count('figure') if content else 0
    tables_mentioned = content.lower().count('table') if content else 0
    references_mentioned = content.lower().count('reference') if content else 0
    
    analysis = f"""# PyMuPDF (Baseline) Analysis Report

## Overview
- **Total Characters**: {char_count:,}
- **Total Words**: {word_count:,}
- **Total Lines**: {line_count:,}
- **Page Count**: {page_count}
- **Estimated Chunks**: {estimated_chunks}
- **Processing Time**: {processing_time:.2f} seconds

## Content Analysis
- **Figures Mentioned**: {figures_mentioned}
- **Tables Mentioned**: {tables_mentioned}
- **References Mentioned**: {references_mentioned}

## Parser Information
- **Library**: PyMuPDF (fitz)
- **Method**: Existing baseline parser
- **Type**: Local text extraction

## Key Features
- Fast and reliable PDF parsing
- Text extraction with layout preservation
- Metadata extraction
- Currently used in baseline pipeline
- Free and open-source

## Cost Information
- Free and open-source
- No API costs or limits
- Local processing

## Performance Metrics
- **Characters per Second**: {char_count / processing_time if processing_time > 0 else 0:,.0f}
- **Pages per Second**: {page_count / processing_time if processing_time > 0 else 0:.1f}

## Sample Content Preview
```
{content[:500] if content else 'No content extracted'}...
```

## Metadata
```json
{json.dumps(metadata, indent=2)}
```
"""
    
    with open(output_file, 'w') as f:
        f.write(analysis)
    
    print(f"Analysis saved to: {output_file}")
    print(f"Content length: {char_count:,} characters")
    print(f"Processing speed: {char_count / processing_time if processing_time > 0 else 0:,.0f} chars/sec")

def main():
    """Main function to run the PyMuPDF experiment"""
    
    # Define paths
    script_dir = Path(__file__).parent
    pdf_path = script_dir / "papers" / "Baldo et al. 2024.pdf"
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name = pdf_path.stem
    
    output_json = script_dir / f"pymupdf_output_{pdf_name}_{timestamp}.json"
    analysis_file = script_dir / f"pymupdf_output_{pdf_name}_{timestamp}_analysis.md"
    
    try:
        print(f"Starting PyMuPDF (baseline) experiment...")
        print(f"Processing: {pdf_path}")
        
        # Test PyMuPDF extraction
        response_data = test_pymupdf_extraction(pdf_path)
        
        # Save response
        with open(output_json, 'w') as f:
            json.dump(response_data, f, indent=2)
        
        print(f"Response saved to: {output_json}")
        
        # Analyze response
        analyze_pymupdf_response(response_data, analysis_file)
        
        print("\nPyMuPDF experiment completed successfully!")
        print("Check the generated files for detailed results.")
        
    except Exception as e:
        print(f"Error during experiment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()