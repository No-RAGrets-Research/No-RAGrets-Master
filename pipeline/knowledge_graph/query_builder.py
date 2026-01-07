#!/usr/bin/env python3
"""
GraphQL Query Builder
====================
Builds GraphQL queries for the Knowledge Graph API endpoints.
"""

from typing import Optional, Dict, Any, List

class GraphQLQueryBuilder:
    """Builds GraphQL queries for various API endpoints."""
    
    def build_entity_search(self, search_term: str, type_filter: Optional[str] = None, 
                           namespace: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Build query to search for entities."""
        filters = [f'name: {{ anyofterms: "{search_term}" }}']
        
        if type_filter:
            filters.append(f'type: {{ eq: "{type_filter}" }}')
        if namespace:
            filters.append(f'namespace: {{ eq: "{namespace}" }}')
        
        filter_str = " and: [" + ", ".join(["{" + f + "}" for f in filters]) + "]" if len(filters) > 1 else filters[0]
        
        query = f"""
        query SearchEntities {{
          queryNode(filter: {{ {filter_str} }}, first: {limit}) {{
            id
            name
            type
            namespace
            created_at
          }}
        }}"""
        
        return {"query": query, "variables": {}}
    
    def build_relation_search(self, predicate: Optional[str] = None, subject: Optional[str] = None,
                             object_name: Optional[str] = None, section: Optional[str] = None, 
                             limit: int = 20) -> Dict[str, Any]:
        """Build query to search for relations."""
        filters = []
        
        if predicate:
            filters.append(f'predicate: {{ anyofterms: "{predicate}" }}')
        if section:
            filters.append(f'section: {{ anyofterms: "{section}" }}')
        if subject:
            filters.append(f'subject: {{ name: {{ anyofterms: "{subject}" }} }}')
        if object_name:
            filters.append(f'object: {{ name: {{ anyofterms: "{object_name}" }} }}')
        
        filter_str = ""
        if filters:
            if len(filters) > 1:
                filter_str = f"filter: {{ and: [{', '.join(['{'+f+'}' for f in filters])}] }},"
            else:
                filter_str = f"filter: {{ {filters[0]} }},"
        
        query = f"""
        query SearchRelations {{
          queryRelation({filter_str} first: {limit}) {{
            id
            predicate
            section
            pages
            source_paper
            confidence
            subject {{
              id
              name
              type
              namespace
            }}
            object {{
              id
              name
              type
              namespace
            }}
          }}
        }}"""
        
        return {"query": query, "variables": {}}
    
    def build_entity_connections(self, entity_name: str, direction: str = "both", 
                                max_relations: int = 50) -> Dict[str, Any]:
        """Build query to get entity connections."""
        outgoing_field = f"outgoing(first: {max_relations}) {{ id predicate section pages source_paper confidence figure_id table_id subject {{ id name type namespace }} object {{ id name type namespace }} }}" if direction in ["outgoing", "both"] else ""
        incoming_field = f"incoming(first: {max_relations}) {{ id predicate section pages source_paper confidence figure_id table_id subject {{ id name type namespace }} object {{ id name type namespace }} }}" if direction in ["incoming", "both"] else ""
        
        query = f"""
        query EntityConnections {{
          queryNode(filter: {{ name: {{ eq: "{entity_name}" }} }}) {{
            id
            name
            type
            namespace
            {outgoing_field}
            {incoming_field}
          }}
        }}"""
        
        return {"query": query, "variables": {}}
    
    def build_papers_list(self) -> Dict[str, Any]:
        """Build query to list all papers."""
        query = """
        query ListPapers {
          queryPaper {
            id
            title
            filename
            processed_at
            total_entities
            total_relations
            sections
          }
        }"""
        
        return {"query": query, "variables": {}}
    
    def build_paper_entities(self, paper_id: str, section: Optional[str] = None, 
                           limit: int = 100) -> Dict[str, Any]:
        """Build query to get entities from a specific paper."""
        section_filter = f', section: {{ eq: "{section}" }}' if section else ""
        
        query = f"""
        query PaperEntities {{
          queryRelation(filter: {{ source_paper: {{ eq: "{paper_id}" }}{section_filter} }}, first: {limit}) {{
            subject {{
              id
              name
              type
              namespace
            }}
            object {{
              id
              name
              type
              namespace
            }}
          }}
        }}"""
        
        return {"query": query, "variables": {}}
    
    # def build_relation_provenance(self, relation_id: str) -> Dict[str, Any]:
    #     """Build query to get relation provenance."""
    #     query = f"""
    #     query RelationProvenance {{
    #       queryRelation(filter: {{ id: {{ eq: "{relation_id}" }} }}) {{
    #         id
    #         section
    #         pages
    #         bbox_data
    #         source_paper
    #         extraction_method
    #       }}
    #     }}"""
        
    #     return {"query": query, "variables": {}}

    def build_relation_provenance(self) -> Dict[str, Any]:
        """Fetch ALL relations; filtering is done in Python because GraphQL can't filter by UID."""
        query = """
        {
          queryRelation {
            id
            section
            pages
            bbox_data
            source_paper
            extraction_method
          }
        }
        """
        return {"query": query, "variables": {}}


    
    def build_graph_stats(self) -> Dict[str, Any]:
        """Build query to get graph statistics."""
        query = """
        query GraphStats {
          allNodes: queryNode {
            id
          }
          allRelations: queryRelation {
            id
            predicate
          }
          allPapers: queryPaper {
            id
          }
        }"""
        
        return {"query": query, "variables": {}}
    
    def build_most_connected_entities(self, limit: int = 10) -> Dict[str, Any]:
        """Build query to get most connected entities."""
        query = f"""
        query MostConnectedEntities {{
          queryNode(first: {limit * 3}) {{
            id
            name
            type
            namespace
            outgoing {{
              id
            }}
            incoming {{
              id
            }}
          }}
        }}"""
        
        return {"query": query, "variables": {}}
    
    def build_predicate_frequency(self) -> Dict[str, Any]:
        """Build query to get predicate frequency."""
        query = """
        query PredicateFrequency {
          queryRelation {
            predicate
          }
        }"""
        
        return {"query": query, "variables": {}}
    
    def build_path_query(self, source: str, target: str, max_depth: int = 3) -> Dict[str, Any]:
        """Build query for path finding (placeholder - would need recursive logic)."""
        # This would need more sophisticated path-finding algorithm
        query = f"""
        query FindPath {{
          source: queryNode(filter: {{ name: {{ eq: "{source}" }} }}) {{
            id
            name
          }}
          target: queryNode(filter: {{ name: {{ eq: "{target}" }} }}) {{
            id  
            name
          }}
        }}"""
        
        return {"query": query, "variables": {}}