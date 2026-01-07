#!/usr/bin/env python3
"""
discover_entities.py
--------------------
Discover all entities in the knowledge graph and generate statistics.
Use this to verify deduplication is working properly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dgraph_manager import DgraphManager

def discover_entities():
    """Query database for all entities and generate statistics."""
    print("Knowledge Graph Entity Discovery")
    print("=" * 80)
    
    dgraph = DgraphManager()
    
    # Check database connection
    print("\nChecking database connection...")
    if not dgraph.health_check():
        print("ERROR: Dgraph is not running or not reachable")
        return 1
    
    print("SUCCESS: Connected to Dgraph")
    
    # Get all nodes
    print("\nExtracting entities...")
    query = '''
    {
      queryNode {
        id
        name
        type
        namespace
      }
    }
    '''
    
    result = dgraph.query(query)
    nodes = result.get('data', {}).get('queryNode', [])
    
    print(f"Found {len(nodes)} entities in database")
    
    # Get statistics
    print("\n" + "=" * 80)
    print("ENTITY STATISTICS")
    print("=" * 80)
    
    print(f"\nTotal Entities: {len(nodes):,}")
    
    # Type distribution
    types = {}
    for node in nodes:
        node_type = node.get('type', 'unknown')
        types[node_type] = types.get(node_type, 0) + 1
    
    print("\nEntity Type Distribution:")
    for entity_type, count in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  {entity_type}: {count:,}")
    
    # Namespace distribution
    namespaces = {}
    for node in nodes:
        namespace = node.get('namespace', 'unknown')
        namespaces[namespace] = namespaces.get(namespace, 0) + 1
    
    print("\nNamespace Distribution:")
    for namespace, count in sorted(namespaces.items(), key=lambda x: -x[1]):
        print(f"  {namespace}: {count:,}")
    
    # Test for duplicate names
    print("\nChecking for duplicate names...")
    names = {}
    for node in nodes:
        name = node.get('name', '')
        if name:
            if name not in names:
                names[name] = []
            names[name].append(node['id'])
    
    duplicates = {name: uids for name, uids in names.items() if len(uids) > 1}
    
    if duplicates:
        print(f"WARNING: Found {len(duplicates)} entity names with duplicates")
        print("\nSample duplicates:")
        for name, uids in list(duplicates.items())[:5]:
            print(f"  '{name}': {len(uids)} occurrences")
    else:
        print("SUCCESS: No duplicate entity names found!")
        print("Deduplication is working correctly.")
    
    print("\n" + "=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(discover_entities())
