#!/usr/bin/env python3
"""
reset_database.py
-----------------
Instructions for resetting Dgraph database with proper deduplication.

This script provides instructions since Dgraph GraphQL doesn't expose drop_all.
The cleanest way is to restart the Docker container.
"""

def main():
    print("=" * 80)
    print("DATABASE RESET INSTRUCTIONS")
    print("=" * 80)
    print()
    print("To reset the database and reload with proper deduplication:")
    print()
    print("1. Stop and remove Dgraph container (this deletes all data):")
    print("   docker compose down -v")
    print()
    print("2. Start Dgraph fresh:")
    print("   docker compose up -d")
    print()
    print("3. Wait a few seconds for Dgraph to start, then load schema:")
    print("   cd knowledge_graph")
    print("   python load_schema.py")
    print()
    print("4. Reload all papers with working deduplication:")
    print("   ./load_all_papers.sh")
    print()
    print("5. Verify deduplication worked:")
    print("   python scripts/discover_entities.py")
    print()
    print("=" * 80)
    print()
    print("The schema.graphql file already has the 'exact' indices configured,")
    print("so when you reload the schema in step 3, deduplication will work!")
    print()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

