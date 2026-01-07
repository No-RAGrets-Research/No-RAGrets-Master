#!/usr/bin/env python3
"""
Backfill Script: Add docling_ref to Existing Relations
======================================================
This script updates existing relations in the knowledge graph to include
the docling_ref field in their source_span data.

It works by:
1. Fetching all relations from Dgraph
2. Loading appropriate source files based on relation type:
   - Text relations: text_chunks/*.jsonl (match by chunk_id)
   - Figure relations: visual_triples/*.json (match by figure_id)
   - Table relations: docling_json/*.json (match by table_id)
3. Updating source_span JSON to include docling_ref
4. Saving updated relations back to Dgraph

This avoids re-running the entire extraction pipeline.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from dgraph_manager import DgraphManager

class DoclingRefBackfiller:
    """Backfill docling_ref into existing relation source spans."""
    
    def __init__(self, 
                 chunks_dir: str = "../kg_gen_pipeline/output/text_chunks",
                 visual_dir: str = "../kg_gen_pipeline/output/visual_triples",
                 docling_dir: str = "../kg_gen_pipeline/output/docling_json"):
        self.chunks_dir = Path(chunks_dir)
        self.visual_dir = Path(visual_dir)
        self.docling_dir = Path(docling_dir)
        self.dgraph = DgraphManager()
        
        # Caches
        self.chunk_cache = {}  # Cache loaded text chunks by paper name
        self.visual_cache = {}  # Cache loaded visual triples by paper name
        self.docling_cache = {}  # Cache loaded docling JSON by paper name
    
    def load_docling_json(self, paper_name: str) -> dict:
        """Load Docling JSON for a paper."""
        if paper_name in self.docling_cache:
            return self.docling_cache[paper_name]
        
        # Normalize paper name: remove .pdf extension if present
        normalized_name = paper_name.replace('.pdf', '')
        
        # Find the docling JSON file for this paper
        docling_file = self.docling_dir / f"{normalized_name}.json"
        
        if not docling_file.exists():
            print(f"  Warning: Docling JSON not found: {docling_file}")
            return {}
        
        try:
            with open(docling_file, 'r') as f:
                data = json.load(f)
            self.docling_cache[paper_name] = data
            print(f"  Loaded Docling JSON: {docling_file.name}")
            return data
        except Exception as e:
            print(f"  Error loading Docling JSON {docling_file}: {e}")
            return {}
    
    def get_table_docling_ref(self, paper_name: str, table_id: str) -> Optional[str]:
        """
        Get docling_ref for a table by matching table_id to Docling JSON.
        table_id format: "page26_table0" -> maps to tables array index
        """
        docling_data = self.load_docling_json(paper_name)
        tables = docling_data.get("tables", [])
        
        if not tables:
            return None
        
        # Extract table index from table_id (e.g., "page26_table0" -> 0)
        try:
            # table_id format can be "page26_table0" or just "table0"
            if "_table" in table_id:
                table_idx = int(table_id.split("_table")[-1])
            else:
                table_idx = int(table_id.replace("table", ""))
            
            if 0 <= table_idx < len(tables):
                table = tables[table_idx]
                return table.get("self_ref", f"#/tables/{table_idx}")
        except (ValueError, IndexError) as e:
            print(f"  Warning: Could not parse table_id '{table_id}': {e}")
        
        return None
    
    def load_visual_triples_for_paper(self, paper_name: str) -> Dict[str, dict]:
        """
        Load visual triples for a paper and index by figure_id.
        
        Returns:
            Dict mapping figure_id -> chunk data (including provenance)
        """
        if paper_name in self.visual_cache:
            return self.visual_cache[paper_name]
        
        # Normalize paper name: remove .pdf extension if present
        normalized_name = paper_name.replace('.pdf', '')
        
        # Find visual triples file - format: "Copy of {paper_name}_visual_kg_format_*.json"
        visual_files = list(self.visual_dir.glob(f"Copy of {normalized_name}_visual_kg_format_*.json"))
        
        if not visual_files:
            print(f"  Warning: Visual triples file not found for: {paper_name}")
            return {}
        
        # Use the first matching file (should only be one)
        visual_file = visual_files[0]
        
        try:
            with open(visual_file, 'r') as f:
                data = json.load(f)
            
            # Index chunks by figure_id
            figures_by_id = {}
            for chunk in data.get("chunks", []):
                figure_id = chunk.get("figure_id")
                if figure_id:
                    figures_by_id[figure_id] = chunk
            
            self.visual_cache[paper_name] = figures_by_id
            print(f"  Loaded {len(figures_by_id)} figures from {visual_file.name}")
            return figures_by_id
            
        except Exception as e:
            print(f"  Error loading visual triples {visual_file}: {e}")
            return {}
        
    def load_chunks_for_paper(self, paper_name: str) -> Dict[int, dict]:
        """
        Load all chunks for a paper and index by chunk_id.
        
        Returns:
            Dict mapping chunk_id -> chunk data (including provenance)
        """
        if paper_name in self.chunk_cache:
            return self.chunk_cache[paper_name]
        
        # Normalize paper name: remove .pdf extension if present
        normalized_name = paper_name.replace('.pdf', '')
        
        # Find the chunks file for this paper
        # Format: "Copy of Paper Name.texts_chunks.jsonl"
        chunks_file = self.chunks_dir / f"Copy of {normalized_name}.texts_chunks.jsonl"
        
        if not chunks_file.exists():
            print(f"  Warning: Chunks file not found: {chunks_file}")
            return {}
        
        chunks_by_id = {}
        with open(chunks_file, 'r') as f:
            for idx, line in enumerate(f):
                try:
                    chunk = json.loads(line)
                    chunks_by_id[idx] = chunk
                except json.JSONDecodeError as e:
                    print(f"  Warning: Error parsing chunk {idx} in {chunks_file}: {e}")
        
        self.chunk_cache[paper_name] = chunks_by_id
        print(f"  Loaded {len(chunks_by_id)} chunks from {chunks_file.name}")
        return chunks_by_id
    
    def get_docling_ref_from_chunk(self, chunk: dict) -> Optional[str]:
        """Extract docling_ref from chunk provenance."""
        provenance = chunk.get("provenance", [])
        if provenance and len(provenance) > 0:
            return provenance[0].get("docling_ref")
        return None
    
    def fetch_all_relations(self):
        """Fetch all relations from Dgraph."""
        print("Fetching all relations from Dgraph...")
        
        query = """
        {
            queryRelation {
                id
                subject { name }
                predicate
                object { name }
                source_span
                source_paper
            }
        }
        """
        
        response = self.dgraph.query(query)
        
        if "errors" in response:
            print(f"Error fetching relations: {response['errors']}")
            return []
        
        relations = response.get("data", {}).get("queryRelation", [])
        print(f"Found {len(relations)} relations")
        return relations
    
    def update_relation_source_span(self, relation_id: str, updated_source_span: str) -> bool:
        """Update a single relation's source_span in Dgraph."""
        # Use GraphQL mutation format
        mutation = """
        mutation updateRelationSourceSpan($id: ID!, $source_span: String!) {
            updateRelation(input: {filter: {id: [$id]}, set: {source_span: $source_span}}) {
                numUids
            }
        }
        """
        
        variables = {
            "id": relation_id,
            "source_span": updated_source_span
        }
        
        try:
            result = self.dgraph.mutate(mutation, variables)
            # Check if the update was successful
            num_uids = result.get("data", {}).get("updateRelation", {}).get("numUids", 0)
            return num_uids > 0
        except Exception as e:
            print(f"  Error updating relation {relation_id}: {e}")
            return False
    
    def backfill(self):
        """Main backfill process."""
        print("=" * 70)
        print("DOCLING_REF BACKFILL SCRIPT")
        print("=" * 70)
        
        # Fetch all relations
        relations = self.fetch_all_relations()
        
        if not relations:
            print("No relations found. Exiting.")
            return
        
        # Statistics
        total_relations = len(relations)
        updated_count = 0
        updated_text = 0
        updated_figure = 0
        updated_table = 0
        skipped_no_span = 0
        skipped_has_ref = 0
        skipped_no_chunk_id = 0
        skipped_no_paper = 0
        skipped_unknown_type = 0
        error_count = 0
        
        print(f"\nProcessing {total_relations} relations...\n")
        
        for i, relation in enumerate(relations, 1):
            relation_id = relation.get("id")
            source_paper = relation.get("source_paper")
            source_span_str = relation.get("source_span")
            
            # Progress indicator
            if i % 100 == 0:
                print(f"Progress: {i}/{total_relations} relations processed...")
            
            # Skip if no source_span
            if not source_span_str:
                skipped_no_span += 1
                continue
            
            # Skip if no source_paper
            if not source_paper:
                skipped_no_paper += 1
                continue
            
            try:
                # Parse source_span JSON
                source_span = json.loads(source_span_str)
                
                # Skip if already has docling_ref (check top level for regular, nested for cross_chunk)
                span_type = source_span.get("span_type", "unknown")
                
                if span_type == "cross_chunk":
                    # Check if both subject and object chunks have docling_ref
                    subject_has_ref = source_span.get("subject_chunk", {}).get("docling_ref")
                    object_has_ref = source_span.get("object_chunk", {}).get("docling_ref")
                    if subject_has_ref and object_has_ref:
                        skipped_has_ref += 1
                        continue
                else:
                    # Check top-level docling_ref
                    if source_span.get("docling_ref"):
                        skipped_has_ref += 1
                        continue
                
                # Route to appropriate handler based on span_type
                docling_ref = None
                updated = False
                
                if span_type == "cross_chunk":
                    # TEXT: Cross-chunk relations
                    updated = False
                    
                    subject_chunk_data = source_span.get("subject_chunk", {})
                    object_chunk_data = source_span.get("object_chunk", {})
                    
                    subject_chunk_id = subject_chunk_data.get("chunk_id")
                    object_chunk_id = object_chunk_data.get("chunk_id")
                    
                    if subject_chunk_id is not None and object_chunk_id is not None:
                        chunks = self.load_chunks_for_paper(source_paper)
                        
                        if subject_chunk_id in chunks:
                            subject_ref = self.get_docling_ref_from_chunk(chunks[subject_chunk_id])
                            if subject_ref:
                                subject_chunk_data["docling_ref"] = subject_ref
                                updated = True
                        
                        if object_chunk_id in chunks:
                            object_ref = self.get_docling_ref_from_chunk(chunks[object_chunk_id])
                            if object_ref:
                                object_chunk_data["docling_ref"] = object_ref
                                updated = True
                        
                        if updated:
                            updated_span_str = json.dumps(source_span)
                            if self.update_relation_source_span(relation_id, updated_span_str):
                                updated_count += 1
                                updated_text += 1
                            else:
                                error_count += 1
                    else:
                        skipped_no_chunk_id += 1
                
                elif span_type == "visual_figure":
                    # FIGURE: Get docling_ref from visual triples
                    figure_id = source_span.get("figure_id")
                    
                    if not figure_id:
                        skipped_no_chunk_id += 1
                        continue
                    
                    figures = self.load_visual_triples_for_paper(source_paper)
                    
                    if figure_id in figures:
                        figure_data = figures[figure_id]
                        provenance = figure_data.get("provenance", [])
                        
                        if provenance and len(provenance) > 0:
                            docling_ref = provenance[0].get("docling_ref")
                            
                            if docling_ref:
                                source_span["docling_ref"] = docling_ref
                                updated_span_str = json.dumps(source_span)
                                
                                if self.update_relation_source_span(relation_id, updated_span_str):
                                    updated_count += 1
                                    updated_figure += 1
                                    updated = True
                                else:
                                    error_count += 1
                            else:
                                print(f"  Warning: No docling_ref in figure provenance for {figure_id}")
                                error_count += 1
                    else:
                        print(f"  Warning: Figure {figure_id} not found for paper '{source_paper}'")
                        error_count += 1
                
                elif span_type == "visual_table":
                    # TABLE: Get docling_ref from Docling JSON by table_id
                    table_id = source_span.get("table_id")
                    
                    if not table_id:
                        skipped_no_chunk_id += 1
                        continue
                    
                    docling_ref = self.get_table_docling_ref(source_paper, table_id)
                    
                    if docling_ref:
                        source_span["docling_ref"] = docling_ref
                        updated_span_str = json.dumps(source_span)
                        
                        if self.update_relation_source_span(relation_id, updated_span_str):
                            updated_count += 1
                            updated_table += 1
                            updated = True
                        else:
                            error_count += 1
                    else:
                        print(f"  Warning: Could not find docling_ref for table {table_id} in '{source_paper}'")
                        error_count += 1
                
                elif span_type in ["single_sentence", "multi_sentence", "chunk_fallback"]:
                    # TEXT: Regular text relations
                    chunk_id = source_span.get("chunk_id")
                    
                    if chunk_id is None:
                        skipped_no_chunk_id += 1
                        continue
                    
                    chunks = self.load_chunks_for_paper(source_paper)
                    
                    if chunk_id not in chunks:
                        print(f"  Warning: Chunk {chunk_id} not found for paper '{source_paper}'")
                        error_count += 1
                        continue
                    
                    docling_ref = self.get_docling_ref_from_chunk(chunks[chunk_id])
                    
                    if not docling_ref:
                        print(f"  Warning: No docling_ref in chunk {chunk_id} for paper '{source_paper}'")
                        error_count += 1
                        continue
                    
                    source_span["docling_ref"] = docling_ref
                    updated_span_str = json.dumps(source_span)
                    
                    if self.update_relation_source_span(relation_id, updated_span_str):
                        updated_count += 1
                        updated_text += 1
                        updated = True
                    else:
                        error_count += 1
                
                else:
                    # Unknown span type
                    skipped_unknown_type += 1
                    continue
                
            except json.JSONDecodeError as e:
                print(f"  Error parsing source_span for relation {relation_id}: {e}")
                error_count += 1
                continue
            except Exception as e:
                print(f"  Unexpected error processing relation {relation_id}: {e}")
                error_count += 1
                continue
        
        # Print summary
        print("\n" + "=" * 70)
        print("BACKFILL COMPLETE")
        print("=" * 70)
        print(f"Total relations:             {total_relations}")
        print(f"Successfully updated:        {updated_count}")
        print(f"  - Text relations:          {updated_text}")
        print(f"  - Figure relations:        {updated_figure}")
        print(f"  - Table relations:         {updated_table}")
        print(f"Skipped (no source_span):    {skipped_no_span}")
        print(f"Skipped (has docling_ref):   {skipped_has_ref}")
        print(f"Skipped (no chunk/fig/tbl):  {skipped_no_chunk_id}")
        print(f"Skipped (no source_paper):   {skipped_no_paper}")
        print(f"Skipped (unknown type):      {skipped_unknown_type}")
        print(f"Errors:                      {error_count}")
        print("=" * 70)
        
        if updated_count > 0:
            print(f"\n✅ Successfully backfilled {updated_count} relations with docling_ref!")
            print(f"   Text: {updated_text} | Figures: {updated_figure} | Tables: {updated_table}")
        else:
            print("\n⚠️  No relations were updated. Check the warnings above.")


def main():
    """Run the backfill script."""
    import sys
    
    # Check if chunks directory exists
    chunks_dir = "../kg_gen_pipeline/output/text_chunks"
    if not Path(chunks_dir).exists():
        print(f"Error: Chunks directory not found: {chunks_dir}")
        print("Please ensure the text chunks have been generated first.")
        sys.exit(1)
    
    # Run backfill
    backfiller = DoclingRefBackfiller(chunks_dir=chunks_dir)
    backfiller.backfill()


if __name__ == "__main__":
    main()
