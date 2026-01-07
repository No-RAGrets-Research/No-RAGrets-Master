#!/usr/bin/env python3
"""
Database status checker - shows what's currently loaded in the database.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from dgraph_manager import DgraphManager

def check_database_status():
    """Check what's currently in the database."""
    
    manager = DgraphManager()
    if not manager.health_check():
        print("ERROR: Dgraph is not running. Start it with:")
        print("   cd knowledge_graph && docker compose up -d")
        return False
    
    print("DATABASE STATUS")
    print("=" * 50)
    
    # Count papers
    papers_query = """
    query {
      queryPaper {
        id
        title
        filename
        total_entities
        total_relations
      }
    }"""
    
    papers_response = manager.query(papers_query)
    papers = papers_response.get('data', {}).get('queryPaper', [])
    
    print(f"Papers loaded: {len(papers)}")
    if papers:
        print("\nLoaded papers:")
        for paper in papers[:10]:  # Show first 10
            entities = paper.get('total_entities', 0)
            relations = paper.get('total_relations', 0)
            print(f"  - {paper['title']} ({entities} entities, {relations} relations)")
        
        if len(papers) > 10:
            print(f"  ... and {len(papers) - 10} more papers")
    
    # Count nodes
    nodes_query = """
    query {
      aggregateNode {
        count
      }
    }"""
    
    nodes_response = manager.query(nodes_query)
    node_count = nodes_response.get('data', {}).get('aggregateNode', {}).get('count', 0)
    print(f"\nTotal nodes (entities): {node_count}")
    
    # Count relations
    relations_query = """
    query {
      aggregateRelation {
        count
      }
    }"""
    
    relations_response = manager.query(relations_query)
    relation_count = relations_response.get('data', {}).get('aggregateRelation', {}).get('count', 0)
    print(f"Total relations: {relation_count}")
    
    # Show sample entities
    sample_nodes_query = """
    query {
      queryNode(first: 10) {
        name
        type
        namespace
      }
    }"""
    
    sample_response = manager.query(sample_nodes_query)
    sample_nodes = sample_response.get('data', {}).get('queryNode', [])
    
    if sample_nodes:
        print(f"\nSample entities:")
        for node in sample_nodes:
            print(f"  - {node['name']} ({node.get('type', 'unknown')})")
    
    return True

def main():
    success = check_database_status()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())