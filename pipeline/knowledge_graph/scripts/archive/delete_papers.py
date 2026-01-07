#!/usr/bin/env python3
"""
Delete specific papers from the knowledge graph.

This script removes:
1. extraction_summary.pdf - Not a real research paper
2. Nguyen et al. 2021.pdf - Didn't process correctly through the triples pipeline
"""

import sys
import requests


def query_dgraph(query: str):
    """Execute a DQL query."""
    response = requests.post(
        "http://localhost:8080/query",
        data=query,
        headers={"Content-Type": "application/dql"}
    )
    return response.json()


def mutate_dgraph(mutation: str):
    """Execute a DQL mutation."""
    response = requests.post(
        "http://localhost:8080/mutate?commitNow=true",
        json={"delete": mutation},
        headers={"Content-Type": "application/json"}
    )
    return response.json()


def delete_paper(paper_uid: str, filename: str):
    """Delete a paper and all its relations from the database."""
    
    print(f"\nDeleting: {filename} (UID: {paper_uid})")
    
    # Step 1: Get all relations associated with this paper
    query = f'''
    {{
      relations(func: uid({paper_uid})) {{
        ~source_paper {{
          uid
        }}
      }}
    }}
    '''
    
    result = query_dgraph(query)
    relations = result.get('relations', [])
    
    relation_count = 0
    if relations and relations[0].get('~source_paper'):
        relation_uids = [r['uid'] for r in relations[0]['~source_paper']]
        relation_count = len(relation_uids)
        print(f"  Found {relation_count} relations to delete")
        
        # Delete all relations using JSON format
        for rel_uid in relation_uids:
            mutation = [{"uid": rel_uid}]
            mutate_dgraph(mutation)
        print(f"  Deleted {relation_count} relations")
    else:
        print("  No relations found")
    
    # Step 2: Delete the paper itself
    mutation = [{"uid": paper_uid}]
    mutate_dgraph(mutation)
    print(f"  Deleted paper: {filename}")
    
    return relation_count


def main():
    # Papers to delete
    papers_to_delete = [
        {"uid": "0xa82e", "filename": "extraction_summary.pdf"},
        {"uid": "0xada0", "filename": "Nguyen et al. 2021.pdf"}
    ]
    
    print("=" * 60)
    print("Deleting papers from knowledge graph")
    print("=" * 60)
    
    # Verify papers exist
    print("\nVerifying papers exist:")
    for paper in papers_to_delete:
        query = f'''
        {{
          paper(func: uid({paper["uid"]})) {{
            uid
            filename
            title
          }}
        }}
        '''
        result = query_dgraph(query)
        found = result.get('paper', [])
        if found:
            print(f"  ✓ Found: {found[0].get('filename')}")
        else:
            print(f"  ✗ NOT FOUND: {paper['filename']} (UID: {paper['uid']})")
    
    # Confirm deletion
    print("\n" + "=" * 60)
    response = input("Proceed with deletion? (yes/no): ")
    if response.lower() != 'yes':
        print("Deletion cancelled.")
        return
    
    # Delete papers
    total_relations = 0
    for paper in papers_to_delete:
        count = delete_paper(paper["uid"], paper["filename"])
        total_relations += count
    
    print("\n" + "=" * 60)
    print("Deletion complete!")
    print(f"  Deleted 2 papers")
    print(f"  Deleted {total_relations} relations")
    print("=" * 60)
    
    # Verify by checking total count
    print("\nVerifying total papers remaining:")
    query = '''
    {
      papers(func: type(Paper)) {
        count(uid)
      }
    }
    '''
    result = query_dgraph(query)
    if result.get('papers'):
        count = result['papers'][0].get('count', 0)
        print(f"  Papers remaining: {count}")
        print(f"  (Expected: 47)")


if __name__ == "__main__":
    main()
