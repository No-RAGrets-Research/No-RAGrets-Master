#!/usr/bin/env python3
"""
Batch process all papers to extract table relations.
Reads existing Docling JSON files and extracts relations from tables only.
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from kg_gen_pipeline.extract_tables_only import extract_tables_from_paper


def main():
    # Setup paths
    project_root = Path(__file__).parent.parent
    docling_dir = project_root / "kg_gen_pipeline" / "output" / "docling_json"
    output_dir = project_root / "kg_gen_pipeline" / "output" / "table_triples"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all Docling JSON files
    json_files = sorted(docling_dir.glob("*.json"))
    
    print(f"Found {len(json_files)} Docling JSON files")
    print("=" * 80)
    
    # Track statistics
    stats = {
        'total_papers': len(json_files),
        'papers_with_tables': 0,
        'papers_without_tables': 0,
        'total_tables': 0,
        'total_relations': 0,
        'errors': []
    }
    
    # Process each file
    for i, json_file in enumerate(json_files, 1):
        print(f"\n[{i}/{len(json_files)}] Processing: {json_file.name}")
        print("-" * 80)
        
        try:
            # Extract tables
            result = extract_tables_from_paper(
                str(json_file),
                str(output_dir)
            )
            
            if result['success']:
                if result['table_count'] > 0:
                    stats['papers_with_tables'] += 1
                    stats['total_tables'] += result['table_count']
                    stats['total_relations'] += result['relation_count']
                    
                    print(f"✓ Extracted {result['relation_count']} relations from {result['table_count']} tables")
                    print(f"  Output: {result['output_file']}")
                else:
                    stats['papers_without_tables'] += 1
                    print("  No tables found in this paper")
            else:
                stats['errors'].append({
                    'paper': json_file.name,
                    'error': result.get('error', 'Unknown error')
                })
                print(f"✗ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            stats['errors'].append({
                'paper': json_file.name,
                'error': str(e)
            })
            print(f"✗ Exception: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total papers processed: {stats['total_papers']}")
    print(f"Papers with tables: {stats['papers_with_tables']}")
    print(f"Papers without tables: {stats['papers_without_tables']}")
    print(f"Total tables extracted: {stats['total_tables']}")
    print(f"Total relations extracted: {stats['total_relations']}")
    
    if stats['errors']:
        print(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors']:
            print(f"  - {error['paper']}: {error['error']}")
    
    # Save summary to file
    summary_file = output_dir / f"extraction_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    print("\nNext step: Load table relations to Dgraph with:")
    print(f"  python3 knowledge_graph/kg_data_loader.py {output_dir}/*.json")


if __name__ == "__main__":
    main()
