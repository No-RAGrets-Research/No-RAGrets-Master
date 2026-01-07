#!/usr/bin/env python3
"""
load_schema.py
--------------
Loads the GraphQL schema into Dgraph.

This script reads schema.graphql and applies it to the running Dgraph instance.
It performs a COMPLETE schema load/replacement, not just updates.

When to use:
- After starting Dgraph fresh (docker compose up -d)
- After modifying schema.graphql
- When schema is missing or corrupted

Note: start_carbonbridge.sh already calls this automatically.

Usage:
    python load_schema.py
"""

from dgraph_manager import DgraphManager
from pathlib import Path

def load_schema():
    """Load the complete schema into Dgraph."""
    dgraph = DgraphManager()
    
    print("Loading GraphQL schema into Dgraph...")
    print()
    
    # The load_schema method reads schema.graphql and sends it to Dgraph's admin endpoint
    # This replaces the entire schema, not just updates
    success = dgraph.load_schema("schema.graphql")
    
    if success:
        print("\nSUCCESS: Schema loaded!")
        print("\nSchema features enabled:")
        print("  - Exact matching on Node.name, type, and namespace")
        print("  - Full-text search on Node.name and Relation.predicate")
        print("  - Trigram search for fuzzy matching")
        print("\nThe kg_data_loader can now properly deduplicate entities.")
    else:
        print("\nERROR: Failed to load schema")
        print("Make sure Dgraph is running at http://localhost:8080")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if load_schema() else 1)
