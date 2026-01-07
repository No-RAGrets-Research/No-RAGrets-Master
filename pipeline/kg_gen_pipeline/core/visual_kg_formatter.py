#!/usr/bin/env python3
"""
visual_kg_formatter.py
---------------------
Transforms visual triple extraction output to KG loader compatible format.

Takes the JSON output from visual_kg_extractor.py and converts it to the
format expected by kg_data_loader.py for seamless integration with existing KG pipeline.

Usage:
    python visual_kg_formatter.py visual_triples_poc.json
"""

import json
import re
import ast
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set


class VisualKGFormatter:
    def __init__(self):
        pass
    
    def parse_raw_output(self, raw_output: str) -> List[Tuple[str, str, str]]:
        """Parse the raw VLM output string into structured triples."""
        triples = []
        
        # Handle different output formats from the VLM
        if raw_output.startswith('[') and raw_output.endswith(']'):
            try:
                # Try to parse as a Python list literal
                parsed = ast.literal_eval(raw_output)
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, (list, tuple)) and len(item) >= 3:
                            subject = str(item[0]).strip()
                            predicate = str(item[1]).strip()
                            obj = str(item[2]).strip()
                            if subject and predicate and obj:
                                triples.append((subject, predicate, obj))
                return triples
            except (ValueError, SyntaxError):
                pass
        
        # Fallback: regex parsing for tuple patterns
        # Pattern matches: (subject, predicate, object)
        pattern = r'\([^)]*?["\']([^"\']*?)["\'][^)]*?["\']([^"\']*?)["\'][^)]*?["\']([^"\']*?)["\'][^)]*?\)'
        matches = re.findall(pattern, raw_output)
        
        if matches:
            for match in matches:
                subject, predicate, obj = match
                subject = subject.strip()
                predicate = predicate.strip()
                obj = obj.strip()
                if subject and predicate and obj:
                    triples.append((subject, predicate, obj))
            return triples
        
        # Alternative pattern without quotes
        pattern2 = r'\(([^,]+),\s*([^,]+),\s*([^)]+)\)'
        matches2 = re.findall(pattern2, raw_output)
        
        for match in matches2:
            subject = str(match[0]).strip().strip('"\'')
            predicate = str(match[1]).strip().strip('"\'')
            obj = str(match[2]).strip().strip('"\'')
            if subject and predicate and obj:
                triples.append((subject, predicate, obj))
        
        return triples
    
    def extract_entities(self, triples: List[Tuple[str, str, str]]) -> Set[str]:
        """Extract unique entities from triples."""
        entities = set()
        for subject, predicate, obj in triples:
            entities.add(subject)
            entities.add(obj)
        return entities
    
    def create_visual_source_span(self, figure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create visual-specific source span format."""
        return {
            "span_type": "visual_figure",
            "figure_id": figure_data.get("figure_id", "unknown"),
            "page_number": figure_data.get("page", 0),
            "caption_evidence": figure_data.get("caption", ""),
            "bbox_coordinates": figure_data.get("provenance", {}).get("bbox", {}),
            "confidence": 0.9 if figure_data.get("success", False) else 0.3,
            "extraction_method": "visual_triple_extraction",
            "image_info": figure_data.get("image_info", {}),
            "charspan": figure_data.get("provenance", {}).get("charspan", [])
        }
    
    def format_single_figure(self, figure_data: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """Format a single figure's data into chunk format."""
        # Parse raw output into triples
        raw_output = figure_data.get("raw_output", "")
        triples = self.parse_raw_output(raw_output)
        
        # Extract entities
        entities = list(self.extract_entities(triples))
        
        # Create visual source span
        visual_source_span = self.create_visual_source_span(figure_data)
        
        # Format relations with source span
        relations = []
        for subject, predicate, obj in triples:
            relation = {
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "source_span": visual_source_span
            }
            relations.append(relation)
        
        # Create provenance for KG loader compatibility
        provenance = []
        if "provenance" in figure_data:
            prov_data = figure_data["provenance"]
            provenance.append({
                "docling_ref": f"#/figures/{chunk_index}",
                "label": "figure",
                "pages": [{
                    "page_no": prov_data.get("page_no", figure_data.get("page", 0)),
                    "bbox": prov_data.get("bbox", {}),
                    "coord_origin": "BOTTOMLEFT"
                }]
            })
        
        # Create chunk
        chunk = {
            "index": chunk_index,
            "section": f"Figure {figure_data.get('page', chunk_index)} Analysis",
            "entities": entities,
            "relations": relations,
            "provenance": provenance,
            "figure_id": figure_data.get("figure_id", f"fig_{chunk_index}"),
            "success": figure_data.get("success", False),
            "extraction_method": "visual_triple_extraction"
        }
        
        return chunk
    
    def create_summary(self, chunks: List[Dict[str, Any]], source_file: str) -> Dict[str, Any]:
        """Create summary statistics."""
        total_entities = set()
        total_relations = 0
        sections = {}
        successful_extractions = 0
        
        for chunk in chunks:
            # Count entities and relations
            chunk_entities = chunk.get("entities", [])
            chunk_relations = chunk.get("relations", [])
            
            total_entities.update(chunk_entities)
            total_relations += len(chunk_relations)
            
            # Track sections
            section = chunk.get("section", "Unknown")
            if section not in sections:
                sections[section] = {"chunks": 0, "entities": 0, "relations": 0}
            
            sections[section]["chunks"] += 1
            sections[section]["entities"] += len(chunk_entities)
            sections[section]["relations"] += len(chunk_relations)
            
            # Track success rate
            if chunk.get("success", False):
                successful_extractions += 1
        
        summary = {
            "total_chunks": len(chunks),
            "errors": len(chunks) - successful_extractions,
            "entities": len(total_entities),
            "relations": total_relations,
            "cross_chunk_relations": 0,  # Not applicable for visual extraction
            "relations_with_spans": total_relations,
            "sections": sections,
            "source_file": source_file,
            "extraction_method": "visual_triple_extraction",
            "success_rate": successful_extractions / len(chunks) if chunks else 0,
            "processed_at": datetime.now().isoformat()
        }
        
        return summary
    
    def transform_visual_output(self, visual_output_file: str) -> Dict[str, Any]:
        """Transform visual triples output to KG loader format."""
        # Load visual triples data
        with open(visual_output_file, 'r', encoding='utf-8') as f:
            visual_data = json.load(f)
        
        if not isinstance(visual_data, list):
            raise ValueError("Expected visual output to be a list of figure data")
        
        # Process each figure into chunk format
        chunks = []
        for i, figure_data in enumerate(visual_data):
            chunk = self.format_single_figure(figure_data, i)
            chunks.append(chunk)
        
        # Create summary
        summary = self.create_summary(chunks, visual_output_file)
        
        # Create final KG loader compatible format
        kg_format = {
            "summary": summary,
            "chunks": chunks
        }
        
        return kg_format
    
    def save_formatted_output(self, kg_format: Dict[str, Any], output_file: str):
        """Save the formatted output to file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(kg_format, f, indent=2, ensure_ascii=False)
        
        print(f"Formatted KG data saved to: {output_file}")
        print(f"Summary: {kg_format['summary']['entities']} entities, {kg_format['summary']['relations']} relations")
        print(f"Success rate: {kg_format['summary']['success_rate']:.1%}")
    
    def process_visual_output(self, input_file: str, output_file: str = None):
        """Process visual triples output and save in KG loader format."""
        if output_file is None:
            input_path = Path(input_file)
            output_file = str(input_path.parent / f"{input_path.stem}_kg_format.json")
        
        print(f"Processing visual triples from: {input_file}")
        
        # Transform format
        kg_format = self.transform_visual_output(input_file)
        
        # Save formatted output
        self.save_formatted_output(kg_format, output_file)
        
        return output_file


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python visual_kg_formatter.py <visual_triples_output.json> [output_file.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    formatter = VisualKGFormatter()
    result_file = formatter.process_visual_output(input_file, output_file)
    
    print(f"\nFormatted output ready for kg_data_loader.py:")
    print(f"python ../knowledge_graph/kg_data_loader.py {result_file}")


if __name__ == "__main__":
    main()