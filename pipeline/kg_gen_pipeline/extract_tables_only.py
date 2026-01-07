#!/usr/bin/env python3
"""
extract_tables_only.py
----------------------
Extract relations from tables WITHOUT re-processing entire papers.

This script:
1. Reads existing Docling JSON (tables already there)
2. Creates chunks from table content
3. Runs LLM extraction on table chunks only
4. Outputs supplemental kg_format files with ONLY table relations
5. These can be loaded alongside existing data

Usage:
    python extract_tables_only.py                    # Process all papers
    python extract_tables_only.py --paper "A. Priyadarsini et al. 2023"  # Single paper
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.text_kg_extractor import ChunkKGExtractor


class TableOnlyExtractor:
    """Extract relations from tables only, without reprocessing text."""
    
    def __init__(self, model="ollama_chat/mistral:7b", api_base="http://localhost:11434"):
        print("Initializing KG extractor for tables...")
        self.kg_extractor = ChunkKGExtractor(model=model, api_base=api_base)
        
        # Initialize spaCy for sentence segmentation
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            print("Loaded spaCy for sentence segmentation")
        except:
            print("Warning: spaCy not available, using basic sentence splitting")
            self.nlp = None
    
    def _segment_text_into_sentences(self, text: str) -> List[dict]:
        """Segment table text into sentences for span mapping."""
        sentences = []
        
        if self.nlp:
            doc = self.nlp(text)
            for sent_idx, sent in enumerate(doc.sents):
                sentence_text = sent.text.strip()
                if sentence_text:
                    sentences.append({
                        "sentence_id": sent_idx,
                        "text": sentence_text,
                        "char_start": sent.start_char,
                        "char_end": sent.end_char,
                        "document_start": sent.start_char,
                        "document_end": sent.end_char,
                        "length": len(sentence_text)
                    })
        else:
            # Simple fallback
            import re
            parts = re.split(r'[.!?]+\s+', text)
            offset = 0
            for sent_idx, part in enumerate(parts):
                if part.strip():
                    sentences.append({
                        "sentence_id": sent_idx,
                        "text": part.strip(),
                        "char_start": offset,
                        "char_end": offset + len(part),
                        "document_start": offset,
                        "document_end": offset + len(part),
                        "length": len(part)
                    })
                    offset += len(part) + 2  # Approximate
        
        return sentences
    
    def create_table_chunk(self, table: dict, table_id: str, paper_name: str) -> Optional[dict]:
        """
        Convert a Docling table into a chunk suitable for LLM extraction.
        
        Args:
            table: Table dict from Docling JSON
            table_id: Generated ID like "page3_table1"
            paper_name: Source paper name
        
        Returns:
            Chunk dict or None if table has no content
        """
        # Extract table content - prefer structured data over text field
        # (text field contains full JSON dump with bbox/metadata)
        text_content = None
        
        if 'data' in table:
            # Convert structured table data to clean text
            text_content = self._table_data_to_text(table['data'])
        
        # Only use text field as fallback if no structured data
        if not text_content or not text_content.strip():
            text_content = table.get('text', '')
        
        if not text_content or not text_content.strip():
            return None
        
        # Get provenance
        prov = table.get('prov', [])
        if not prov:
            return None
        
        prov_entry = prov[0] if isinstance(prov, list) else prov
        page_no = prov_entry.get('page_no')
        bbox = prov_entry.get('bbox')
        
        # Segment table text into sentences
        chunk_text = f"[Table {table_id}]\n{text_content}"
        sentences = self._segment_text_into_sentences(text_content)
        
        # Create chunk in same format as text chunks
        chunk = {
            "chunk": chunk_text,
            "provenance": [{
                "docling_ref": table.get('self_ref', f'#/tables/{table_id}'),
                "label": "table",
                "pages": [{
                    "page_no": page_no,
                    "bbox": bbox
                }]
            }],
            "section": f"Visual Analysis: Table {table_id}",
            "table_id": table_id,
            "page_no": page_no,
            "sentences": sentences  # Add sentence segmentation for span mapping
        }
        
        return chunk
    
    def _table_data_to_text(self, table_data: dict) -> str:
        """Convert structured table data to readable text."""
        lines = []
        
        if 'grid' in table_data:
            # Table has grid structure - extract just text from each cell
            for row in table_data['grid']:
                row_cells = []
                for cell in row:
                    if isinstance(cell, dict):
                        # Cell is a dict with 'text' field
                        cell_text = cell.get('text', '').strip()
                    else:
                        # Cell is already text
                        cell_text = str(cell).strip()
                    
                    if cell_text:  # Only include non-empty cells
                        row_cells.append(cell_text)
                
                if row_cells:  # Only add non-empty rows
                    lines.append(' | '.join(row_cells))
                    
        elif isinstance(table_data, list):
            # Table is a list of rows
            for row in table_data:
                if isinstance(row, list):
                    row_cells = []
                    for cell in row:
                        if isinstance(cell, dict):
                            cell_text = cell.get('text', '').strip()
                        else:
                            cell_text = str(cell).strip()
                        
                        if cell_text:
                            row_cells.append(cell_text)
                    
                    if row_cells:
                        lines.append(' | '.join(row_cells))
        
        return '\n'.join(lines)
    
    def extract_tables_from_paper(
        self,
        docling_json_path: str,
        output_dir: Path
    ) -> Dict:
        """
        Extract relations from all tables in a single paper.
        
        Returns:
            Summary dict with extraction stats
        """
        print(f"\n{'='*80}")
        print(f"Processing: {Path(docling_json_path).name}")
        print(f"{'='*80}")
        
        # Load Docling JSON
        with open(docling_json_path, 'r') as f:
            docling = json.load(f)
        
        # Use original paper name from Docling origin, falling back to filename
        # Remove "Copy of " prefix if present for cleaner names
        origin_filename = docling.get('origin', {}).get('filename', '')
        if origin_filename:
            paper_name = origin_filename
            if paper_name.startswith('Copy of '):
                paper_name = paper_name[8:]  # Remove "Copy of " prefix
        else:
            paper_name = Path(docling_json_path).stem
            if paper_name.startswith('Copy of '):
                paper_name = paper_name[8:]
        
        # Extract tables
        tables = docling.get('tables', [])
        if not tables:
            print(f"  No tables found")
            return {
                'paper': paper_name,
                'tables_found': 0,
                'tables_processed': 0,
                'relations_extracted': 0
            }
        
        print(f"  Found {len(tables)} tables")
        
        table_chunks = []
        
        for table_index, table in enumerate(tables):
            # Get page number from provenance
            prov = table.get('prov', [])
            if not prov:
                continue
            
            prov_entry = prov[0] if isinstance(prov, list) else prov
            page_no = prov_entry.get('page_no')
            
            if page_no is None:
                continue
            
            # Generate table_id using Docling's global table index (0-based)
            # This matches the self_ref format: "#/tables/0", "#/tables/1", etc.
            table_id = f"page{page_no}_table{table_index}"
            
            # Create chunk
            chunk = self.create_table_chunk(table, table_id, paper_name)
            if chunk:
                table_chunks.append(chunk)
                print(f"    Created chunk for {table_id} (page {page_no}, docling index {table_index})")
        
        if not table_chunks:
            print(f"  No table content to extract")
            return {
                'paper': paper_name,
                'tables_found': len(tables),
                'tables_processed': 0,
                'relations_extracted': 0
            }
        
        print(f"  Extracting relations from {len(table_chunks)} tables...")
        
        # Run KG extraction on table chunks
        all_entities = set()
        all_relations = []
        
        for i, chunk in enumerate(table_chunks):
            try:
                print(f"    Processing {chunk['table_id']}...")
                
                # Extract using KG extractor (returns dict with entities, relations, etc.)
                result = self.kg_extractor.process_chunk(
                    chunk_data=chunk,
                    idx=i,
                    total_chunks=len(table_chunks)
                )
                
                entities = result.get('entities', [])
                relations = result.get('relations', [])
                
                # Add to global sets
                for entity in entities:
                    all_entities.add(str(entity))
                
                # Add table metadata to relations
                for relation in relations:
                    if 'source_span' not in relation:
                        relation['source_span'] = {}
                    
                    # Ensure it's marked as table source
                    relation['source_span'].update({
                        'span_type': 'visual_table',
                        'table_id': chunk['table_id'],
                        'page_number': chunk['page_no'],
                        'bbox_coordinates': chunk['provenance'][0]['pages'][0].get('bbox')
                    })
                    
                    all_relations.append(relation)
                
                print(f"      ✓ {chunk['table_id']}: {len(relations)} relations")
                
            except Exception as e:
                print(f"      ✗ Error extracting from {chunk['table_id']}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Create output in kg_format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{paper_name}_tables_only_kg_format_{timestamp}.json"
        
        output_data = {
            "summary": {
                "total_chunks": len(table_chunks),
                "errors": 0,
                "entities": len(all_entities),
                "relations": len(all_relations),
                "extraction_method": "table_only_extraction",
                "source_file": docling_json_path,
                "processed_at": datetime.now().isoformat()
            },
            "chunks": [],  # Tables are standalone, no multi-chunk processing
            "all_relations": all_relations,
            "entities": list(all_entities)
        }
        
        # Save output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"  ✅ Saved {len(all_relations)} table relations to {output_file.name}")
        
        return {
            'paper': paper_name,
            'tables_found': len(tables),
            'tables_processed': len(table_chunks),
            'relations_extracted': len(all_relations),
            'output_file': str(output_file)
        }
    
    def process_all_papers(self, docling_dir: Path, output_dir: Path):
        """Process all papers in the Docling directory."""
        docling_files = sorted(docling_dir.glob('*.json'))
        
        print(f"\n{'='*80}")
        print(f"TABLE-ONLY EXTRACTION")
        print(f"{'='*80}")
        print(f"Found {len(docling_files)} papers")
        print(f"Output directory: {output_dir}")
        print()
        
        results = []
        total_tables = 0
        total_relations = 0
        
        for docling_file in docling_files:
            result = self.extract_tables_from_paper(str(docling_file), output_dir)
            results.append(result)
            total_tables += result['tables_processed']
            total_relations += result['relations_extracted']
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Papers processed: {len(results)}")
        print(f"Tables extracted: {total_tables}")
        print(f"Relations generated: {total_relations}")
        print()
        print("Next steps:")
        print(f"1. Review output files in {output_dir}")
        print("2. Load to Dgraph:")
        print(f"   cd ../knowledge_graph")
        print(f"   python kg_data_loader.py --file {output_dir}/*_tables_only_kg_format_*.json")
        print("3. Test API:")
        print("   curl 'http://localhost:8001/api/relations/by-table?paper_id=PAPER.pdf&table_id=page3_table1'")


def main():
    parser = argparse.ArgumentParser(description='Extract relations from tables only')
    parser.add_argument(
        '--paper',
        help='Process only this paper (e.g., "A. Priyadarsini et al. 2023")',
        default=None
    )
    parser.add_argument(
        '--docling-dir',
        help='Directory containing Docling JSON files',
        default='output/docling_json'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for table extractions',
        default='output/table_triples'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    base_dir = Path(__file__).parent
    docling_dir = base_dir / args.docling_dir
    output_dir = base_dir / args.output_dir
    
    if not docling_dir.exists():
        print(f"Error: Docling directory not found: {docling_dir}")
        sys.exit(1)
    
    extractor = TableOnlyExtractor()
    
    if args.paper:
        # Process single paper
        docling_file = docling_dir / f"{args.paper}.json"
        if not docling_file.exists():
            print(f"Error: Paper not found: {docling_file}")
            sys.exit(1)
        
        extractor.extract_tables_from_paper(str(docling_file), output_dir)
    else:
        # Process all papers
        extractor.process_all_papers(docling_dir, output_dir)


if __name__ == '__main__':
    main()


# Standalone function for batch processing
def extract_tables_from_paper(docling_file: str, output_dir: str, 
                               model="ollama_chat/mistral:7b", 
                               api_base="http://localhost:11434") -> dict:
    """
    Extract table relations from a single paper.
    
    Args:
        docling_file: Path to Docling JSON file
        output_dir: Directory for output files
        model: LLM model to use
        api_base: API base URL for LLM
        
    Returns:
        dict with keys: success, table_count, relation_count, output_file, error
    """
    try:
        extractor = TableOnlyExtractor(model=model, api_base=api_base)
        result = extractor.extract_tables_from_paper(docling_file, Path(output_dir))
        return {
            'success': True,
            'table_count': result.get('tables_found', 0),
            'relation_count': result.get('relations_extracted', 0),
            'output_file': result.get('output_file', ''),
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'table_count': 0,
            'relation_count': 0,
            'output_file': None,
            'error': str(e)
        }
