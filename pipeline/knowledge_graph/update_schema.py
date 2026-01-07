#!/usr/bin/env python3
"""
update_schema.py
----------------
Updates the Dgraph GraphQL schema to add exact indices for deduplication.

This script loads the schema.graphql file and applies it to the running Dgraph instance.
Adding 'exact' indices to the name, type, and namespace fields enables the equality (eq)
filter to work in GraphQL queries, which is required for the deduplication logic in
kg_data_loader.py to find existing nodes before creating duplicates.

Usage:
    python update_schema.py
"""

from dgraph_manager import DgraphManager
from pathlib import Path

def update_schema():
    """Load and apply the updated schema to Dgraph."""
    dgraph = DgraphManager()
    
    print("Updating Dgraph GraphQL schema...")
    print("(Adding exact indices to name, type, and namespace fields)")
    print()
    
    # The load_schema method reads schema.graphql and sends it to Dgraph's admin endpoint
    success = dgraph.load_schema("schema.graphql")
    
    if success:
        print("\n✓ SUCCESS: Schema updated!")
        print("\nThe following fields now support exact matching (eq filter):")
        print("  • Node.name - can now use: filter: { name: { eq: \"exact string\" } }")
        print("  • Node.type - can now use: filter: { type: { eq: \"biochemical_entity\" } }")
        print("  • Node.namespace - can now use: filter: { namespace: { eq: \"extracted\" } }")
        print("\nThis enables the kg_data_loader to properly check for existing nodes")
        print("and prevent duplicate entities with identical names from being created.")
    else:
        print("\n✗ ERROR: Failed to update schema")
        print("Make sure Dgraph is running at http://localhost:8080")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if update_schema() else 1)
