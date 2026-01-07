"""
Knowledge Graph API Client

Provides methods to interact with the Knowledge Graph REST API endpoints.
"""

import requests
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv

load_dotenv()


class KnowledgeGraphClient:
    """Client for interacting with the Knowledge Graph API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API. Defaults to environment variable API_BASE_URL.
        """
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8001/api')
        self.session = requests.Session()
    
    def get_most_connected_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most connected entities (hub entities) in the graph.
        
        Args:
            limit: Maximum number of entities to return
            
        Returns:
            List of entity dictionaries with connection counts
        """
        endpoint = f"{self.base_url}/entities/most-connected"
        params = {"limit": limit}
        
        response = self.session.get(endpoint, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_entity_connections(
        self, 
        entity_name: str, 
        direction: str = "both",
        max_relations: int = 1000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all connections (relations) for a specific entity.
        
        Args:
            entity_name: Name of the entity
            direction: Direction of relationships ("incoming", "outgoing", "both")
            max_relations: Maximum relations per direction
            
        Returns:
            Dictionary with "incoming" and/or "outgoing" relation lists
        """
        endpoint = f"{self.base_url}/entities/{entity_name}/connections"
        params = {
            "direction": direction,
            "max_relations": max_relations
        }
        
        response = self.session.get(endpoint, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def search_relations(
        self,
        predicate: Optional[str] = None,
        subject: Optional[str] = None,
        object_name: Optional[str] = None,
        section: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for relations by various criteria.
        
        Args:
            predicate: Filter by relationship type
            subject: Filter by subject entity name
            object_name: Filter by object entity name
            section: Filter by document section
            limit: Maximum results
            
        Returns:
            List of relation dictionaries
        """
        endpoint = f"{self.base_url}/relations/search"
        params = {
            "limit": limit
        }
        
        if predicate:
            params["predicate"] = predicate
        if subject:
            params["subject"] = subject
        if object_name:
            params["object"] = object_name
        if section:
            params["section"] = section
        
        response = self.session.get(endpoint, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_paper_relations(
        self,
        paper_id: str,
        section: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get all relations from a specific paper.
        
        Args:
            paper_id: Paper ID or filename
            section: Optional filter by document section
            limit: Maximum number of relations to return
            
        Returns:
            List of relation dictionaries from this paper
        """
        endpoint = f"{self.base_url}/papers/{paper_id}/relations"
        params = {"limit": limit}
        
        if section:
            params["section"] = section
        
        response = self.session.get(endpoint, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_relation_provenance(self, relation_id: str) -> Dict[str, Any]:
        """
        Get detailed provenance information for a relation.
        
        Args:
            relation_id: Relation UID
            
        Returns:
            Dictionary with provenance details
        """
        endpoint = f"{self.base_url}/relations/{relation_id}/provenance"
        
        response = self.session.get(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def get_relation_source_span(self, relation_id: str) -> Dict[str, Any]:
        """
        Get the exact text span where a relation was extracted.
        
        Args:
            relation_id: Relation UID
            
        Returns:
            Dictionary with source span details including sentence text and entity positions
        """
        endpoint = f"{self.base_url}/relations/{relation_id}/source-span"
        
        response = self.session.get(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def get_relation_section_image(self, relation_id: str, output_path: Optional[str] = None) -> bytes:
        """
        Get PDF page image with the relation's bounding box highlighted.
        
        Args:
            relation_id: Relation UID
            output_path: Optional path to save the image
            
        Returns:
            Image bytes (PNG format)
        """
        endpoint = f"{self.base_url}/relations/{relation_id}/section-image"
        
        response = self.session.get(endpoint)
        response.raise_for_status()
        
        image_bytes = response.content
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
        
        return image_bytes
    
    def get_predicate_frequency(self) -> Dict[str, Any]:
        """
        Get frequency distribution of all relationship types.
        
        Returns:
            Dictionary with predicate counts
        """
        endpoint = f"{self.base_url}/predicates/frequency"
        
        response = self.session.get(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the knowledge graph.
        
        Returns:
            Dictionary with graph statistics
        """
        endpoint = f"{self.base_url}/graph/stats"
        
        response = self.session.get(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API and database health status.
        
        Returns:
            Dictionary with health status
        """
        endpoint = f"{self.base_url}/health"
        
        response = self.session.get(endpoint)
        response.raise_for_status()
        
        return response.json()
