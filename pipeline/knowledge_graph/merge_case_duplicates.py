#!/usr/bin/env python3
"""
Merge Case-Insensitive Duplicate Nodes

Finds nodes that differ only by case (e.g., "Methanol" vs "methanol") and merges them:
1. Identify groups of nodes with same name (case-insensitive), type, and namespace
2. Choose canonical form (most common casing, or alphabetically first)
3. Update all relations to point to canonical node
4. Delete duplicate nodes

This is safe to run multiple times - it will only merge duplicates.
"""

import requests
import json
from collections import defaultdict
from typing import Dict, List, Tuple

DGRAPH_URL = "http://localhost:8080"

def query_dgraph(query: str) -> dict:
    """Execute DQL query."""
    try:
        response = requests.post(
            f"{DGRAPH_URL}/query",
            data=query,
            headers={"Content-Type": "application/dql"}
        )
        return response.json()
    except Exception as e:
        print(f"Query error: {e}")
        return {}

def mutate_dgraph(mutation: dict) -> dict:
    """Execute DQL mutation."""
    response = requests.post(
        f"{DGRAPH_URL}/mutate?commitNow=true",
        json=mutation,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def get_all_nodes() -> List[dict]:
    """Get all nodes from the database."""
    query = """{
      nodes(func: has(Node.name)) {
        uid
        Node.name
        Node.type
        Node.namespace
      }
    }"""
    
    result = query_dgraph(query)
    nodes = result.get('data', {}).get('nodes', [])
    
    # Normalize field names (remove Node. prefix)
    normalized = []
    for node in nodes:
        normalized.append({
            'uid': node.get('uid'),
            'name': node.get('Node.name', ''),
            'type': node.get('Node.type', ''),
            'namespace': node.get('Node.namespace', '')
        })
    
    return normalized

def find_case_duplicates(nodes: List[dict]) -> Dict[str, List[dict]]:
    """
    Group nodes by (lowercase_name, type, namespace).
    Returns only groups with multiple nodes (duplicates).
    """
    groups = defaultdict(list)
    
    for node in nodes:
        name = node.get('name', '')
        node_type = node.get('type', '')
        namespace = node.get('namespace', '')
        
        # Create key: (lowercase_name, type, namespace)
        key = (name.lower(), node_type, namespace)
        groups[key].append(node)
    
    # Filter to only groups with duplicates
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    
    return duplicates

def choose_canonical(nodes: List[dict]) -> Tuple[dict, List[dict]]:
    """
    Choose canonical node (keep) and duplicates (merge from these).
    Strategy: Keep the most common casing, or if tied, alphabetically first.
    """
    # Count occurrences of each exact casing
    casing_count = defaultdict(list)
    for node in nodes:
        name = node.get('name', '')
        casing_count[name].append(node)
    
    # Sort by: 1) most common (desc), 2) alphabetically (asc)
    sorted_casings = sorted(
        casing_count.items(),
        key=lambda x: (-len(x[1]), x[0])
    )
    
    canonical_name, canonical_nodes = sorted_casings[0]
    canonical_node = canonical_nodes[0]  # Pick first if multiple nodes with same casing
    
    # All other nodes are duplicates
    duplicates = []
    for name, nodes_list in sorted_casings[1:]:
        duplicates.extend(nodes_list)
    
    # Also add extra nodes with canonical casing (if more than one)
    if len(canonical_nodes) > 1:
        duplicates.extend(canonical_nodes[1:])
    
    return canonical_node, duplicates

def get_relations_for_node(node_uid: str) -> Tuple[List[dict], List[dict]]:
    """Get all relations where node is subject or object."""
    query = f"""{{
      as_subject(func: uid({node_uid})) {{
        ~Relation.subject {{
          uid
        }}
      }}
      as_object(func: uid({node_uid})) {{
        ~Relation.object {{
          uid
        }}
      }}
    }}"""
    
    result = query_dgraph(query)
    
    if not result:
        print(f"Warning: No result for node {node_uid}")
        return [], []
    
    data = result.get('data')
    if not data:
        print(f"Warning: No data in result for node {node_uid}")
        return [], []
    
    subject_relations = []
    object_relations = []
    
    if data.get('as_subject') and len(data['as_subject']) > 0:
        subject_relations = data['as_subject'][0].get('~Relation.subject', [])
    
    if data.get('as_object') and len(data['as_object']) > 0:
        object_relations = data['as_object'][0].get('~Relation.object', [])
    
    return subject_relations, object_relations

def merge_duplicate_nodes(canonical: dict, duplicates: List[dict], dry_run: bool = True):
    """Merge duplicate nodes into canonical node."""
    canonical_uid = canonical['uid']
    canonical_name = canonical['name']
    
    total_subject_relations = 0
    total_object_relations = 0
    
    print(f"\n  Canonical: {canonical_name} ({canonical_uid})")
    print(f"  Duplicates to merge:")
    
    for dup in duplicates:
        dup_uid = dup['uid']
        dup_name = dup['name']
        
        # Get relations for this duplicate
        subject_rels, object_rels = get_relations_for_node(dup_uid)
        
        print(f"    - {dup_name} ({dup_uid}): {len(subject_rels)} as subject, {len(object_rels)} as object")
        
        total_subject_relations += len(subject_rels)
        total_object_relations += len(object_rels)
        
        if not dry_run:
            # Update relations where duplicate is subject
            for rel in subject_rels:
                mutation = {
                    "set": [{
                        "uid": rel['uid'],
                        "Relation.subject": {"uid": canonical_uid}
                    }]
                }
                mutate_dgraph(mutation)
            
            # Update relations where duplicate is object
            for rel in object_rels:
                mutation = {
                    "set": [{
                        "uid": rel['uid'],
                        "Relation.object": {"uid": canonical_uid}
                    }]
                }
                mutate_dgraph(mutation)
            
            # Delete duplicate node
            mutation = {
                "delete": [{"uid": dup_uid}]
            }
            mutate_dgraph(mutation)
    
    print(f"  Total: {total_subject_relations + total_object_relations} relations to update")
    
    return len(duplicates), total_subject_relations + total_object_relations

def main():
    import sys
    
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        dry_run = False
        print("⚠️  EXECUTE MODE - Changes will be made to the database!")
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    else:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("Run with --execute to actually merge duplicates\n")
    
    print("Step 1: Fetching all nodes...")
    nodes = get_all_nodes()
    print(f"Found {len(nodes)} total nodes")
    
    print("\nStep 2: Finding case-insensitive duplicates...")
    duplicates = find_case_duplicates(nodes)
    
    if not duplicates:
        print("✅ No case-insensitive duplicates found!")
        return
    
    print(f"Found {len(duplicates)} groups with case-insensitive duplicates\n")
    
    total_nodes_to_merge = 0
    total_relations_to_update = 0
    
    print("Step 3: Analyzing duplicates...\n")
    
    for (lowercase_name, node_type, namespace), group in sorted(duplicates.items()):
        print(f"Group: '{lowercase_name}' (type: {node_type}, namespace: {namespace})")
        print(f"  {len(group)} nodes found:")
        
        # Show all casings in this group
        for node in group:
            print(f"    - {node['name']} ({node['uid']})")
        
        canonical, dups = choose_canonical(group)
        nodes_merged, relations_updated = merge_duplicate_nodes(canonical, dups, dry_run)
        
        total_nodes_to_merge += nodes_merged
        total_relations_to_update += relations_updated
    
    print("\n" + "="*70)
    print(f"Summary:")
    print(f"  Groups with duplicates: {len(duplicates)}")
    print(f"  Nodes to merge: {total_nodes_to_merge}")
    print(f"  Relations to update: {total_relations_to_update}")
    
    if dry_run:
        print("\n✨ Run with --execute to perform the merge")
    else:
        print("\n✅ Merge completed successfully!")

if __name__ == "__main__":
    main()
