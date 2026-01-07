#!/usr/bin/env python3
"""
dgraph_manager.py
-----------------
Dgraph database schema and connection management utility.

This module provides the DgraphManager class for:
- Database health checking
- Schema loading and management
- GraphQL query and mutation execution
- Connection management for Dgraph v25.0.0+

Usage:
    python dgraph_manager.py  # Load schema and test connection
    
    # Or import in other scripts:
    from dgraph_manager import DgraphManager
    manager = DgraphManager()
    manager.load_schema('schema.graphql')
"""

import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any

class DgraphManager:
    def __init__(self, url: str = "http://localhost:8080"):
        self.url = url
        self.graphql_endpoint = f"{url}/graphql"
        self.admin_endpoint = f"{url}/admin"
        
    def load_schema(self, schema_file: str = "schema.graphql") -> bool:
        """Load GraphQL schema into Dgraph."""
        schema_path = Path(schema_file)
        if not schema_path.exists():
            print(f"ERROR: Schema file not found: {schema_file}")
            return False
            
        try:
            schema_content = schema_path.read_text()
            # Use GraphQL mutation format for Dgraph v25+
            mutation = {
                "query": "mutation updateSchema($sch: String!) { updateGQLSchema(input: { set: { schema: $sch } }) { gqlSchema { schema } } }",
                "variables": {
                    "sch": schema_content.strip()
                }
            }
            response = requests.post(self.admin_endpoint, json=mutation)
            
            if response.status_code == 200:
                print("SUCCESS: Dgraph schema loaded successfully")
                return True
            else:
                print(f"ERROR: Schema load failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"ERROR: Error loading schema: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Dgraph is running and accessible."""
        try:
            response = requests.get(f"{self.url}/health")
            if response.status_code == 200:
                print("SUCCESS: Dgraph is healthy")
                return True
            else:
                print(f"WARNING: Dgraph health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"ERROR: Cannot connect to Dgraph: {e}")
            return False
    
    def query(self, query: str, variables: Optional[Dict] = None) -> Dict[Any, Any]:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        response = requests.post(self.graphql_endpoint, json=payload)
        return response.json()
    
    def mutate(self, mutation: str, variables: Optional[Dict] = None) -> Dict[Any, Any]:
        """Execute a GraphQL mutation."""
        return self.query(mutation, variables)

if __name__ == "__main__":
    # Test the schema loading
    manager = DgraphManager()
    
    print("Testing Dgraph connection...")
    if manager.health_check():
        print("\nLoading schema...")
        manager.load_schema("schema.graphql")
    else:
        print("ERROR: Please start Dgraph first: docker-compose up -d")