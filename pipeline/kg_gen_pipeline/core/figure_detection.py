#!/usr/bin/env python3
"""
figure_detection.py
------------------
Lightweight utility to analyze Docling JSON and determine if visual extraction is worthwhile.

Examines figure presence, quality, and content type to make intelligent decisions about
whether to run GPU-intensive visual triple extraction.

Usage:
    from figure_detection import FigureDetector
    detector = FigureDetector()
    result = detector.analyze_document("output/docling_json/paper.json")
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple


class FigureDetector:
    """Analyzes documents to determine if visual extraction is worthwhile."""
    
    def __init__(self, 
                 min_caption_length: int = 20,
                 min_figure_area: float = 1000.0,
                 max_figures_per_document: int = 20):
        """
        Initialize the figure detector with configurable thresholds.
        
        Args:
            min_caption_length: Minimum meaningful caption length
            min_figure_area: Minimum figure area (width * height) to consider
            max_figures_per_document: Maximum figures to process (performance limit)
        """
        self.min_caption_length = min_caption_length
        self.min_figure_area = min_figure_area
        self.max_figures_per_document = max_figures_per_document
        
        # Patterns that indicate scientific/extractable content
        self.scientific_keywords = [
            'diagram', 'chart', 'graph', 'plot', 'tree', 'pathway', 'structure',
            'analysis', 'comparison', 'distribution', 'relationship', 'model',
            'phylogenetic', 'metabolic', 'network', 'flow', 'cycle', 'process',
            'experiment', 'result', 'data', 'measurement', 'observation',
            'classification', 'taxonomy', 'evolution', 'mechanism'
        ]
        
        # Patterns that suggest non-extractable content
        self.skip_keywords = [
            'logo', 'header', 'footer', 'watermark', 'decoration',
            'separator', 'divider', 'border', 'frame'
        ]
    
    def calculate_figure_area(self, bbox: Dict[str, float]) -> float:
        """Calculate the area of a figure from its bounding box."""
        if not bbox or not all(k in bbox for k in ['l', 't', 'r', 'b']):
            return 0.0
        
        width = abs(bbox['r'] - bbox['l'])
        height = abs(bbox['t'] - bbox['b'])
        return width * height
    
    def assess_caption_quality(self, caption: str) -> Tuple[bool, str]:
        """
        Assess if a caption indicates extractable scientific content.
        
        Returns:
            (is_meaningful, reason)
        """
        if not caption or len(caption.strip()) < self.min_caption_length:
            return False, f"Caption too short (< {self.min_caption_length} chars)"
        
        caption_lower = caption.lower()
        
        # Check for scientific keywords
        scientific_score = sum(1 for keyword in self.scientific_keywords 
                             if keyword in caption_lower)
        
        # Check for skip keywords
        skip_score = sum(1 for keyword in self.skip_keywords 
                        if keyword in caption_lower)
        
        if skip_score > 0:
            return False, f"Contains non-scientific keywords: {skip_score}"
        
        if scientific_score >= 1:
            return True, f"Contains scientific keywords: {scientific_score}"
        
        # Check for figure numbering with description
        fig_pattern = r'fig(?:ure)?\s*\d+\.?\s*(.+)'
        match = re.search(fig_pattern, caption_lower)
        if match and len(match.group(1).strip()) > 10:
            return True, "Numbered figure with description"
        
        # Check for descriptive content (multiple sentences or detailed description)
        if len(caption.strip()) > 50 and ('.' in caption or ',' in caption):
            return True, "Detailed descriptive caption"
        
        return False, "Caption lacks scientific indicators"
    
    def analyze_single_figure(self, figure_data: Dict[str, Any], figure_index: int, 
                             figure_captions: Dict[int, str] = None) -> Dict[str, Any]:
        """Analyze a single figure to determine if it's worth extracting."""
        
        # Extract basic information from Docling picture format
        figure_type = figure_data.get('label', 'picture')
        prov = figure_data.get('prov', [])
        
        if not prov:
            return {
                'extractable': False,
                'reason': 'No provenance data',
                'figure_data': None
            }
        
        # Get first provenance entry (Docling format)
        main_prov = prov[0]
        page_no = main_prov.get('page_no', 0)
        bbox = main_prov.get('bbox', {})
        
        # Calculate figure area
        area = self.calculate_figure_area(bbox)
        if area < self.min_figure_area:
            return {
                'extractable': False,
                'reason': f'Figure too small (area: {area:.1f} < {self.min_figure_area})',
                'figure_data': None
            }
        
        # Get caption text - first try figure captions from texts, then embedded captions
        caption = ''
        if figure_captions and page_no in figure_captions:
            caption = figure_captions[page_no]
        else:
            # Fallback to embedded captions
            captions = figure_data.get('captions', [])
            if captions and len(captions) > 0:
                caption = captions[0].get('text', '').strip()
        
        # Assess caption quality
        is_meaningful, caption_reason = self.assess_caption_quality(caption)
        if not is_meaningful:
            return {
                'extractable': False,
                'reason': f'Caption quality: {caption_reason}',
                'figure_data': None
            }
        
        # Create figure summary
        figure_summary = {
            'figure_id': f'page{page_no}_fig{figure_index + 1}',
            'page': page_no,
            'caption': caption,
            'area': area,
            'bbox': bbox,
            'type': figure_type,
            'reason': caption_reason
        }
        
        return {
            'extractable': True,
            'reason': caption_reason,
            'figure_data': figure_summary
        }
    
    def find_figure_captions(self, texts: List[Dict[str, Any]]) -> Dict[int, str]:
        """Find figure captions in the texts section and map them by page."""
        captions_by_page = {}
        
        for text in texts:
            text_content = text.get('text', '').strip()
            if not text_content:
                continue
                
            # Look for figure caption patterns
            fig_match = re.match(r'^FIG\.?\s*(\d+)\.?\s*(.+)', text_content, re.IGNORECASE)
            if fig_match:
                prov = text.get('prov', [])
                if prov:
                    page_no = prov[0].get('page_no', 0)
                    captions_by_page[page_no] = text_content
        
        return captions_by_page

    def analyze_document(self, docling_json_path: str) -> Dict[str, Any]:
        """
        Analyze a Docling JSON document to determine if visual extraction is worthwhile.
        
        Returns:
            {
                'should_extract': bool,
                'figure_count': int,
                'extractable_figures': List[Dict],
                'skip_reasons': List[str],
                'summary': Dict
            }
        """
        
        docling_path = Path(docling_json_path)
        if not docling_path.exists():
            return {
                'should_extract': False,
                'figure_count': 0,
                'extractable_figures': [],
                'skip_reasons': [f'Docling JSON not found: {docling_json_path}'],
                'summary': {'error': 'File not found'}
            }
        
        try:
            with open(docling_path, 'r', encoding='utf-8') as f:
                docling_data = json.load(f)
        except Exception as e:
            return {
                'should_extract': False,
                'figure_count': 0,
                'extractable_figures': [],
                'skip_reasons': [f'Error reading JSON: {str(e)}'],
                'summary': {'error': f'JSON parse error: {str(e)}'}
            }
        
        # Find figures in the document (Docling stores them as 'pictures')
        figures = docling_data.get('pictures', [])
        
        # Find figure captions in texts section
        figure_captions = self.find_figure_captions(docling_data.get('texts', []))
        
        if not figures:
            return {
                'should_extract': False,
                'figure_count': 0,
                'extractable_figures': [],
                'skip_reasons': ['No figures found in document'],
                'summary': {'total_elements': len(docling_data.get('texts', []))}
            }
        
        # Limit number of figures for performance
        if len(figures) > self.max_figures_per_document:
            figures = figures[:self.max_figures_per_document]
            performance_limit_note = f'Limited to first {self.max_figures_per_document} figures'
        else:
            performance_limit_note = None
        
        # Analyze each figure
        extractable_figures = []
        skip_reasons = []
        
        for i, figure in enumerate(figures):
            analysis = self.analyze_single_figure(figure, i, figure_captions)
            
            if analysis['extractable']:
                extractable_figures.append(analysis['figure_data'])
            else:
                skip_reasons.append(f"Figure {i+1}: {analysis['reason']}")
        
        # Make final decision
        should_extract = len(extractable_figures) > 0
        
        # Create summary
        summary = {
            'total_figures': len(figures),
            'extractable_count': len(extractable_figures),
            'skip_count': len(figures) - len(extractable_figures),
            'document_path': str(docling_path),
            'analysis_date': docling_path.stat().st_mtime if docling_path.exists() else None
        }
        
        if performance_limit_note:
            summary['note'] = performance_limit_note
        
        return {
            'should_extract': should_extract,
            'figure_count': len(extractable_figures),
            'extractable_figures': extractable_figures,
            'skip_reasons': skip_reasons,
            'summary': summary
        }
    
    def print_analysis_report(self, analysis: Dict[str, Any], verbose: bool = True):
        """Print a formatted analysis report."""
        
        print(f"\n" + "=" * 60)
        print(f"FIGURE DETECTION ANALYSIS")
        print(f"=" * 60)
        
        summary = analysis['summary']
        print(f"Document: {summary.get('document_path', 'Unknown')}")
        print(f"Total figures found: {summary.get('total_figures', 0)}")
        print(f"Extractable figures: {summary.get('extractable_count', 0)}")
        print(f"Skipped figures: {summary.get('skip_count', 0)}")
        
        print(f"\nRECOMMENDATION: {'RUN VISUAL EXTRACTION' if analysis['should_extract'] else 'SKIP VISUAL EXTRACTION'}")
        
        if analysis['extractable_figures'] and verbose:
            print(f"\nEXTRACTABLE FIGURES:")
            for i, fig in enumerate(analysis['extractable_figures'], 1):
                print(f"  {i}. {fig['figure_id']} (Page {fig['page']})")
                print(f"     Caption: {fig['caption'][:100]}{'...' if len(fig['caption']) > 100 else ''}")
                print(f"     Reason: {fig['reason']}")
                print(f"     Size: {fig['area']:.0f} units²")
        
        if analysis['skip_reasons'] and verbose:
            print(f"\nSKIPPED FIGURES:")
            for reason in analysis['skip_reasons']:
                print(f"  - {reason}")
        
        if 'note' in summary:
            print(f"\nNOTE: {summary['note']}")
        
        print(f"=" * 60)


def main():
    """Command line interface for figure detection."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python figure_detection.py <docling_json_file> [--verbose]")
        print("Example: python figure_detection.py output/docling_json/paper.json")
        sys.exit(1)
    
    docling_file = sys.argv[1]
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    detector = FigureDetector()
    analysis = detector.analyze_document(docling_file)
    detector.print_analysis_report(analysis, verbose=verbose)
    
    # Exit with appropriate code
    sys.exit(0 if analysis['should_extract'] else 1)


if __name__ == "__main__":
    main()