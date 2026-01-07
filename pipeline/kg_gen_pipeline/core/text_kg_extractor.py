#!/usr/bin/env python3
"""
chunk_kg_extractor_texts_based.py
---------------------------------
Runs KG-GEN on Docling-derived text chunks that preserve provenance.

Input:  *.texts_chunks.jsonl  (from text_chunker.py)
Output: _kg_results_*.json, _kg_summary_*.json, optional HTML viz
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from kg_gen import KGGen
import re


class ChunkKGExtractor:
    def __init__(self, model="ollama_chat/mistral:7b", api_base="http://localhost:11434"):
        print(f"Initializing KGGen with model: {model}", flush=True)
        self.kg = KGGen(model=model, temperature=0.0, api_base=api_base)
        print(f"KGGen initialized successfully", flush=True)

    # --------------------------------------------------------------
    # NEW: Relation-to-Span Mapping Methods
    # --------------------------------------------------------------
    def find_sentences_containing_entity(self, entity_name, sentences):
        """Find which sentences contain mentions of an entity."""
        if not entity_name or not sentences:
            return []
        
        matching_sentences = []
        entity_lower = entity_name.lower()
        
        for sentence in sentences:
            sentence_text = sentence["text"].lower()
            
            # Simple string matching (can be enhanced with fuzzy matching later)
            if entity_lower in sentence_text:
                matching_sentences.append(sentence)
        
        return matching_sentences

    def find_entity_positions_in_sentence(self, entity_name, sentence_text):
        """Find character positions where an entity is mentioned in a sentence."""
        if not entity_name or not sentence_text:
            return []
        
        positions = []
        entity_lower = entity_name.lower()
        text_lower = sentence_text.lower()
        
        # Find all occurrences using word boundaries
        pattern = r'\b' + re.escape(entity_lower) + r'\b'
        
        for match in re.finditer(pattern, text_lower):
            positions.append({
                "start": match.start(),
                "end": match.end(),
                "matched_text": sentence_text[match.start():match.end()]
            })
        
        return positions

    def calculate_relation_span(self, relation, chunk_sentences, chunk_id, chunk_provenance=None):
        """
        Calculate the span (sentence range) for a relation within a chunk.
        
        Args:
            relation: The relation object with subject, predicate, object
            chunk_sentences: List of sentences with offset information
            chunk_id: ID of the current chunk
            chunk_provenance: Optional provenance data containing docling_ref
            
        Returns:
            Enhanced relation with source span information
        """
        # Extract subject and object from relation
        subject = str(relation.get("subject", "")).strip()
        object_entity = str(relation.get("object", "")).strip()
        predicate = str(relation.get("predicate", "")).strip()
        
        if not subject or not object_entity:
            # Can't map relation without both subject and object
            return None
        
        # Find sentences containing subject and object
        subject_sentences = self.find_sentences_containing_entity(subject, chunk_sentences)
        object_sentences = self.find_sentences_containing_entity(object_entity, chunk_sentences)
        
        if not subject_sentences and not object_sentences:
            # Extract docling_ref from chunk provenance if available
            docling_ref = None
            if chunk_provenance and len(chunk_provenance) > 0:
                first_prov = chunk_provenance[0]
                docling_ref = first_prov.get("docling_ref")
            
            # Relation not found in any sentences (fallback to chunk level)
            return {
                **relation,
                "source_span": {
                    "chunk_id": chunk_id,
                    "span_type": "chunk_fallback",
                    "sentence_start": None,
                    "sentence_end": None,
                    "text_evidence": "Relation found in chunk but not mapped to specific sentences",
                    "confidence": 0.3,
                    "docling_ref": docling_ref
                }
            }
        
        # Combine all relevant sentences
        all_relevant_sentences = subject_sentences + object_sentences
        
        # Remove duplicates and sort by sentence ID
        unique_sentences = {s["sentence_id"]: s for s in all_relevant_sentences}
        sorted_sentences = sorted(unique_sentences.values(), key=lambda x: x["sentence_id"])
        
        if not sorted_sentences:
            return None
        
        # Calculate span
        span_start = sorted_sentences[0]["sentence_id"]
        span_end = sorted_sentences[-1]["sentence_id"]
        span_type = "single_sentence" if span_start == span_end else "multi_sentence"
        
        # Create text evidence (combine all relevant sentences)
        if span_type == "single_sentence":
            text_evidence = sorted_sentences[0]["text"]
        else:
            text_evidence = " ".join(s["text"] for s in sorted_sentences)
        
        # Calculate document offsets
        document_start = sorted_sentences[0]["document_start"]
        document_end = sorted_sentences[-1]["document_end"]
        
        # Find specific entity positions within the sentences
        subject_positions = []
        object_positions = []
        
        for sentence in sorted_sentences:
            subject_pos = self.find_entity_positions_in_sentence(subject, sentence["text"])
            object_pos = self.find_entity_positions_in_sentence(object_entity, sentence["text"])
            
            # Adjust positions to be relative to the span
            base_offset = sentence["document_start"] - document_start
            for pos in subject_pos:
                subject_positions.append({
                    "start": pos["start"] + base_offset,
                    "end": pos["end"] + base_offset,
                    "sentence_id": sentence["sentence_id"],
                    "matched_text": pos["matched_text"]
                })
            
            for pos in object_pos:
                object_positions.append({
                    "start": pos["start"] + base_offset,
                    "end": pos["end"] + base_offset,
                    "sentence_id": sentence["sentence_id"],
                    "matched_text": pos["matched_text"]
                })
        
        # Calculate confidence based on entity co-occurrence
        confidence = 0.9 if span_type == "single_sentence" else 0.7
        if subject_positions and object_positions:
            confidence += 0.1
        
        # Extract docling_ref from chunk provenance if available
        docling_ref = None
        if chunk_provenance and len(chunk_provenance) > 0:
            # Get the first provenance entry's docling_ref
            # In most cases, there will be one main provenance entry per chunk
            first_prov = chunk_provenance[0]
            docling_ref = first_prov.get("docling_ref")
        
        return {
            **relation,
            "source_span": {
                "chunk_id": chunk_id,
                "span_type": span_type,
                "sentence_start": span_start,
                "sentence_end": span_end,
                "text_evidence": text_evidence,
                "document_offsets": {
                    "start": document_start,
                    "end": document_end
                },
                "subject_positions": subject_positions,
                "object_positions": object_positions,
                "confidence": confidence,
                "docling_ref": docling_ref
            }
        }

    # --------------------------------------------------------------
    # NEW: Cross-Chunk Relation Detection Methods
    # --------------------------------------------------------------
    def find_entity_in_chunks(self, entity_name, all_chunk_results):
        """Find all chunks that contain mentions of a specific entity."""
        entity_chunks = []
        entity_lower = entity_name.lower()
        
        for chunk_result in all_chunk_results:
            chunk_id = chunk_result["index"]
            
            # Check if entity appears in any of the chunk's entities
            chunk_entities = [str(e).lower() for e in chunk_result.get("entities", [])]
            if entity_lower in chunk_entities:
                entity_chunks.append({
                    "chunk_id": chunk_id,
                    "chunk_result": chunk_result
                })
                continue
            
            # Also check if entity appears in relation subjects/objects
            for relation in chunk_result.get("relations", []):
                subject = str(relation.get("subject", "")).lower()
                object_entity = str(relation.get("object", "")).lower()
                
                if entity_lower in [subject, object_entity]:
                    entity_chunks.append({
                        "chunk_id": chunk_id,
                        "chunk_result": chunk_result
                    })
                    break
        
        return entity_chunks

    def detect_cross_chunk_relations(self, all_chunk_results):
        """
        Detect potential relations that span across multiple chunks.
        
        Enhanced approach:
        1. Look for entities that appear in multiple chunks
        2. Find cases where subject in chunk A could relate to object in chunk B
        3. Use co-occurrence patterns and semantic similarity to suggest relations
        """
        cross_chunk_relations = []
        
        # Build comprehensive entity-to-chunks mapping
        entity_chunk_map = {}
        all_relations = []
        
        for chunk_result in all_chunk_results:
            chunk_id = chunk_result["index"]
            
            # Collect entities from this chunk with their context
            chunk_entities = set()
            
            # Add explicit entities
            for entity in chunk_result.get("entities", []):
                entity_str = str(entity).lower().strip()
                if entity_str:
                    chunk_entities.add(entity_str)
            
            # Add entities from relations
            for relation in chunk_result.get("relations", []):
                all_relations.append((chunk_id, relation))
                
                subject = str(relation.get("subject", "")).strip()
                object_entity = str(relation.get("object", "")).strip()
                
                if subject:
                    chunk_entities.add(subject.lower())
                if object_entity:
                    chunk_entities.add(object_entity.lower())
            
            # Update entity mapping
            for entity in chunk_entities:
                if entity not in entity_chunk_map:
                    entity_chunk_map[entity] = []
                entity_chunk_map[entity].append({
                    "chunk_id": chunk_id,
                    "chunk_result": chunk_result
                })
        
        # Strategy 1: Find entities that appear in multiple chunks
        multi_chunk_entities = {
            entity: chunks for entity, chunks in entity_chunk_map.items() 
            if len(chunks) > 1
        }
        
        print(f"Found {len(multi_chunk_entities)} entities appearing in multiple chunks")
        
        # Strategy 2: Look for incomplete relations that might be completed cross-chunk
        processed_pairs = set()
        
        for chunk_id_1, relation in all_relations:
            subject = str(relation.get("subject", "")).strip()
            object_entity = str(relation.get("object", "")).strip()
            predicate = str(relation.get("predicate", "")).strip()
            
            if not subject or not object_entity or not predicate:
                continue
                
            subject_lower = subject.lower()
            object_lower = object_entity.lower()
            
            # Look for the same entities in other chunks
            for entity, chunks in multi_chunk_entities.items():
                if entity in [subject_lower, object_lower]:
                    # This entity appears in multiple chunks
                    for chunk_info in chunks:
                        if chunk_info["chunk_id"] != chunk_id_1:
                            # Found entity in a different chunk
                            
                            # Create cross-chunk relation if we have subject in one chunk
                            # and object in another
                            if entity == subject_lower:
                                # Subject found in another chunk, look for different objects
                                other_chunk_id = chunk_info["chunk_id"]
                                pair_key = (
                                    min(chunk_id_1, other_chunk_id),
                                    max(chunk_id_1, other_chunk_id),
                                    subject_lower,
                                    object_lower,
                                    predicate.lower()
                                )
                                
                                if pair_key not in processed_pairs:
                                    processed_pairs.add(pair_key)
                                    
                                    # Find chunk result for the other chunk
                                    subject_chunk = chunk_info
                                    object_chunk = None
                                    
                                    # Find chunk containing the object
                                    for cr in all_chunk_results:
                                        if cr["index"] == chunk_id_1:
                                            object_chunk = {"chunk_id": chunk_id_1, "chunk_result": cr}
                                            break
                                    
                                    if object_chunk:
                                        cross_chunk_relation = self.create_cross_chunk_relation(
                                            subject, predicate, object_entity,
                                            subject_chunk, object_chunk
                                        )
                                        
                                        if cross_chunk_relation:
                                            cross_chunk_relations.append(cross_chunk_relation)
        
        return cross_chunk_relations

    def create_cross_chunk_relation(self, subject, predicate, object_entity, 
                                  subject_chunk, object_chunk):
        """Create a cross-chunk relation with proper span information."""
        
        # Find sentences containing subject in subject chunk
        subject_sentences = self.find_sentences_containing_entity(
            subject, subject_chunk["chunk_result"].get("sentences", [])
        )
        
        # Find sentences containing object in object chunk  
        object_sentences = self.find_sentences_containing_entity(
            object_entity, object_chunk["chunk_result"].get("sentences", [])
        )
        
        if not subject_sentences or not object_sentences:
            return None
        
        # Take the first mention of each (could be enhanced with better selection)
        primary_subject_sentence = subject_sentences[0]
        primary_object_sentence = object_sentences[0]
        
        # Extract docling_refs from both chunks
        subject_docling_ref = None
        object_docling_ref = None
        
        subject_provenance = subject_chunk["chunk_result"].get("provenance", [])
        if subject_provenance and len(subject_provenance) > 0:
            subject_docling_ref = subject_provenance[0].get("docling_ref")
        
        object_provenance = object_chunk["chunk_result"].get("provenance", [])
        if object_provenance and len(object_provenance) > 0:
            object_docling_ref = object_provenance[0].get("docling_ref")
        
        # Create cross-chunk relation
        cross_chunk_relation = {
            "subject": subject,
            "predicate": predicate,
            "object": object_entity,
            "source_span": {
                "span_type": "cross_chunk",
                "subject_chunk": {
                    "chunk_id": subject_chunk["chunk_id"],
                    "section": subject_chunk["chunk_result"].get("section", "Unknown"),
                    "sentence_id": primary_subject_sentence["sentence_id"],
                    "sentence_text": primary_subject_sentence["text"],
                    "document_offsets": {
                        "start": primary_subject_sentence["document_start"],
                        "end": primary_subject_sentence["document_end"]
                    },
                    "docling_ref": subject_docling_ref
                },
                "object_chunk": {
                    "chunk_id": object_chunk["chunk_id"],
                    "section": object_chunk["chunk_result"].get("section", "Unknown"),
                    "sentence_id": primary_object_sentence["sentence_id"], 
                    "sentence_text": primary_object_sentence["text"],
                    "document_offsets": {
                        "start": primary_object_sentence["document_start"],
                        "end": primary_object_sentence["document_end"]
                    },
                    "docling_ref": object_docling_ref
                },
                "text_evidence": f"Subject: \"{primary_subject_sentence['text']}\" | Object: \"{primary_object_sentence['text']}\"",
                "confidence": 0.5,  # Lower confidence for cross-chunk relations
                "total_span": {
                    "start": min(primary_subject_sentence["document_start"], 
                               primary_object_sentence["document_start"]),
                    "end": max(primary_subject_sentence["document_end"],
                             primary_object_sentence["document_end"])
                }
            }
        }
        
        return cross_chunk_relation

    # --------------------------------------------------------------
    def load_chunks(self, chunks_jsonl_path: str):
        print(f"Loading chunks from: {chunks_jsonl_path}")
        chunks = []
        with open(chunks_jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    chunks.append(json.loads(line))
                except Exception as e:
                    print(f"Warning line {line_num}: {e}")
        print(f"Loaded {len(chunks)} chunks", flush=True)
        return chunks

    # --------------------------------------------------------------
    def process_chunk(self, chunk_data: dict, idx: int, total_chunks: int = None):
        section = chunk_data.get("section", "Unknown")
        text = chunk_data.get("chunk", "").strip()
        provenance = chunk_data.get("provenance", [])
        
        # NEW: Get sentence data for span mapping
        sentences = chunk_data.get("sentences", [])
        chunk_id = idx  # Use index as chunk ID
        
        if text.startswith("[Section:"):
            # remove header line
            lines = text.split("\n", 1)
            text = lines[1] if len(lines) > 1 else text

        # Show progress with total if available
        if total_chunks:
            print(f"→ Processing chunk {idx+1}/{total_chunks}: {section} ({len(text)} chars)", flush=True)
        else:
            print(f"→ Processing chunk {idx+1}: {section} ({len(text)} chars)", flush=True)

        start = time.time()
        try:
            # Original KG extraction (unchanged)
            print(f"  Generating knowledge graph...", flush=True)
            graph = self.kg.generate(
                input_data=text,
                context=f"Scientific text from section '{section}'. Extract entities and relations.",
                cluster=False,
            )
            
            # NEW: Add span mapping to relations
            enhanced_relations = []
            original_relations = list(graph.relations)
            
            print(f"  Found {len(graph.entities)} entities, {len(original_relations)} relations", flush=True)
            print(f"  Mapping {len(original_relations)} relations to sentences...", flush=True)
            
            for relation in original_relations:
                # Convert relation to dict - KG-GEN returns tuples (subject, predicate, object)
                if isinstance(relation, tuple) and len(relation) == 3:
                    relation_dict = {
                        "subject": str(relation[0]),
                        "predicate": str(relation[1]), 
                        "object": str(relation[2])
                    }
                elif hasattr(relation, 'model_dump'):
                    relation_dict = relation.model_dump()
                elif hasattr(relation, 'dict'):
                    relation_dict = relation.dict()
                elif isinstance(relation, dict):
                    relation_dict = relation
                else:
                    # Fallback: convert to string representation
                    relation_dict = {"subject": str(relation), "predicate": "unknown", "object": "unknown"}
                
                # Calculate span for this relation
                enhanced_relation = self.calculate_relation_span(relation_dict, sentences, chunk_id, provenance)
                
                if enhanced_relation:
                    enhanced_relations.append(enhanced_relation)
                    # Show span info for debugging
                    span = enhanced_relation["source_span"]
                    if span["span_type"] != "chunk_fallback":
                        print(f"    {enhanced_relation.get('subject', 'N/A')} → {enhanced_relation.get('predicate', 'N/A')} → {enhanced_relation.get('object', 'N/A')}")
                        print(f"      Span: sentences {span['sentence_start']}-{span['sentence_end']} ({span['span_type']})")
                else:
                    # Keep original relation if span mapping failed
                    enhanced_relations.append(relation_dict)
            
            elapsed = time.time() - start
            return {
                "index": idx,
                "section": section,
                "entities": list(graph.entities),
                "relations": enhanced_relations,  # NEW: Use enhanced relations with spans
                "provenance": provenance,
                "time": elapsed,
                "raw_graph": graph,
                # NEW: Add sentence metadata
                "sentence_count": len(sentences),
                "relations_with_spans": len([r for r in enhanced_relations if r.get("source_span")])
            }
        except Exception as e:
            print(f"  ERROR: {e}")
            return {
                "index": idx,
                "section": section,
                "entities": [],
                "relations": [],
                "provenance": provenance,
                "time": time.time() - start,
                "error": str(e),
                "raw_graph": None,
            }

    # --------------------------------------------------------------
    def process_all(self, chunks, max_chunks=None):
        if max_chunks:
            chunks = chunks[:max_chunks]
            print(f"Processing first {max_chunks} chunks", flush=True)

        print(f"Starting KG extraction for {len(chunks)} chunks...", flush=True)
        results = []
        total_start = time.time()
        for i, ch in enumerate(chunks):
            result = self.process_chunk(ch, i, len(chunks))
            results.append(result)
            # Show completion for each chunk
            if result.get("error"):
                print(f"  ✗ Chunk {i+1}/{len(chunks)} failed: {result.get('error', 'Unknown error')}", flush=True)
            else:
                entities_count = len(result.get("entities", []))
                relations_count = len(result.get("relations", []))
                chunk_time = result.get("time", 0)
                print(f"  ✓ Chunk {i+1}/{len(chunks)} completed in {chunk_time:.1f}s ({entities_count} entities, {relations_count} relations)", flush=True)
        
        total = time.time() - total_start
        print(f"\nProcessed {len(results)} chunks in {total:.2f}s", flush=True)
        return results

    # --------------------------------------------------------------
    def aggregate(self, results):
        all_entities, all_relations = set(), []  # Changed: relations as list since they're now dicts
        section_stats = defaultdict(lambda: {"chunks": 0, "entities": 0, "relations": 0})
        errors = []
        total_relations_with_spans = 0
        
        for r in results:
            if r.get("error"):
                errors.append(r)
                continue
            all_entities.update(r["entities"])
            all_relations.extend(r["relations"])  # Changed: extend instead of update
            
            # Count relations with spans
            relations_with_spans = r.get("relations_with_spans", 0)
            total_relations_with_spans += relations_with_spans
            
            s = r["section"]
            section_stats[s]["chunks"] += 1
            section_stats[s]["entities"] += len(r["entities"])
            section_stats[s]["relations"] += len(r["relations"])
        
        # NEW: Detect cross-chunk relations
        cross_chunk_relations = self.detect_cross_chunk_relations(results)
        
        # Combine original relations with cross-chunk relations
        total_relations = all_relations + cross_chunk_relations
            
        summary = {
            "total_chunks": len(results),
            "errors": len(errors),
            "entities": len(all_entities),
            "relations": len(total_relations),
            "cross_chunk_relations": len(cross_chunk_relations),
            "relations_with_spans": total_relations_with_spans,  # NEW: Track span mapping
            "sections": dict(section_stats),
            "all_relations": total_relations,  # Include all relations for save method
        }
        print(f"\nEntities: {summary['entities']} | Relations: {summary['relations']}")
        print(f"Relations with span mapping: {summary['relations_with_spans']}")
        print(f"Cross-chunk relations detected: {summary['cross_chunk_relations']}")
        return summary

    # --------------------------------------------------------------
    def save(self, results, summary, base, kg_output_dir="output/text_triples", report_output_dir="output/reports", timestamp=None):
        ts = timestamp if timestamp else datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directories
        Path(kg_output_dir).mkdir(parents=True, exist_ok=True)
        Path(report_output_dir).mkdir(parents=True, exist_ok=True)
        
        out_res = Path(kg_output_dir) / f"{base}_kg_results_{ts}.json"
        out_sum = Path(report_output_dir) / f"{base}_kg_summary_{ts}.json"

        def safe_serialize_graph(g):
            """Safely convert a KGGen graph to something JSON serializable."""
            if g is None:
                return None

            # If it’s a Pydantic model or dict
            if hasattr(g, "model_dump"):
                g = g.model_dump()
            elif hasattr(g, "dict"):
                g = g.dict()
            elif not isinstance(g, dict):
                return str(g)

            # Recursively convert any sets to lists
            def convert_sets(obj):
                if isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: convert_sets(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_sets(v) for v in obj]
                return obj

            return convert_sets(g)

        serializable = []
        for r in results:
            x = r.copy()
            x["raw_graph"] = safe_serialize_graph(x.get("raw_graph"))
            serializable.append(x)

        # Extract all relations (including cross-chunk) for output
        all_relations_output = summary.get("all_relations", [])
        
        with open(out_res, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {k: v for k, v in summary.items() if k != "all_relations"},  # Exclude from summary
                "chunks": serializable,
                "all_relations": all_relations_output  # Include all relations separately
            }, f, indent=2)

        with open(out_sum, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"\nResults saved to {out_res}")
        print(f"Summary saved to {out_sum}")

        return {"results": str(out_res), "summary": str(out_sum)}

    # --------------------------------------------------------------
    def run(self, chunks_jsonl_path, max_chunks=None, timestamp=None):
        base = Path(chunks_jsonl_path).stem.replace(".texts_chunks", "")
        print(f"\n=== Running KG Extraction Pipeline ===\nFile: {chunks_jsonl_path}")
        chunks = self.load_chunks(chunks_jsonl_path)
        results = self.process_all(chunks, max_chunks)
        summary = self.aggregate(results)
        paths = self.save(results, summary, base, timestamp=timestamp)
        print("\n=== PIPELINE COMPLETE ===")
        return {"summary": summary, "outputs": paths}

    # --------------------------------------------------------------
    def process_chunks_file(self, chunks_jsonl_path, max_chunks=None):
        """Process a chunks file and return the paths to generated files."""
        result = self.run(chunks_jsonl_path, max_chunks)
        return [result["outputs"]["results"], result["outputs"]["summary"]]


def main():
    import sys
    
    extractor = ChunkKGExtractor()
    
    # Handle command line arguments
    if len(sys.argv) >= 2:
        file = sys.argv[1]
        timestamp = sys.argv[2] if len(sys.argv) >= 3 else None
        
        if not Path(file).exists():
            print(f"Error: File not found: {file}")
            return
            
        print(f"Using: {file}")
        if timestamp:
            print(f"Using timestamp: {timestamp}")
        extractor.run(file, timestamp=timestamp)
    else:
        # Fallback to automatic detection
        candidates = list(Path(".").glob("*.texts_chunks.jsonl"))
        if not candidates:
            print("No .texts_chunks.jsonl found — run core/text_chunker.py first.")
            return
        file = str(candidates[0])
        print(f"Using: {file}")
        extractor.run(file)


if __name__ == "__main__":
    main()
