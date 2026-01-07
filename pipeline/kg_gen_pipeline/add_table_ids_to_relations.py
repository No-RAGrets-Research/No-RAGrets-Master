#!/usr/bin/env python3
"""
Retroactively add table_id to relations that came from tables.

This script:
1. Reads Docling JSON to find table locations (page numbers + bounding boxes)
2. Reads text triple JSON files to find relations
3. Matches relations to tables based on chunk provenance (if it references #/tables/X)
4. Adds table_id field to matching relations
5. Outputs updated kg_format files

This avoids re-running the entire extraction pipeline.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def load_docling_tables(docling_json_path: str) -> Dict[str, Dict]:
    """
    Extract table metadata from Docling JSON.
    
    Returns:
        Dict mapping table_ref (e.g., "#/tables/0") to table metadata
        {
            "#/tables/0": {
                "page_no": 3,
                "bbox": {...},
                "table_id": "page3_table1"
            }
        }
    """
    with open(docling_json_path, 'r') as f:
        docling = json.load(f)
    
    tables = {}
    if 'tables' not in docling:
        return tables
    
    # Track tables per page for numbering
    tables_per_page = {}
    
    for i, table in enumerate(docling['tables']):
        table_ref = table.get('self_ref', f'#/tables/{i}')
        
        if 'prov' in table and len(table['prov']) > 0:
            prov = table['prov'][0]
            page_no = prov.get('page_no')
            
            if page_no is not None:
                # Count tables on this page
                if page_no not in tables_per_page:
                    tables_per_page[page_no] = 0
                tables_per_page[page_no] += 1
                table_num = tables_per_page[page_no]
                
                table_id = f"page{page_no}_table{table_num}"
                
                tables[table_ref] = {
                    'page_no': page_no,
                    'bbox': prov.get('bbox'),
                    'table_id': table_id,
                    'table_ref': table_ref
                }
    
    return tables


def find_table_from_chunk_provenance(chunk_provenance: List[Dict], tables: Dict[str, Dict]) -> Optional[str]:
    """
    Check if a chunk's provenance references a table.
    
    Args:
        chunk_provenance: Provenance data from a text chunk
        tables: Dict of table metadata keyed by table_ref
    
    Returns:
        table_id if chunk came from a table, else None
    """
    if not chunk_provenance:
        return None
    
    for prov in chunk_provenance:
        docling_ref = prov.get('docling_ref', '')
        if docling_ref.startswith('#/tables/'):
            # This chunk came from a table
            if docling_ref in tables:
                return tables[docling_ref]['table_id']
    
    return None


def process_text_triples_file(
    text_triples_path: str,
    docling_json_path: str,
    output_path: str
) -> Tuple[int, int]:
    """
    Process a text triples file and add table_id to relations from tables.
    
    Returns:
        (total_relations, relations_with_table_id)
    """
    # Load table metadata
    tables = load_docling_tables(docling_json_path)
    
    if not tables:
        print(f"  No tables found in Docling JSON")
        return 0, 0
    
    print(f"  Found {len(tables)} tables: {[t['table_id'] for t in tables.values()]}")
    
    # Load text triples
    with open(text_triples_path, 'r') as f:
        data = json.load(f)
    
    total_relations = 0
    relations_with_table_id = 0
    
    # Process each chunk
    for chunk in data.get('chunks', []):
        chunk_provenance = chunk.get('provenance', [])
        
        # Check if this chunk came from a table
        table_id = find_table_from_chunk_provenance(chunk_provenance, tables)
        
        # Update relations in this chunk
        for relation in chunk.get('relations', []):
            total_relations += 1
            
            if table_id:
                # Add table_id to the relation's source_span
                if 'source_span' in relation:
                    relation['source_span']['table_id'] = table_id
                    relation['source_span']['span_type'] = 'visual_table'
                    relations_with_table_id += 1
    
    # Also check all_relations if it exists
    for relation in data.get('all_relations', []):
        # This is trickier - we need to match by chunk_id
        if 'source_span' in relation and 'location' in relation['source_span']:
            chunk_id = relation['source_span']['location'].get('chunk_id')
            
            if chunk_id is not None and chunk_id < len(data.get('chunks', [])):
                chunk = data['chunks'][chunk_id]
                chunk_provenance = chunk.get('provenance', [])
                table_id = find_table_from_chunk_provenance(chunk_provenance, tables)
                
                if table_id:
                    relation['source_span']['table_id'] = table_id
                    relation['source_span']['span_type'] = 'visual_table'
    
    # Save updated file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return total_relations, relations_with_table_id


def main():
    """Process all text triple files and add table_id where applicable."""
    
    base_dir = Path(__file__).parent / 'output'
    docling_dir = base_dir / 'docling_json'
    text_triples_dir = base_dir / 'text_triples'
    output_dir = base_dir / 'text_triples_with_tables'
    
    if not docling_dir.exists():
        print(f"Error: {docling_dir} not found")
        return
    
    if not text_triples_dir.exists():
        print(f"Error: {text_triples_dir} not found")
        return
    
    print("=" * 80)
    print("Adding table_id to text relations")
    print("=" * 80)
    print()
    
    total_files = 0
    total_relations = 0
    total_table_relations = 0
    
    # Process each text triples file
    for text_file in sorted(text_triples_dir.glob('*.json')):
        # Extract base paper name by removing the _kg_results_TIMESTAMP suffix
        # e.g., "Copy of A. Priyadarsini et al. 2023_kg_results_20251115_012936.json"
        #    -> "Copy of A. Priyadarsini et al. 2023.json"
        base_name = text_file.stem
        if '_kg_results_' in base_name:
            base_name = base_name.split('_kg_results_')[0]
        
        # Find corresponding Docling JSON
        docling_file = docling_dir / f"{base_name}.json"
        
        if not docling_file.exists():
            print(f"⚠️  {text_file.name}")
            print(f"  Docling JSON not found: {docling_file.name}")
            continue
        
        print(f"📄 {text_file.name}")
        
        output_file = output_dir / text_file.name
        
        try:
            relations, table_relations = process_text_triples_file(
                str(text_file),
                str(docling_file),
                str(output_file)
            )
            
            total_files += 1
            total_relations += relations
            total_table_relations += table_relations
            
            if table_relations > 0:
                print(f"  ✅ {table_relations}/{relations} relations tagged with table_id")
            else:
                print(f"  ℹ️  No table relations found ({relations} total relations)")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Files processed: {total_files}")
    print(f"Total relations: {total_relations}")
    print(f"Relations with table_id: {total_table_relations}")
    print(f"Percentage: {100 * total_table_relations / total_relations if total_relations > 0 else 0:.1f}%")
    print()
    print(f"Updated files saved to: {output_dir}")
    print()
    print("Next steps:")
    print("1. Review a few updated files to verify table_id was added correctly")
    print("2. Load the updated files into Dgraph using kg_data_loader.py")
    print("3. Test /api/relations/by-table endpoint with actual table_ids")


if __name__ == '__main__':
    main()
