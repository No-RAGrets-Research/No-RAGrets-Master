#!/usr/bin/env python3
"""
migrate_visual_papers.py
------------------------
Migrate relations from *_visual_kg_format.pdf papers to their parent papers.

This script:
1. Finds all papers ending in _visual_kg_format.pdf
2. Updates all their relations to point to the correct paper name
3. Deletes the _visual_kg_format.pdf paper entries

Usage:
    python migrate_visual_papers.py [--dry-run]
"""

import sys
from dgraph_manager import DgraphManager

def migrate_visual_papers(dry_run=False):
    """Migrate relations from visual_kg_format papers to their parent papers."""
    manager = DgraphManager("http://localhost:8080")
    
    # Step 1: Find all _visual_kg_format.pdf papers
    # Note: We'll filter in Python since Dgraph regexp can be tricky
    query = """
    {
      queryPaper {
        id
        filename
        title
        total_relations
      }
    }
    """
    
    result = manager.query(query)
    all_papers = result.get('data', {}).get('queryPaper', [])
    
    # Filter for visual_kg_format papers in Python
    visual_papers = [p for p in all_papers if '_visual_kg_format.pdf' in p['filename']]
    
    if not visual_papers:
        print("No _visual_kg_format.pdf papers found. Migration complete!")
        return
    
    print(f"Found {len(visual_papers)} visual_kg_format papers to migrate:")
    for paper in visual_papers:
        print(f"  - {paper['filename']} ({paper['total_relations']} relations)")
    
    if dry_run:
        print("\n[DRY RUN] Would migrate these papers. Run without --dry-run to execute.")
        return
    
    print("\nStarting migration...\n")
    
    # Step 2: For each visual paper, update its relations to point to the correct paper
    total_migrated = 0
    for paper in visual_papers:
        old_filename = paper['filename']
        # Remove _visual_kg_format.pdf suffix
        new_filename = old_filename.replace('_visual_kg_format.pdf', '.pdf')
        
        print(f"Migrating: {old_filename} -> {new_filename}")
        
        # Check if target paper exists
        check_query = """
        query CheckPaper($filename: String!) {
          queryPaper(filter: { filename: { eq: $filename } }) {
            id
            filename
          }
        }
        """
        
        check_result = manager.query(check_query, {'filename': new_filename})
        target_papers = check_result.get('data', {}).get('queryPaper', [])
        
        if not target_papers:
            print(f"  WARNING: Target paper '{new_filename}' does not exist!")
            print(f"  Creating it...")
            
            # Create the target paper
            create_mutation = """
            mutation CreatePaper($title: String!, $filename: String!) {
              addPaper(input: [{
                title: $title,
                filename: $filename
              }]) {
                paper { id }
              }
            }
            """
            
            title = new_filename.replace('.pdf', '').replace('_', ' ')
            create_result = manager.mutate(create_mutation, {
                'title': title,
                'filename': new_filename
            })
            
            if 'errors' in create_result:
                print(f"  ERROR creating paper: {create_result['errors']}")
                continue
        
        # Update all relations from this visual paper to point to the correct paper
        update_mutation = """
        mutation UpdateRelations($oldPaper: String!, $newPaper: String!) {
          updateRelation(
            input: {
              filter: { source_paper: { eq: $oldPaper } }
              set: { source_paper: $newPaper }
            }
          ) {
            numUids
          }
        }
        """
        
        update_result = manager.mutate(update_mutation, {
            'oldPaper': old_filename,
            'newPaper': new_filename
        })
        
        if 'errors' in update_result:
            print(f"  ERROR updating relations: {update_result['errors']}")
            continue
        
        num_updated = update_result.get('data', {}).get('updateRelation', {}).get('numUids', 0)
        total_migrated += num_updated
        print(f"  ✓ Migrated {num_updated} relations")
        
        # Delete the visual_kg_format paper
        delete_mutation = """
        mutation DeletePaper($paperId: [ID!]) {
          deletePaper(filter: { id: $paperId }) {
            numUids
          }
        }
        """
        
        delete_result = manager.mutate(delete_mutation, {'paperId': [paper['id']]})
        
        if 'errors' in delete_result:
            print(f"  ERROR deleting paper: {delete_result['errors']}")
        else:
            print(f"  ✓ Deleted paper: {old_filename}")
    
    print(f"\n{'='*60}")
    print(f"Migration complete!")
    print(f"  Papers processed: {len(visual_papers)}")
    print(f"  Relations migrated: {total_migrated}")
    print(f"{'='*60}")

if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("Running in DRY RUN mode (no changes will be made)\n")
    
    migrate_visual_papers(dry_run=dry_run)
