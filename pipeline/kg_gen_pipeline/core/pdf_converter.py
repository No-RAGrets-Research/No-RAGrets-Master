#!/usr/bin/env python3
"""
convert_pdfs_to_docling.py
--------------------------
Convert all PDFs in the papers directory to Docling JSON format.

This script uses the Docling library to parse PDFs and extract structured content.
Run this before the batch processing pipeline.

Usage:
    python convert_pdfs_to_docling.py
    python convert_pdfs_to_docling.py --papers-dir ../papers --output-dir .
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
except ImportError:
    print("ERROR: Docling library not installed.")
    print("Install with: pip install docling")
    sys.exit(1)


class DoclingConverter:
    def __init__(self, papers_dir: str = "../papers", output_dir: str = "output/docling_json"):
        self.papers_dir = Path(papers_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Papers directory: {self.papers_dir}")
        print(f"Output directory: {self.output_dir}")
        
        # Initialize Docling converter with basic settings
        # Use default configuration to avoid backend attribute issues
        self.converter = DocumentConverter()
    
    def find_pdf_files(self):
        """Find all PDF files in the papers directory."""
        if not self.papers_dir.exists():
            raise FileNotFoundError(f"Papers directory not found: {self.papers_dir}")
        
        pdf_files = list(self.papers_dir.glob("**/*.pdf"))
        print(f"Found {len(pdf_files)} PDF files:")
        for pdf in pdf_files:
            print(f"  - {pdf.relative_to(self.papers_dir)}")
        
        return pdf_files
    
    def convert_pdf(self, pdf_path: Path) -> Path:
        """Convert a single PDF to Docling JSON."""
        output_path = self.output_dir / f"{pdf_path.stem}.json"
        
        if output_path.exists():
            print(f"Skipping {pdf_path.name} (JSON already exists)")
            return output_path
        
        print(f"Converting {pdf_path.name} to Docling JSON...")
        
        try:
            # Convert the PDF
            result = self.converter.convert(str(pdf_path))
            
            # Get the document
            doc = result.document
            
            # Export to JSON format
            json_data = doc.export_to_dict()
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"Successfully converted: {pdf_path.name} -> {output_path.name}")
            return output_path
            
        except Exception as e:
            print(f"Error converting {pdf_path.name}: {e}")
            return None
    
    def convert_all_pdfs(self):
        """Convert all PDFs in the papers directory."""
        pdf_files = self.find_pdf_files()
        
        if not pdf_files:
            print("No PDF files found in papers directory.")
            return
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "papers_directory": str(self.papers_dir),
            "output_directory": str(self.output_dir),
            "total_pdfs": len(pdf_files),
            "successful": [],
            "failed": []
        }
        
        for pdf_path in pdf_files:
            output_path = self.convert_pdf(pdf_path)
            
            if output_path and output_path.exists():
                results["successful"].append({
                    "pdf": str(pdf_path),
                    "json": str(output_path),
                    "size_mb": round(pdf_path.stat().st_size / 1024 / 1024, 2)
                })
            else:
                results["failed"].append(str(pdf_path))
        
        # Save conversion report
        report_path = self.output_dir / f"docling_conversion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*50}")
        print("CONVERSION SUMMARY")
        print(f"{'='*50}")
        print(f"Total PDFs: {results['total_pdfs']}")
        print(f"Successfully converted: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Report saved: {report_path.name}")
        
        if results['failed']:
            print("\nFailed conversions:")
            for failed_pdf in results['failed']:
                print(f"  - {Path(failed_pdf).name}")


def main():
    parser = argparse.ArgumentParser(description="Convert PDFs to Docling JSON format")
    parser.add_argument("--papers-dir", default="../papers",
                       help="Directory containing PDF papers (default: ../papers)")
    parser.add_argument("--output-dir", default="output/docling_json",
                       help="Directory to save JSON files (default: output/docling_json)")
    
    args = parser.parse_args()
    
    print("PDF to Docling JSON Converter")
    print("="*35)
    
    try:
        converter = DoclingConverter(
            papers_dir=args.papers_dir,
            output_dir=args.output_dir
        )
        
        converter.convert_all_pdfs()
        
        print("\nConversion complete!")
        print("Next step: Run 'python batch_process_papers.py' to process the JSON files")
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()