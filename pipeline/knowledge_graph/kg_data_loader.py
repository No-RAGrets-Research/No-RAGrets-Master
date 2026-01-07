#!/usr/bin/env python3
"""
kg_data_loader.py
-----------------
Knowledge Graph Data Loader - Loads extracted KG results into Dgraph database.

This module takes JSON output from the kg_gen_pipeline and loads it into a searchable
Dgraph graph database, creating nodes, relations, and paper metadata.

Usage:
    python kg_data_loader.py ../kg_gen_pipeline/your_kg_results_file.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from dgraph_manager import DgraphManager

class KGDataLoader:
    def __init__(self, dgraph_url: str = "http://localhost:8080", verbose: bool = False, force_update: bool = False):
        self.manager = DgraphManager(dgraph_url)
        self.verbose = verbose
        self.force_update = force_update
    
    @staticmethod
    def _escape_regex(text: str) -> str:
        """Escape special regex characters for safe DQL regexp matching."""
        special_chars = r'\.[]{}()*+?^$|'
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
        
    def create_paper(self, filename: str, title: str, summary: dict) -> str:
        """Create Paper only if it doesn't already exist."""
        # First check if paper already exists
        check_query = """
        query CheckPaper($filename: String!) {
          queryPaper(filter: { filename: { eq: $filename } }) {
            id
            title
          }
        }"""
        
        check_response = self.manager.query(check_query, {'filename': filename})
        
        if check_response.get('data', {}).get('queryPaper'):
            existing_paper = check_response['data']['queryPaper'][0]
            if self.force_update:
                # Delete existing paper and all its relations
                delete_mutation = """
                mutation DeletePaper($paperId: [ID!]) {
                  deletePaper(filter: { id: $paperId }) {
                    msg
                  }
                }"""
                self.manager.mutate(delete_mutation, {'paperId': [existing_paper['id']]})
                if self.verbose:
                    print(f"Deleted existing paper: {existing_paper['title']} for update")
            else:
                if self.verbose:
                    print(f"SKIPPED: Paper already exists: {existing_paper['title']} (ID: {existing_paper['id']})")
                return existing_paper['id']
        
        # Create new paper if it doesn't exist
        sections = list(summary.get('sections', {}).keys()) if summary.get('sections') else []
        
        mutation = """
        mutation CreatePaper($title: String!, $filename: String!,
                           $totalEntities: Int, $totalRelations: Int, $sections: [String]) {
          addPaper(input: [{
            title: $title,
            filename: $filename,
            total_entities: $totalEntities,
            total_relations: $totalRelations,
            sections: $sections
          }]) {
            paper { id }
          }
        }"""
        
        variables = {
            'title': title,
            'filename': filename,
            'totalEntities': summary.get('entities', 0),
            'totalRelations': summary.get('relations', 0),
            'sections': sections
        }
        
        response = self.manager.mutate(mutation, variables)
        
        if 'errors' in response:
            print(f"ERROR creating paper: {response['errors']}")
            return None
            
        paper_id = response['data']['addPaper']['paper'][0]['id']
        print(f"Created Paper: {title} (ID: {paper_id})")
        return paper_id
    
    def create_node(self, name: str, node_type: str = "biochemical_entity", namespace: str = "extracted") -> str:
        """
        Create Node only if it doesn't already exist.
        Uses case-insensitive matching to prevent duplicates like "Methanol" vs "methanol".
        """
        # Check if node already exists (case-insensitive)
        # Use DQL for case-insensitive matching via regexp
        import requests
        dql_query = f"""{{
          nodes(func: has(Node.name)) @filter(
            regexp(Node.name, /^{self._escape_regex(name)}$/i) AND 
            eq(Node.type, "{node_type}") AND 
            eq(Node.namespace, "{namespace}")
          ) {{
            uid
            Node.name
          }}
        }}"""
        
        try:
            response = requests.post(
                "http://localhost:8080/query",
                data=dql_query,
                headers={"Content-Type": "application/dql"}
            )
            result = response.json()
            existing_nodes = result.get('data', {}).get('nodes', [])
            
            if existing_nodes:
                # Reuse existing node (keeps original casing)
                existing_node = existing_nodes[0]
                if self.verbose:
                    existing_name = existing_node.get('Node.name', name)
                    if existing_name != name:
                        print(f"REUSED (case-insensitive): {name} → {existing_name} ({existing_node['uid']})")
                    else:
                        print(f"REUSED: Node already exists: {name}")
                return existing_node['uid']
        except Exception as e:
            # Fall back to exact match if DQL query fails
            if self.verbose:
                print(f"Warning: Case-insensitive check failed, using exact match: {e}")
            
            check_query = """
            query CheckNode($name: String!, $type: String, $namespace: String) {
              queryNode(filter: { 
                name: { eq: $name }, 
                type: { eq: $type }, 
                namespace: { eq: $namespace } 
              }) {
                id
                name
              }
            }"""
            
            check_response = self.manager.query(check_query, {
                'name': name,
                'type': node_type,
                'namespace': namespace
            })
            
            if check_response.get('data', {}).get('queryNode'):
                existing_node = check_response['data']['queryNode'][0]
                if self.verbose:
                    print(f"REUSED: Node already exists: {name}")
                return existing_node['id']
        
        # Create new node if it doesn't exist
        mutation = """
        mutation CreateNode($name: String!, $type: String, $namespace: String, $createdAt: String) {
          addNode(input: [{
            name: $name,
            type: $type,
            namespace: $namespace,
            created_at: $createdAt
          }]) {
            node { id }
          }
        }"""
        
        variables = {
            'name': name,
            'type': node_type,
            'namespace': namespace,
            'createdAt': datetime.now().isoformat()
        }
        
        response = self.manager.mutate(mutation, variables)
        
        if 'errors' in response:
            print(f"ERROR creating node '{name}': {response['errors']}")
            return None
            
        node_id = response['data']['addNode']['node'][0]['id']
        print(f"Created node: {name} (ID: {node_id})")
        return node_id
    
    def create_relation(self, subject_id: str, predicate: str, object_id: str,
                       section: str, pages: list, source_paper: str,
                       bbox_data: str = None, source_span: str = None, 
                       figure_id: str = None, table_id: str = None) -> bool:
        """Create a relationship between two nodes only if it doesn't exist."""
        # Check if relation already exists
        check_query = """
        query CheckRelation($subjectId: ID!, $predicate: String!, $objectId: ID!, $sourcePaper: String) {
          queryRelation(filter: { 
            and: [
              { subject: { id: [$subjectId] } },
              { predicate: { eq: $predicate } },
              { object: { id: [$objectId] } },
              { source_paper: { eq: $sourcePaper } }
            ]
          }) {
            id
          }
        }"""
        
        check_response = self.manager.query(check_query, {
            'subjectId': subject_id,
            'predicate': predicate,
            'objectId': object_id,
            'sourcePaper': source_paper
        })
        
        if check_response.get('data', {}).get('queryRelation'):
            existing_relation = check_response['data']['queryRelation'][0]
            if self.force_update:
                # Delete and recreate the relation with new data
                delete_mutation = """
                mutation DeleteRelation($relationId: [ID!]) {
                  deleteRelation(filter: { id: $relationId }) {
                    msg
                  }
                }"""
                self.manager.mutate(delete_mutation, {'relationId': [existing_relation['id']]})
                if self.verbose:
                    print(f"DELETED: Existing relation for update: {predicate}")
                # Continue to create new relation
            else:
                if self.verbose:
                    print(f"SKIPPED: Relation already exists: {predicate}")
                return True  # Relation already exists, skip creation
        
        # Create new relation if it doesn't exist
        mutation = """
        mutation CreateRelation($subjectId: ID!, $predicate: String!, $objectId: ID!,
                              $section: String, $pages: [Int], $sourcePaper: String,
                              $bboxData: String, $sourceSpan: String, $figureId: String, $tableId: String,
                              $createdAt: String, $extractionMethod: String) {
          addRelation(input: [{
            subject: { id: $subjectId },
            predicate: $predicate,
            object: { id: $objectId },
            section: $section,
            pages: $pages,
            source_paper: $sourcePaper,
            bbox_data: $bboxData,
            source_span: $sourceSpan,
            figure_id: $figureId,
            table_id: $tableId,
            created_at: $createdAt,
            extraction_method: $extractionMethod
          }]) {
            relation { id }
          }
        }"""
        
        variables = {
            'subjectId': subject_id,
            'predicate': predicate,
            'objectId': object_id,
            'section': section,
            'pages': pages,
            'sourcePaper': source_paper,
            'bboxData': bbox_data,
            'sourceSpan': source_span,
            'figureId': figure_id,
            'tableId': table_id,
            'createdAt': datetime.now().isoformat(),
            'extractionMethod': 'kg-gen'
        }
        
        if self.verbose and table_id:
            print(f"    DEBUG MUTATION: Creating relation with table_id={table_id}")
        
        response = self.manager.mutate(mutation, variables)
        
        if 'errors' in response:
            print(f"ERROR creating relation '{predicate}': {response['errors']}")
            return False
            
        return True
    
    def load_kg_results(self, results_file: str) -> bool:
        """Load KG extraction results into Dgraph."""
        results_path = Path(results_file)
        if not results_path.exists():
            print(f"ERROR: Results file not found: {results_file}")
            return False
        
        print(f"Loading {results_file} into Dgraph...")
        
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"ERROR reading JSON file: {e}")
            return False
        
        # Extract metadata
        summary = data.get('summary', {})
        chunks = data.get('chunks', [])
        
        # Derive paper info from filename
        # Remove common suffixes and clean up the filename
        clean_stem = results_path.stem
        
        # Remove various suffixes that may be present
        clean_stem = clean_stem.replace('_visual_triples_kg_format', '')
        clean_stem = clean_stem.replace('_visual_kg_format', '')
        
        # Remove .pdf_tables_only_kg_format and everything after it
        # The stem already removes .json, so we have something like "paper.pdf_tables_only_kg_format_timestamp"
        if '.pdf_tables_only_kg_format' in clean_stem:
            clean_stem = clean_stem.split('.pdf_tables_only_kg_format')[0]
            if not clean_stem.endswith('.pdf'):
                clean_stem += '.pdf'
        
        # Remove _kg_results_ and everything after it (including timestamp)
        elif '_kg_results_' in clean_stem:
            clean_stem = clean_stem.split('_kg_results_')[0]
        
        # Remove _tables_only_kg_format_ and everything after it
        elif '_tables_only_kg_format_' in clean_stem:
            clean_stem = clean_stem.split('_tables_only_kg_format_')[0]
        
        # Remove timestamp suffixes like _20251115
        import re
        clean_stem = re.sub(r'_\d{8}.*$', '', clean_stem)
        
        # Create filename - add .pdf only if it doesn't already end with it
        if clean_stem.endswith('.pdf'):
            filename = clean_stem
        else:
            filename = clean_stem + '.pdf'
        filename = filename.replace('Copy of ', '')
        
        title = filename.replace('.pdf', '').replace('_', ' ')
        
        # Create Paper object
        paper_id = self.create_paper(filename, title, summary)
        if not paper_id:
            return False
        
        # Track created entities to avoid duplicates within this session
        entity_cache = {}
        total_nodes = 0
        total_relations = 0
        skipped_nodes = 0
        skipped_relations = 0
        processed_relations = set()  # Track (subject, predicate, object) globally to avoid duplicates
        
        # Process chunks and relations
        for i, chunk in enumerate(chunks):
            section = chunk.get('section', 'Unknown Section')
            
            # Extract page numbers from provenance
            pages = []
            bbox_info = []
            
            for prov in chunk.get('provenance', []):
                for page_info in prov.get('pages', []):
                    page_no = page_info.get('page_no', 0)
                    if page_no:
                        pages.append(page_no)
                    
                    # Collect bounding box data
                    if 'bbox' in page_info:
                        bbox_info.append({
                            'page': page_no,
                            'bbox': page_info['bbox']
                        })
            
            # Remove duplicates and sort pages
            pages = sorted(list(set(pages)))
            bbox_json = json.dumps(bbox_info) if bbox_info else None
            
            # Process entities (create nodes)
            for entity in chunk.get('entities', []):
                if entity not in entity_cache:
                    node_id = self.create_node(entity, 'biochemical_entity', 'extracted')
                    if node_id:
                        entity_cache[entity] = node_id
                        total_nodes += 1
                        print(f"  Created node: {entity}")
            
            # Process relations
            for relation in chunk.get('relations', []):
                # Initialize variables
                source_span_data = None
                source_span_json = None
                
                # Handle both old format (list) and new format (dict with source_span)
                if isinstance(relation, list) and len(relation) >= 3:
                    subject, predicate, obj = relation[0], relation[1], relation[2]
                elif isinstance(relation, dict):
                    subject = relation.get('subject')
                    predicate = relation.get('predicate') 
                    obj = relation.get('object')
                    
                    # Extract source span data if available
                    source_span_data = relation.get('source_span')
                    source_span_json = json.dumps(source_span_data) if source_span_data else None
                else:
                    continue  # Skip malformed relations
                
                if not all([subject, predicate, obj]):
                    continue  # Skip incomplete relations
                
                # Skip relations with "none" as object (incomplete extractions)
                if obj.lower() == "none":
                    continue
                    
                # Create/get subject and object nodes if not already created
                if subject not in entity_cache:
                    subject_id = self.create_node(subject, 'biochemical_entity', 'extracted')
                    if subject_id:
                        entity_cache[subject] = subject_id
                        total_nodes += 1
                        print(f"  Created node: {subject}")
                
                if obj not in entity_cache:
                    object_id = self.create_node(obj, 'biochemical_entity', 'extracted')
                    if object_id:
                        entity_cache[obj] = object_id
                        total_nodes += 1
                        print(f"  Created node: {obj}")
                
                # Check if this relation already exists (avoid duplicates)
                relation_key = (subject, predicate, obj)
                if relation_key in processed_relations:
                    print(f"  Skipped duplicate: {subject} --[{predicate}]--> {obj}")
                    skipped_relations += 1
                    continue
                
                # Create relation if both nodes exist
                subject_id = entity_cache.get(subject)
                object_id = entity_cache.get(obj)
                
                if subject_id and object_id:
                    # Extract figure_id and table_id from source_span if available
                    figure_id = None
                    table_id = None
                    if source_span_data:
                        if source_span_data.get('span_type') == 'visual_figure':
                            figure_id = source_span_data.get('figure_id')
                        elif source_span_data.get('span_type') == 'visual_table':
                            table_id = source_span_data.get('table_id')
                    
                    success = self.create_relation(
                        subject_id, predicate, object_id,
                        section, pages, filename,
                        bbox_json, source_span_json, figure_id, table_id
                    )
                    if success:
                        total_relations += 1
                        processed_relations.add(relation_key)  # Mark as processed
                        span_info = f" (with span)" if source_span_json else ""
                        fig_info = f" [from {figure_id}]" if figure_id else ""
                        table_info = f" [from {table_id}]" if table_id else ""
                        print(f"  Created relation: {subject} --[{predicate}]--> {obj}{span_info}{fig_info}{table_info}")
        
        # Process all_relations section (includes cross-chunk relations)
        all_relations = data.get('all_relations', [])
        if all_relations:
            print(f"\nProcessing {len(all_relations)} relations from all_relations section...")
            # Note: Using global processed_relations set to check for duplicates from chunks
            
            for relation in all_relations:
                # Initialize variables
                source_span_data = None
                source_span_json = None
                
                # Handle both old format (list) and new format (dict with source_span)
                if isinstance(relation, list) and len(relation) >= 3:
                    subject, predicate, obj = relation[0], relation[1], relation[2]
                elif isinstance(relation, dict):
                    subject = relation.get('subject')
                    predicate = relation.get('predicate') 
                    obj = relation.get('object')
                    
                    # Extract source span data if available
                    source_span_data = relation.get('source_span')
                    source_span_json = json.dumps(source_span_data) if source_span_data else None
                else:
                    continue  # Skip malformed relations
                
                if not all([subject, predicate, obj]):
                    continue  # Skip incomplete relations
                
                # Skip relations with "none" as object (incomplete extractions)
                if obj.lower() == "none":
                    continue
                
                # Check if relation already exists from chunks (avoid duplicates)
                relation_key = (subject, predicate, obj)
                if relation_key in processed_relations:
                    print(f"  Skipped duplicate from all_relations: {subject} --[{predicate}]--> {obj}")
                    skipped_relations += 1
                    continue
                    
                # Create/get subject and object nodes if not already created
                if subject not in entity_cache:
                    subject_id = self.create_node(subject, 'biochemical_entity', 'extracted')
                    if subject_id:
                        entity_cache[subject] = subject_id
                        total_nodes += 1
                        print(f"  Created node: {subject}")
                
                if obj not in entity_cache:
                    object_id = self.create_node(obj, 'biochemical_entity', 'extracted')
                    if object_id:
                        entity_cache[obj] = object_id
                        total_nodes += 1
                        print(f"  Created node: {obj}")
                
                # Create relation if both nodes exist
                subject_id = entity_cache.get(subject)
                object_id = entity_cache.get(obj)
                
                if subject_id and object_id:
                    # Determine section and pages from source_span if available
                    section = "Cross-chunk Analysis"  # Default for all_relations
                    pages = []
                    bbox_json = None
                    figure_id = None
                    table_id = None
                    
                    if source_span_data:
                        # Extract section and page info from source_span
                        if source_span_data.get('span_type') == 'cross_chunk':
                            subject_chunk = source_span_data.get('subject_chunk', {})
                            object_chunk = source_span_data.get('object_chunk', {})
                            section = f"Cross-chunk: {subject_chunk.get('section', 'Unknown')} <-> {object_chunk.get('section', 'Unknown')}"
                        elif source_span_data.get('span_type') == 'visual_figure':
                            figure_id = source_span_data.get('figure_id')
                            section = f"Visual Analysis: Figure {figure_id or 'Unknown'}"
                            if 'page_number' in source_span_data:
                                pages = [source_span_data['page_number']]
                        elif source_span_data.get('span_type') == 'visual_table':
                            table_id = source_span_data.get('table_id')
                            section = f"Visual Analysis: Table {table_id or 'Unknown'}"
                            if 'page_number' in source_span_data:
                                pages = [source_span_data['page_number']]
                    
                    success = self.create_relation(
                        subject_id, predicate, object_id,
                        section, pages, filename,
                        bbox_json, source_span_json, figure_id, table_id
                    )
                    if success:
                        total_relations += 1
                        processed_relations.add(relation_key)  # Mark as processed
                        span_info = f" (with span)" if source_span_json else ""
                        fig_info = f" [from {figure_id}]" if figure_id else ""
                        table_info = f" [from {table_id}]" if table_id else ""
                        if self.verbose:
                            print(f"  DEBUG: span_type={source_span_data.get('span_type') if source_span_data else None}, figure_id={figure_id}, table_id={table_id}")
                        print(f"  Created all_relations: {subject} --[{predicate}]--> {obj}{span_info}{fig_info}{table_info}")
        
        print(f"\nSUCCESS: Loaded {total_nodes} nodes and {total_relations} relations")
        if skipped_relations > 0:
            print(f"Skipped {skipped_relations} duplicate relations (preferring chunk relations with metadata)")
        print("Note: Existing data was preserved - no duplicates created")
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Load KG results into Dgraph database")
    parser.add_argument("results_file", help="KG results JSON file to load")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show what items are being skipped/updated")
    parser.add_argument("--force-update", action="store_true",
                       help="Overwrite existing papers/nodes/relations with new data")
    parser.add_argument("--dgraph-url", default="http://localhost:8080",
                       help="Dgraph endpoint URL")
    
    args = parser.parse_args()
    
    # Check if Dgraph is running
    loader = KGDataLoader(args.dgraph_url, args.verbose, args.force_update)
    if not loader.manager.health_check():
        print("ERROR: Dgraph is not running. Start it with: docker compose up -d")
        return 1
    
    if args.force_update:
        print("WARNING: Force update mode - existing data will be overwritten!")
        confirm = input("Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return 1
    
    # Load the data
    success = loader.load_kg_results(args.results_file)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
