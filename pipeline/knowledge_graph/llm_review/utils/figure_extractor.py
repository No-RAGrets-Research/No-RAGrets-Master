"""
Figure Extractor for Paper Review System

Extracts figures from PDFs using Docling JSON and PyMuPDF.
Adapted from kg_gen_pipeline/core/visual_kg_extractor.py
"""

import json
import fitz  # PyMuPDF
import io
from PIL import Image
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FigureExtractor:
    """Extract figures from scientific papers for quality assessment."""
    
    def __init__(self, cleanup_images: bool = True):
        """
        Initialize figure extractor.
        
        Args:
            cleanup_images: Whether to delete extracted images after processing
        """
        self.cleanup_images = cleanup_images
    
    def parse_docling_figures(self, docling_json_path: str) -> Dict[int, Dict]:
        """
        Extract figure metadata from Docling JSON.
        
        Args:
            docling_json_path: Path to Docling JSON file
        
        Returns:
            Dictionary mapping page numbers to figure metadata
        """
        with open(docling_json_path, 'r') as f:
            data = json.load(f)
        
        # Extract captions
        captions = [item for item in data['texts'] if item.get('label') == 'caption']
        
        # Extract pictures  
        pictures = data.get('pictures', [])
        
        # Organize by page
        figures_by_page = {}
        
        for caption in captions:
            if 'prov' in caption:
                for prov in caption['prov']:
                    page_num = prov['page_no']
                    if page_num not in figures_by_page:
                        figures_by_page[page_num] = {'captions': [], 'pictures': []}
                    figures_by_page[page_num]['captions'].append({
                        'text': caption['text'],
                        'prov': prov
                    })
        
        for picture in pictures:
            if 'prov' in picture:
                for prov in picture['prov']:
                    page_num = prov['page_no']
                    if page_num not in figures_by_page:
                        figures_by_page[page_num] = {'captions': [], 'pictures': []}
                    figures_by_page[page_num]['pictures'].append({
                        'self_ref': picture.get('self_ref', ''),
                        'prov': prov
                    })
        
        return figures_by_page

    def extract_pdf_images(self, pdf_path: str, target_pages: Optional[List[int]] = None) -> Dict[int, List[Dict]]:
        """
        Extract embedded images from PDF pages.
        
        Args:
            pdf_path: Path to PDF file
            target_pages: Optional list of specific pages to extract (1-based)
        
        Returns:
            Dictionary mapping page numbers to lists of image data
        """
        pdf_doc = fitz.open(pdf_path)
        extracted_images = {}
        
        for page_num in range(len(pdf_doc)):
            page_num_1based = page_num + 1
            
            if target_pages and page_num_1based not in target_pages:
                continue
                
            page = pdf_doc[page_num]
            images = page.get_images(full=True)
            
            if images:
                extracted_images[page_num_1based] = []
                
                for img_index, img in enumerate(images):
                    try:
                        xref = img[0]
                        base_image = pdf_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        
                        extracted_images[page_num_1based].append({
                            'index': img_index,
                            'pil_image': pil_image,
                            'size': pil_image.size,
                            'mode': pil_image.mode,
                            'image_bytes': image_bytes  # Keep for saving if needed
                        })
                        
                    except Exception as e:
                        print(f"Error extracting image {img_index} on page {page_num_1based}: {e}")
        
        pdf_doc.close()
        return extracted_images

    def match_figures_to_images(self, docling_figures: Dict, pdf_images: Dict) -> List[Dict]:
        """
        Match Docling figure metadata with extracted PDF images.
        
        Args:
            docling_figures: Figure metadata from Docling JSON
            pdf_images: Extracted images from PDF
        
        Returns:
            List of matched figures with captions and images
        """
        matches = []
        
        for page_num in docling_figures.keys():
            docling_data = docling_figures[page_num]
            pdf_data = pdf_images.get(page_num, [])
            
            # Simple positional matching
            for i, caption in enumerate(docling_data['captions']):
                if i < len(pdf_data):
                    matches.append({
                        'page': page_num,
                        'caption_text': caption['text'],
                        'caption_prov': caption['prov'],
                        'image': pdf_data[i]['pil_image'],
                        'image_size': pdf_data[i]['size'],
                        'figure_id': f"page{page_num}_fig{i}"
                    })
        
        return matches

    def extract_figures(self, pdf_path: str, docling_json_path: str) -> List[Dict]:
        """
        Complete pipeline to extract figures from a paper.
        
        Args:
            pdf_path: Path to PDF file
            docling_json_path: Path to corresponding Docling JSON file
        
        Returns:
            List of figure dictionaries with image, caption, and metadata
        """
        # Parse Docling JSON
        docling_figures = self.parse_docling_figures(docling_json_path)
        
        # Extract images from PDF
        target_pages = list(docling_figures.keys())
        pdf_images = self.extract_pdf_images(pdf_path, target_pages)
        
        # Match figures to images
        matches = self.match_figures_to_images(docling_figures, pdf_images)
        
        return matches

    def get_figure_by_id(self, pdf_path: str, docling_json_path: str, figure_id: str) -> Optional[Dict]:
        """
        Extract a specific figure by ID.
        
        Args:
            pdf_path: Path to PDF file
            docling_json_path: Path to Docling JSON file
            figure_id: Figure identifier (e.g., "page5_fig0")
        
        Returns:
            Figure dictionary or None if not found
        """
        all_figures = self.extract_figures(pdf_path, docling_json_path)
        
        for figure in all_figures:
            if figure['figure_id'] == figure_id:
                return figure
        
        return None


def load_paper_figures(pdf_filename: str, papers_dir: str = "papers", 
                      docling_dir: str = "kg_gen_pipeline/output/docling_json") -> List[Dict]:
    """
    Convenience function to load all figures from a paper.
    
    Args:
        pdf_filename: Name of PDF file
        papers_dir: Directory containing PDFs (relative to repo root)
        docling_dir: Directory containing Docling JSON files (relative to repo root)
    
    Returns:
        List of figure dictionaries
    """
    from pathlib import Path
    import os
    
    # Find repository root (contains README.md, papers/, kg_gen_pipeline/)
    current_file = Path(__file__).resolve()
    repo_root = current_file
    while repo_root.parent != repo_root:
        if (repo_root / "README.md").exists() and (repo_root / "papers").exists():
            break
        repo_root = repo_root.parent
    
    # Construct absolute paths
    pdf_path = repo_root / papers_dir / pdf_filename
    docling_path = repo_root / docling_dir
    
    # Find corresponding Docling JSON
    stem = Path(pdf_filename).stem
    docling_pattern = f"*{stem}*.json"
    
    docling_candidates = list(docling_path.glob(docling_pattern))
    if not docling_candidates:
        raise FileNotFoundError(f"No Docling JSON found for {pdf_filename} in {docling_path}")
    
    # Use most recent
    docling_json_path = sorted(docling_candidates)[-1]
    
    # Extract figures
    extractor = FigureExtractor()
    figures = extractor.extract_figures(str(pdf_path), str(docling_json_path))
    
    return figures


# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        figures = load_paper_figures(pdf_file)
        print(f"Extracted {len(figures)} figures from {pdf_file}:")
        for fig in figures:
            print(f"  - {fig['figure_id']}: {fig['caption_text'][:80]}...")
    else:
        print("Usage: python figure_extractor.py <pdf_filename>")
