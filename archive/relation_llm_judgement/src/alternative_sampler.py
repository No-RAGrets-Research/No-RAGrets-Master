"""
Alternative sampling strategy when API search filters are broken.

Fetches all relations and filters/samples client-side.
"""

from typing import List, Dict, Any
import random
from collections import defaultdict
from api_client import KnowledgeGraphClient


class AlternativeSampler:
    """Samples relations when API filtering is broken."""
    
    def __init__(self, client: KnowledgeGraphClient):
        self.client = client
        self._all_relations_cache = None
    
    def _fetch_all_relations(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch all relations (up to limit) without filters.
        
        Args:
            limit: Maximum relations to fetch
            
        Returns:
            List of all relations
        """
        if self._all_relations_cache is not None:
            return self._all_relations_cache
        
        print(f"   Fetching up to {limit} relations from API...")
        
        try:
            relations = self.client.search_relations(limit=limit)
            self._all_relations_cache = relations
            print(f"   ✓ Fetched {len(relations)} relations")
            return relations
        except Exception as e:
            print(f"   ✗ Error fetching relations: {e}")
            return []
    
    def get_entity_participation(
        self,
        relations: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate which entities participate in how many relations.
        
        Args:
            relations: List of all relations
            
        Returns:
            Dictionary mapping entity names to participation stats
        """
        entity_stats = defaultdict(lambda: {
            "incoming": 0,
            "outgoing": 0,
            "total": 0,
            "relations": []
        })
        
        for rel in relations:
            subject_name = rel.get("subject", {}).get("name")
            object_name = rel.get("object", {}).get("name")
            
            if subject_name:
                entity_stats[subject_name]["outgoing"] += 1
                entity_stats[subject_name]["total"] += 1
                entity_stats[subject_name]["relations"].append(rel)
            
            if object_name:
                entity_stats[object_name]["incoming"] += 1
                entity_stats[object_name]["total"] += 1
                entity_stats[object_name]["relations"].append(rel)
        
        return dict(entity_stats)
    
    def sample_from_top_entities(
        self,
        n_entities: int = 5,
        target_relations: int = 30,
        per_entity_max: int = 10,
        max_fetch: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Sample relations from top participating entities.
        
        Args:
            n_entities: Number of top entities to sample from
            target_relations: Target number of relations
            per_entity_max: Max relations per entity
            max_fetch: Maximum relations to fetch from API
            
        Returns:
            List of sampled relations
        """
        # Fetch all available relations
        all_relations = self._fetch_all_relations(limit=max_fetch)
        
        if not all_relations:
            return []
        
        # Calculate entity participation
        entity_stats = self.get_entity_participation(all_relations)
        
        # Sort entities by total participation
        top_entities = sorted(
            entity_stats.items(),
            key=lambda x: x[1]["total"],
            reverse=True
        )[:n_entities]
        
        print(f"\n   Top {n_entities} entities by relation count:")
        for entity_name, stats in top_entities:
            print(f"      - {entity_name}: {stats['total']} relations")
        
        # Sample relations from these entities
        sampled = []
        seen_ids = set()
        
        for entity_name, stats in top_entities:
            entity_relations = stats["relations"]
            
            # Deduplicate
            unique_rels = []
            for rel in entity_relations:
                rel_id = rel.get("id")
                if rel_id and rel_id not in seen_ids:
                    seen_ids.add(rel_id)
                    unique_rels.append(rel)
            
            # Sample from this entity
            n_sample = min(per_entity_max, len(unique_rels))
            entity_sample = random.sample(unique_rels, n_sample)
            
            # Add hub entity metadata
            for rel in entity_sample:
                rel["hub_entity"] = entity_name
                rel["hub_connectivity"] = stats["total"]
            
            sampled.extend(entity_sample)
        
        # Shuffle and limit
        random.shuffle(sampled)
        return sampled[:target_relations]
