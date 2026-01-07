#!/usr/bin/env python3
"""
master_kg_orchestrator.py
-------------------------
Master orchestrator for comprehensive knowledge graph extraction from scientific papers.

Coordinates text-based and visual-based extraction pipelines with intelligent figure detection,
graceful error handling, and separate output files for clean provenance tracking.

Workflow:
1. Convert PDF to Docling JSON (if needed)
2. Extract text chunks and process with KG extraction
3. Detect figures and conditionally run visual extraction
4. Generate separate KG-format outputs for text and visual content
5. Provide loading instructions for KG database

Usage:
    python master_kg_orchestrator.py paper.pdf
    python master_kg_orchestrator.py --docling-json existing.json --pdf paper.pdf
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import subprocess
import shutil

# Import our pipeline components
from .figure_detection import FigureDetector
from .visual_kg_extractor import VisualTripleExtractor
from .visual_kg_formatter import VisualKGFormatter
from .text_kg_extractor import ChunkKGExtractor
from .pdf_converter import DoclingConverter


class MasterKGOrchestrator:
    """Orchestrates complete text + visual knowledge graph extraction."""
    
    def __init__(self, 
                 output_dir: str = "output",
                 skip_existing: bool = True,
                 verbose: bool = True,
                 enable_cleanup: bool = True):
        """
        Initialize the master orchestrator.
        
        Args:
            output_dir: Base directory for all outputs
            skip_existing: Skip processing if outputs already exist
            verbose: Enable detailed logging
            enable_cleanup: Clean up intermediate files and memory after processing
        """
        self.output_dir = Path(output_dir)
        self.skip_existing = skip_existing
        self.verbose = verbose
        self.enable_cleanup = enable_cleanup
        
        # Create output subdirectories
        self.docling_dir = self.output_dir / "docling_json"
        self.chunks_dir = self.output_dir / "text_chunks"
        self.raw_visual_triples_dir = self.output_dir / "raw_visual_triples"
        self.visual_triples_dir = self.output_dir / "visual_triples"
        self.text_triples_dir = self.output_dir / "text_triples"
        self.reports_dir = self.output_dir / "reports"
        
        for dir_path in [self.docling_dir, self.chunks_dir, self.raw_visual_triples_dir, self.visual_triples_dir, self.text_triples_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.figure_detector = FigureDetector()
        self.visual_extractor = None  # Lazy load to save memory
        self.visual_formatter = VisualKGFormatter()
        
        # Processing stats
        self.stats = {
            'start_time': None,
            'end_time': None,
            'pdf_processed': False,
            'docling_created': False,
            'text_extraction_success': False,
            'figure_detection_run': False,
            'visual_extraction_attempted': False,
            'visual_extraction_success': False,
            'total_text_entities': 0,
            'total_text_relations': 0,
            'total_visual_entities': 0,
            'total_visual_relations': 0,
            'errors': []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command: list, description: str) -> Tuple[bool, str]:
        """Run a subprocess command and return success status and output."""
        self.log(f"Running: {description}")
        try:
            # Use simpler approach with real-time output
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=0,  # Unbuffered
                universal_newlines=True,
                cwd=Path.cwd()
            )
            
            output_lines = []
            
            # Read output line by line in real-time
            while True:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip(), flush=True)  # Print immediately with flush
                    output_lines.append(line)
                else:
                    # No more output, check if process is done
                    if process.poll() is not None:
                        break
                    # Small sleep to prevent busy waiting
                    import time
                    time.sleep(0.01)
            
            # Wait for process to complete and get return code
            return_code = process.wait()
            full_output = ''.join(output_lines)
            
            if return_code == 0:
                return True, full_output
            else:
                error_msg = f"Command failed with code {return_code}"
                self.log(error_msg, "ERROR")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.log(error_msg, "ERROR")
            return False, error_msg
    
    def ensure_docling_json(self, pdf_path: str, docling_json_path: Optional[str] = None) -> Optional[str]:
        """Ensure Docling JSON exists, creating it if necessary."""
        
        if docling_json_path and Path(docling_json_path).exists():
            self.log(f"Using existing Docling JSON: {docling_json_path}")
            return docling_json_path
        
        # Generate Docling JSON path
        pdf_name = Path(pdf_path).stem
        generated_docling = self.docling_dir / f"{pdf_name}.json"
        
        if self.skip_existing and generated_docling.exists():
            self.log(f"Using existing Docling JSON: {generated_docling}")
            return str(generated_docling)
        
        # Convert PDF to Docling JSON using direct import
        self.log(f"Converting PDF to Docling JSON: {pdf_path}")
        try:
            # Create a DoclingConverter configured for our output directory
            converter = DoclingConverter(
                papers_dir=str(Path(pdf_path).parent),
                output_dir=str(self.docling_dir)
            )
            
            # Convert the single PDF file
            result_path = converter.convert_pdf(Path(pdf_path))
            
            if result_path and result_path.exists():
                self.stats['docling_created'] = True
                self.log(f"Docling JSON created: {result_path}")
                return str(result_path)
            else:
                self.stats['errors'].append(f"Docling conversion failed: No output file created")
                return None
                
        except Exception as e:
            self.stats['errors'].append(f"Docling conversion failed: {str(e)}")
            return None
    
    def run_text_extraction(self, docling_json_path: str, timestamp: str) -> Optional[str]:
        """Run text chunking and KG extraction pipeline."""
        
        pdf_name = Path(docling_json_path).stem
        
        # Check if text chunking output exists
        chunks_file = self.chunks_dir / f"{pdf_name}.texts_chunks.jsonl"
        
        if not (self.skip_existing and chunks_file.exists()):
            # Run text chunking
            self.log("Running text chunking...")
            success, output = self.run_command([
                "python", "kg_gen_pipeline/core/text_chunker.py", docling_json_path, str(self.chunks_dir)
            ], "Text chunking")
            
            if not success:
                self.stats['errors'].append(f"Text chunking failed: {output}")
                return None
        
        if not chunks_file.exists():
            self.stats['errors'].append(f"Text chunks file not found: {chunks_file}")
            return None
        
        # Run KG extraction on text chunks
        self.log("Running text-based KG extraction...")
        try:
            extractor = ChunkKGExtractor()
            
            # Custom save method to use our output directories
            base = Path(chunks_file).stem.replace(".texts_chunks", "")
            chunks = extractor.load_chunks(str(chunks_file))
            results = extractor.process_all(chunks)
            summary = extractor.aggregate(results)
            
            # Use our output directories instead of defaults
            paths = extractor.save(
                results, 
                summary, 
                base, 
                kg_output_dir=str(self.text_triples_dir),
                report_output_dir=str(self.reports_dir),
                timestamp=timestamp
            )
            
            self.stats['text_extraction_success'] = True
            
            # Find the generated text triples file with matching timestamp  
            expected_text_file = self.text_triples_dir / f"{pdf_name}_kg_results_{timestamp}.json"
            
            if expected_text_file.exists():
                self.log(f"Text triples extraction completed: {expected_text_file.name}")
                latest_file = expected_text_file
                
                # Extract stats from results
                try:
                    with open(latest_file, 'r') as f:
                        file_results = json.load(f)
                    file_summary = file_results.get('summary', {})
                    self.stats['total_text_entities'] = file_summary.get('entities', 0)
                    self.stats['total_text_relations'] = file_summary.get('relations', 0)
                except Exception as e:
                    self.log(f"Could not read text KG stats: {e}", "WARNING")
                
                return str(latest_file)
            else:
                self.stats['errors'].append(f"Text triples file not found: {expected_text_file}")
                return None
        
        except Exception as e:
            self.stats['errors'].append(f"Text KG extraction failed: {str(e)}")
            return None
    
    def run_visual_extraction(self, docling_json_path: str, pdf_path: str, timestamp: str) -> Optional[str]:
        """Run visual extraction pipeline if figures are detected."""
        
        # Step 1: Figure detection
        self.log("Running figure detection...")
        self.stats['figure_detection_run'] = True
        
        detection_result = self.figure_detector.analyze_document(docling_json_path)
        
        if not detection_result['should_extract']:
            self.log(f"Skipping visual extraction: {', '.join(detection_result['skip_reasons'])}")
            return None
        
        self.log(f"Figure detection: {detection_result['figure_count']} extractable figures found")
        
        # Step 2: Visual extraction
        self.log("Running visual triple extraction...")
        self.stats['visual_extraction_attempted'] = True
        
        try:
            # Lazy load visual extractor to save memory
            if self.visual_extractor is None:
                self.visual_extractor = VisualTripleExtractor(cleanup_images=self.enable_cleanup)
                if not self.visual_extractor.load_model():
                    raise Exception("Failed to load visual extraction model")
            
            # Generate output path in raw_visual_triples directory
            pdf_name = Path(pdf_path).stem
            visual_output = self.raw_visual_triples_dir / f"{pdf_name}_visual_triples.json"
            
            # Run visual extraction
            success = self.visual_extractor.process_paper(
                docling_json_path, 
                pdf_path, 
                str(visual_output)
            )
            
            if success and visual_output.exists():
                self.stats['visual_extraction_success'] = True
                self.log(f"Visual extraction completed: {visual_output.name}")
                
                # Step 3: Format for KG loading and save to final visual_triples directory with timestamp
                kg_format_output = self.visual_triples_dir / f"{pdf_name}_visual_kg_format_{timestamp}.json"
                self.visual_formatter.process_visual_output(str(visual_output), str(kg_format_output))
                
                # Extract stats
                try:
                    with open(kg_format_output, 'r') as f:
                        formatted_results = json.load(f)
                    summary = formatted_results.get('summary', {})
                    self.stats['total_visual_entities'] = summary.get('entities', 0)
                    self.stats['total_visual_relations'] = summary.get('relations', 0)
                except Exception as e:
                    self.log(f"Could not read visual KG stats: {e}", "WARNING")
                
                return kg_format_output
            else:
                raise Exception("Visual extraction process failed")
                
        except Exception as e:
            error_msg = f"Visual extraction failed: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            return None
    
    def cleanup_intermediate_files(self, pdf_path: str):
        """Clean up intermediate files after successful processing."""
        if not self.enable_cleanup:
            return
            
        try:
            pdf_name = Path(pdf_path).stem
            
            # Clean up raw visual triples (keep final KG format in visual_triples)
            raw_visual_file = self.raw_visual_triples_dir / f"{pdf_name}_visual_triples.json"
            if raw_visual_file.exists():
                raw_visual_file.unlink()
                self.log(f"Cleaned up raw visual output: {raw_visual_file.name}")
            
            # Clean up any temporary image files (if any were created)
            for img_ext in [".png", ".jpg", ".jpeg"]:
                pattern = f"{pdf_name}_*{img_ext}"
                for img_file in self.raw_visual_triples_dir.glob(pattern):
                    img_file.unlink()
                    self.log(f"Cleaned up image file: {img_file.name}")
                    
        except Exception as e:
            self.log(f"Intermediate cleanup warning: {e}", "WARNING")

    def cleanup_resources(self):
        """Clean up GPU resources."""
        if self.visual_extractor:
            try:
                # Force garbage collection and GPU memory cleanup
                import torch
                import gc
                if hasattr(self.visual_extractor, 'model') and self.visual_extractor.model:
                    del self.visual_extractor.model
                if hasattr(self.visual_extractor, 'processor') and self.visual_extractor.processor:
                    del self.visual_extractor.processor
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                self.log("GPU resources cleaned up")
            except Exception as e:
                self.log(f"Resource cleanup warning: {e}", "WARNING")
    
    def generate_report(self, pdf_path: str, text_kg_file: Optional[str], visual_kg_file: Optional[str]) -> str:
        """Generate a processing report."""
        
        report = {
            'processing_summary': {
                'pdf_file': pdf_path,
                'start_time': self.stats['start_time'],
                'end_time': self.stats['end_time'],
                'total_duration': (self.stats['end_time'] - self.stats['start_time']).total_seconds() if self.stats['end_time'] and self.stats['start_time'] else 0,
                'success': len(self.stats['errors']) == 0
            },
            'text_extraction': {
                'success': self.stats['text_extraction_success'],
                'entities': self.stats['total_text_entities'],
                'relations': self.stats['total_text_relations'],
                'output_file': text_kg_file
            },
            'visual_extraction': {
                'attempted': self.stats['visual_extraction_attempted'],
                'success': self.stats['visual_extraction_success'],
                'entities': self.stats['total_visual_entities'],
                'relations': self.stats['total_visual_relations'],
                'output_file': visual_kg_file
            },
            'loading_instructions': {
                'text_kg': f"python ../knowledge_graph/kg_data_loader.py {text_kg_file}" if text_kg_file else None,
                'visual_kg': f"python ../knowledge_graph/kg_data_loader.py {visual_kg_file}" if visual_kg_file else None
            },
            'errors': self.stats['errors']
        }
        
        # Save report
        pdf_name = Path(pdf_path).stem
        report_file = self.reports_dir / f"{pdf_name}_processing_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(report_file)
    
    def print_summary(self, pdf_path: str, text_kg_file: Optional[str], visual_kg_file: Optional[str]):
        """Print a processing summary."""
        
        print(f"\n" + "=" * 80)
        print(f"MASTER KG ORCHESTRATOR - PROCESSING COMPLETE")
        print(f"=" * 80)
        print(f"PDF: {Path(pdf_path).name}")
        print(f"Duration: {(self.stats['end_time'] - self.stats['start_time']).total_seconds():.1f}s")
        print()
        
        # Text extraction summary
        print(f"TEXT EXTRACTION:")
        if self.stats['text_extraction_success']:
            print(f"  SUCCESS: {self.stats['total_text_entities']} entities, {self.stats['total_text_relations']} relations")
            print(f"  Output: {Path(text_kg_file).name if text_kg_file else 'None'}")
        else:
            print(f"  FAILED")
        
        # Visual extraction summary
        print(f"\nVISUAL EXTRACTION:")
        if not self.stats['visual_extraction_attempted']:
            print(f"  SKIPPED (no extractable figures detected)")
        elif self.stats['visual_extraction_success']:
            print(f"  SUCCESS: {self.stats['total_visual_entities']} entities, {self.stats['total_visual_relations']} relations")
            print(f"  Output: {Path(visual_kg_file).name if visual_kg_file else 'None'}")
        else:
            print(f"  FAILED")
        
        # Loading instructions
        print(f"\nKG DATABASE LOADING:")
        if text_kg_file:
            print(f"  python ../knowledge_graph/kg_data_loader.py {text_kg_file}")
        if visual_kg_file:
            print(f"  python ../knowledge_graph/kg_data_loader.py {visual_kg_file}")
        
        # Errors
        if self.stats['errors']:
            print(f"\nERRORS ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  - {error}")
        
        print(f"=" * 80)
    
    def process_paper(self, pdf_path: str, docling_json_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single paper through the complete pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            docling_json_path: Optional path to existing Docling JSON
            
        Returns:
            Processing results dictionary
        """
        self.stats['start_time'] = datetime.now()
        # Generate consistent timestamp for this processing run
        run_timestamp = self.stats['start_time'].strftime("%Y%m%d_%H%M%S")
        self.log(f"Starting processing: {Path(pdf_path).name} (Run: {run_timestamp})")
        
        try:
            # Step 1: Ensure Docling JSON exists
            docling_json = self.ensure_docling_json(pdf_path, docling_json_path)
            if not docling_json:
                raise Exception("Failed to create or find Docling JSON")
            
            # Step 2: Text extraction pipeline
            text_kg_file = self.run_text_extraction(docling_json, run_timestamp)
            
            # Step 3: Visual extraction pipeline (conditional)
            visual_kg_file = self.run_visual_extraction(docling_json, pdf_path, run_timestamp)
            
            # Step 4: Cleanup resources and intermediate files
            self.cleanup_resources()
            self.cleanup_intermediate_files(pdf_path)
            
            # Step 5: Generate report
            self.stats['end_time'] = datetime.now()
            report_file = self.generate_report(pdf_path, text_kg_file, visual_kg_file)
            
            # Step 6: Print summary
            self.print_summary(pdf_path, text_kg_file, visual_kg_file)
            
            return {
                'success': len(self.stats['errors']) == 0,
                'text_kg_file': text_kg_file,
                'visual_kg_file': visual_kg_file,
                'report_file': report_file,
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            self.stats['end_time'] = datetime.now()
            error_msg = f"Pipeline failed: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            
            self.cleanup_resources()
            
            return {
                'success': False,
                'error': error_msg,
                'stats': self.stats.copy()
            }


def discover_papers(papers_dir: str, output_dir: str) -> Dict[str, Dict[str, str]]:
    """
    Discover PDF papers and check for existing outputs.
    
    Returns:
        Dict mapping paper names to their paths and status:
        {
            'paper1': {
                'pdf_path': '/path/to/paper1.pdf',
                'output_path': '/path/to/output/paper1',
                'has_existing': True/False
            }
        }
    """
    papers_dir = Path(papers_dir)
    output_dir = Path(output_dir)
    
    if not papers_dir.exists():
        print(f"ERROR: Papers directory not found: {papers_dir}")
        return {}
    
    discovered = {}
    
    # Find all PDF files
    for pdf_file in papers_dir.glob("*.pdf"):
        paper_name = pdf_file.stem
        
        # Check if key output files exist (in the structure created by MasterKGOrchestrator)
        visual_triples_dir = output_dir / "visual_triples"
        text_triples_dir = output_dir / "text_triples"
        
        # Use glob patterns to find timestamped output files
        visual_pattern = f"{paper_name}_visual_kg_format_*.json"
        text_pattern = f"{paper_name}_kg_results_*.json"
        
        visual_files = list(visual_triples_dir.glob(visual_pattern))
        text_files = list(text_triples_dir.glob(text_pattern))
        
        # Paper is considered processed if text triples exist (visual is conditional on extractable figures)
        has_existing = len(text_files) > 0
        
        discovered[paper_name] = {
            'pdf_path': str(pdf_file),
            'text_triples_path': str(text_files[0]) if text_files else str(text_triples_dir / f"{paper_name}_kg_results_TIMESTAMP.json"),
            'visual_triples_path': str(visual_files[0]) if visual_files else str(visual_triples_dir / f"{paper_name}_visual_kg_format_TIMESTAMP.json"),
            'has_existing': has_existing
        }
    
    return discovered


def run_batch_processing(papers_dir: str, output_dir: str, force: bool = False, 
                        enable_cleanup: bool = True, dry_run: bool = False) -> bool:
    """
    Run batch processing on all papers in a directory.
    
    Args:
        papers_dir: Directory containing PDF files
        output_dir: Base output directory
        force: If True, reprocess papers even if outputs exist
        enable_cleanup: If True, clean up intermediate files
        dry_run: If True, only show what would be processed
        
    Returns:
        True if all papers processed successfully (or dry run), False otherwise
    """
    print(f"Discovering papers in: {papers_dir}")
    
    discovered = discover_papers(papers_dir, output_dir)
    
    if not discovered:
        print(f"No PDF files found in {papers_dir}")
        return False
    
    print(f"Found {len(discovered)} papers:")
    
    to_process = []
    for paper_name, info in discovered.items():
        status = "EXISTS" if info['has_existing'] else "NEW"
        if info['has_existing'] and not force:
            action = "SKIP"
        else:
            action = "PROCESS"
            to_process.append((paper_name, info))
        
        print(f"  {paper_name}: {status} -> {action}")
    
    if dry_run:
        print(f"\nDRY RUN: Would process {len(to_process)} papers")
        for paper_name, _ in to_process:
            print(f"  - {paper_name}")
        return True
    
    if not to_process:
        print("All papers already processed. Use --force to reprocess.")
        return True
    
    print(f"\nProcessing {len(to_process)} papers...")
    
    successful = 0
    failed = 0
    
    for i, (paper_name, info) in enumerate(to_process, 1):
        print(f"\n[{i}/{len(to_process)}] Processing: {paper_name}")
        print(f"   PDF: {info['pdf_path']}")
        print(f"   Text triples: {info['text_triples_path']}")
        print(f"   Visual triples: {info['visual_triples_path']}")
        
        # Create orchestrator for this paper
        orchestrator = MasterKGOrchestrator(
            output_dir=output_dir,
            skip_existing=not force,
            verbose=True,
            enable_cleanup=enable_cleanup
        )
        
        # Process the paper
        result = orchestrator.process_paper(info['pdf_path'])
        
        if result['success']:
            successful += 1
            print(f"   SUCCESS: {paper_name}")
        else:
            failed += 1
            print(f"   FAILED: {paper_name}")
            print(f"      Error: {result.get('error', 'Unknown error')}")
    
    print(f"\nBatch Processing Complete:")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {successful}/{len(to_process)} ({100*successful/len(to_process):.1f}%)")
    
    return failed == 0


def main():
    """Command line interface for the master orchestrator."""
    
    # Parse arguments with enhanced batch processing support
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Master KG Orchestrator - Process scientific papers into knowledge graphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single paper
  python master_kg_orchestrator.py paper.pdf
  
  # Process single paper with existing docling JSON
  python master_kg_orchestrator.py paper.pdf --docling-json existing.json
  
  # Process all papers in directory
  python master_kg_orchestrator.py --all --papers-dir ./papers
  
  # Dry run to see what would be processed
  python master_kg_orchestrator.py --all --papers-dir ./papers --dry-run
  
  # Force reprocess all papers (including existing outputs)
  python master_kg_orchestrator.py --all --papers-dir ./papers --force
        """
    )
    
    # Positional argument for single paper mode
    parser.add_argument('pdf_file', nargs='?', help='PDF file to process (required unless --all is used)')
    
    # Batch processing flags
    parser.add_argument('--all', action='store_true', help='Process all PDF files in papers directory')
    parser.add_argument('--papers-dir', default='papers', help='Directory containing PDF files (default: papers)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually running')
    
    # Common options
    parser.add_argument('--docling-json', help='Existing docling JSON file (single paper mode only)')
    parser.add_argument('--output-dir', default='output', help='Output directory (default: output)')
    parser.add_argument('--force', action='store_true', help='Force reprocessing even if outputs exist')
    parser.add_argument('--no-cleanup', action='store_true', help='Keep all intermediate files')
    
    args = parser.parse_args()
    
    # Validate argument combinations
    if args.all and args.pdf_file:
        print("ERROR: Cannot specify both --all and a PDF file")
        sys.exit(1)
    
    if not args.all and not args.pdf_file:
        print("ERROR: Must specify either a PDF file or --all flag")
        sys.exit(1)
    
    if args.docling_json and args.all:
        print("ERROR: --docling-json can only be used in single paper mode")
        sys.exit(1)
    
    # Handle batch processing
    if args.all:
        success = run_batch_processing(
            papers_dir=args.papers_dir,
            output_dir=args.output_dir,
            force=args.force,
            enable_cleanup=not args.no_cleanup,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)
    
    # Handle single paper processing
    pdf_path = args.pdf_file
    
    # Validate single paper inputs
    if not Path(pdf_path).exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    if args.docling_json and not Path(args.docling_json).exists():
        print(f"ERROR: Docling JSON file not found: {args.docling_json}")
        sys.exit(1)
    
    # Run single paper orchestrator
    orchestrator = MasterKGOrchestrator(
        output_dir=args.output_dir,
        skip_existing=not args.force,
        verbose=True,
        enable_cleanup=not args.no_cleanup
    )
    
    result = orchestrator.process_paper(pdf_path, args.docling_json)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()