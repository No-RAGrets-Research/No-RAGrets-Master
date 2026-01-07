"""
Hub Entity and Relation Sampler

Samples relations from hub entities with diversity considerations.
"""

from typing import List, Dict, Any, Optional
import random
from collections import defaultdict
from api_client import KnowledgeGraphClient


class RelationSampler:
    """Samples relations from hub entities with diversity constraints."""
    
    def __init__(self, client: KnowledgeGraphClient):
        """
        Initialize the sampler.
        
        Args:
            client: Knowledge Graph API client
        """
        self.client = client
    
    def get_hub_entities(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get top N hub entities.
        
        Args:
            n: Number of hub entities to retrieve
            
        Returns:
            List of hub entity dictionaries with connection info
        """
        return self.client.get_most_connected_entities(limit=n)
    
    def sample_relations_from_hub(
        self,
        entity_name: str,
        max_relations: int = 10,
        balance_direction: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Sample relations from a single hub entity.
        
        Args:
            entity_name: Name of the hub entity
            max_relations: Maximum relations to sample
            balance_direction: Whether to balance incoming vs outgoing
            
        Returns:
            List of sampled relation dictionaries
        """
        try:
            connections = self.client.get_entity_connections(
                entity_name=entity_name,
                direction="both",
                max_relations=1000
            )
        except Exception as e:
            # Fallback: Use search endpoint instead
            print(f"   Info: Using search fallback for '{entity_name}'")
            return self._sample_relations_via_search(entity_name, max_relations)
        
        incoming = connections.get("incoming", [])
        outgoing = connections.get("outgoing", [])
        
        if not incoming and not outgoing:
            # Try search fallback
            return self._sample_relations_via_search(entity_name, max_relations)
        
        if balance_direction and incoming and outgoing:
            # Sample evenly from both directions
            n_incoming = max_relations // 2
            n_outgoing = max_relations - n_incoming
            
            sampled_incoming = random.sample(
                incoming, 
                min(n_incoming, len(incoming))
            )
            sampled_outgoing = random.sample(
                outgoing, 
                min(n_outgoing, len(outgoing))
            )
            
            sampled = sampled_incoming + sampled_outgoing
        else:
            # Sample from combined pool
            all_relations = incoming + outgoing
            sampled = random.sample(
                all_relations,
                min(max_relations, len(all_relations))
            )
        
        return sampled
    
    def _sample_relations_via_search(
        self,
        entity_name: str,
        max_relations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fallback method to sample relations using search endpoint.
        
        Args:
            entity_name: Name of the entity
            max_relations: Maximum relations to sample
            
        Returns:
            List of relation dictionaries
        """
        try:
            # Search for relations where entity is subject
            subject_relations = self.client.search_relations(
                subject=entity_name,
                limit=max_relations * 2  # Get more to sample from
            )
            
            # Search for relations where entity is object
            object_relations = self.client.search_relations(
                object_name=entity_name,
                limit=max_relations * 2
            )
            
            # Combine and sample
            all_relations = subject_relations + object_relations
            
            if not all_relations:
                return []
            
            # Remove duplicates by relation ID
            seen_ids = set()
            unique_relations = []
            for rel in all_relations:
                rel_id = rel.get("id")
                if rel_id and rel_id not in seen_ids:
                    seen_ids.add(rel_id)
                    unique_relations.append(rel)
            
            # Sample up to max_relations
            sampled = random.sample(
                unique_relations,
                min(max_relations, len(unique_relations))
            )
            
            return sampled
            
        except Exception as e:
            print(f"   Warning: Search fallback also failed for '{entity_name}': {e}")
            return []
    
    def sample_diverse_relations(
        self,
        hub_entities: List[Dict[str, Any]],
        total_target: int = 50,
        per_entity_max: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Sample relations diversely across multiple hub entities.
        
        Args:
            hub_entities: List of hub entity dictionaries
            total_target: Target total number of relations
            per_entity_max: Maximum relations per entity
            
        Returns:
            List of sampled relations with diversity
        """
        all_sampled = []
        successful_entities = []
        
        # Initial equal sampling per entity
        per_entity = min(
            per_entity_max,
            total_target // len(hub_entities)
        )
        
        for entity_info in hub_entities:
            entity_name = entity_info.get("entity", {}).get("name")
            if not entity_name:
                continue
            
            relations = self.sample_relations_from_hub(
                entity_name=entity_name,
                max_relations=per_entity
            )
            
            # Skip entities that returned no relations
            if not relations:
                print(f"   Skipping '{entity_name}' (no relations found)")
                continue
            
            successful_entities.append(entity_name)
            
            # Add hub entity info to each relation
            for rel in relations:
                rel["hub_entity"] = entity_name
                rel["hub_connectivity"] = entity_info.get("total_connections", 0)
            
            all_sampled.extend(relations)
        
        if not all_sampled:
            print("   Warning: No relations found from any hub entities")
            return []
        
        print(f"   Successfully sampled from {len(successful_entities)} entities: {', '.join(successful_entities)}")
        
        # If we need more, sample additional from remaining pool
        if len(all_sampled) < total_target:
            remaining = total_target - len(all_sampled)
            # Could implement additional sampling logic here
        
        # Shuffle to mix entities
        random.shuffle(all_sampled)
        
        return all_sampled[:total_target]
    
    def enrich_relations_with_context(
        self,
        relations: List[Dict[str, Any]],
        include_source_span: bool = True,
        include_provenance: bool = True,
        include_image: bool = False,
        image_output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich sampled relations with full context for judging.
        
        Args:
            relations: List of relation dictionaries
            include_source_span: Whether to fetch source span text
            include_provenance: Whether to fetch provenance details
            include_image: Whether to download section images
            image_output_dir: Directory to save images (required if include_image=True)
            
        Returns:
            List of enriched relation dictionaries
        """
        enriched = []
        
        for rel in relations:
            relation_id = rel.get("id")
            if not relation_id:
                continue
            
            enriched_rel = rel.copy()
            
            try:
                if include_source_span:
                    source_span = self.client.get_relation_source_span(relation_id)
                    enriched_rel["source_span"] = source_span
                
                if include_provenance:
                    provenance = self.client.get_relation_provenance(relation_id)
                    enriched_rel["provenance"] = provenance
                
                if include_image and image_output_dir:
                    image_path = f"{image_output_dir}/{relation_id}.png"
                    self.client.get_relation_section_image(
                        relation_id=relation_id,
                        output_path=image_path
                    )
                    enriched_rel["image_path"] = image_path
                
                enriched.append(enriched_rel)
            
            except Exception as e:
                print(f"Warning: Could not enrich relation {relation_id}: {e}")
                # Still include the relation with whatever data we have
                enriched.append(enriched_rel)
        
        return enriched
    
    def analyze_sample_diversity(self, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze diversity metrics of sampled relations.
        
        Args:
            relations: List of relation dictionaries
            
        Returns:
            Dictionary with diversity metrics
        """
        predicates = defaultdict(int)
        sections = defaultdict(int)
        papers = defaultdict(int)
        hub_entities = defaultdict(int)
        
        confidence_scores = []
        
        for rel in relations:
            predicate = rel.get("predicate", "unknown")
            predicates[predicate] += 1
            
            section = rel.get("section", "unknown")
            sections[section] += 1
            
            paper = rel.get("source_paper", "unknown")
            papers[paper] += 1
            
            hub = rel.get("hub_entity", "unknown")
            hub_entities[hub] += 1
            
            confidence = rel.get("confidence")
            if confidence is not None:
                confidence_scores.append(confidence)
        
        return {
            "total_relations": len(relations),
            "unique_predicates": len(predicates),
            "predicate_distribution": dict(predicates),
            "unique_sections": len(sections),
            "section_distribution": dict(sections),
            "unique_papers": len(papers),
            "paper_distribution": dict(papers),
            "unique_hubs": len(hub_entities),
            "hub_distribution": dict(hub_entities),
            "confidence_stats": {
                "count": len(confidence_scores),
                "mean": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "min": min(confidence_scores) if confidence_scores else 0,
                "max": max(confidence_scores) if confidence_scores else 0,
            }
        }
