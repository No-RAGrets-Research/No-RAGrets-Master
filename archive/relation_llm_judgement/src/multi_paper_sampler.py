"""
Multi-paper sampler that ensures diversity across all papers in the knowledge graph.
"""

from typing import List, Dict, Any
from collections import defaultdict, Counter
import random
from api_client import KnowledgeGraphClient


class MultiPaperSampler:
    """Sampler that ensures relations from multiple papers."""
    
    def __init__(self, client: KnowledgeGraphClient, seed: int = 42):
        """
        Initialize multi-paper sampler.
        
        Args:
            client: Knowledge graph API client
            seed: Random seed for reproducibility
        """
        self.client = client
        random.seed(seed)
        self._papers_cache = None
        self._relations_by_paper_cache = {}
        
    def _get_all_papers(self) -> List[Dict[str, Any]]:
        """Fetch and cache all papers from the API."""
        if self._papers_cache is None:
            print("Fetching all papers from API...")
            response = self.client.session.get(f"{self.client.base_url}/papers")
            response.raise_for_status()
            self._papers_cache = response.json()
            print(f"Found {len(self._papers_cache)} papers")
        return self._papers_cache
    
    def _get_relations_for_paper(self, paper_filename: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get relations from a specific paper using the new /api/papers/{filename}/relations endpoint.
        
        Args:
            paper_filename: The filename of the paper (from the 'filename' field in /api/papers)
            limit: Maximum relations to fetch
            
        Returns:
            List of relations from this paper
        """
        if paper_filename not in self._relations_by_paper_cache:
            # Use the new dedicated endpoint for paper relations (uses filename as identifier)
            paper_relations = self.client.get_paper_relations(paper_filename, limit=limit)
            self._relations_by_paper_cache[paper_filename] = paper_relations
        
        # Return up to limit relations
        cached = self._relations_by_paper_cache[paper_filename]
        return cached[:limit]
    
    def sample_across_papers(
        self,
        n_relations: int = 100,
        n_papers: int = 10,
        min_relations_per_paper: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Sample relations evenly across multiple papers.
        
        Args:
            n_relations: Total number of relations to sample
            n_papers: Number of different papers to sample from
            min_relations_per_paper: Minimum relations each paper should have
            
        Returns:
            List of sampled relations from multiple papers
        """
        print("=" * 70)
        print("MULTI-PAPER SAMPLING")
        print("=" * 70)
        
        # Get all papers
        all_papers = self._get_all_papers()
        
        # Filter papers with enough relations
        eligible_papers = [
            p for p in all_papers 
            if p.get('total_relations', 0) >= min_relations_per_paper
        ]
        
        print(f"Papers with >={min_relations_per_paper} relations: {len(eligible_papers)}/{len(all_papers)}")
        
        # Select top N papers by relation count
        papers_by_relations = sorted(
            eligible_papers,
            key=lambda p: p.get('total_relations', 0),
            reverse=True
        )
        selected_papers = papers_by_relations[:n_papers]
        
        print(f"\nSelected {len(selected_papers)} papers:")
        for i, paper in enumerate(selected_papers, 1):
            print(f"  {i}. {paper['filename'][:50]}... ({paper['total_relations']} relations)")
        
        # Calculate relations per paper
        relations_per_paper = n_relations // len(selected_papers)
        
        print(f"\nSampling ~{relations_per_paper} relations from each paper...")
        
        # Sample from each paper
        sampled_relations = []
        for paper in selected_papers:
            paper_rels = self._get_relations_for_paper(paper['filename'], limit=relations_per_paper * 2)
            
            if len(paper_rels) == 0:
                print(f"  Warning: No relations found for {paper['filename']}")
                continue
            
            # Sample up to relations_per_paper
            n_sample = min(relations_per_paper, len(paper_rels))
            sampled = random.sample(paper_rels, n_sample)
            sampled_relations.extend(sampled)
            
            print(f"  {paper['filename'][:45]}...: sampled {n_sample}/{len(paper_rels)}")
        
        # If we're short, add more from random papers
        if len(sampled_relations) < n_relations:
            shortage = n_relations - len(sampled_relations)
            print(f"\nNeed {shortage} more relations, sampling from remaining papers...")
            
            remaining_papers = [p for p in selected_papers if len(self._get_relations_for_paper(p['filename'])) > relations_per_paper]
            for paper in remaining_papers:
                if len(sampled_relations) >= n_relations:
                    break
                paper_rels = self._get_relations_for_paper(paper['filename'], limit=1000)
                already_sampled = {r['id'] for r in sampled_relations}
                available = [r for r in paper_rels if r['id'] not in already_sampled]
                
                n_sample = min(shortage, len(available))
                if n_sample > 0:
                    additional = random.sample(available, n_sample)
                    sampled_relations.extend(additional)
                    shortage -= n_sample
        
        print(f"\n✓ Total sampled: {len(sampled_relations)} relations from {len(set(r.get('source_paper') for r in sampled_relations))} papers")
        
        return sampled_relations[:n_relations]
    
    def analyze_diversity(self, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze diversity of sampled relations."""
        predicates = [r.get('predicate', 'UNKNOWN') for r in relations]
        papers = [r.get('source_paper', 'UNKNOWN') for r in relations]
        
        return {
            'total_relations': len(relations),
            'unique_predicates': len(set(predicates)),
            'unique_papers': len(set(papers)),
            'predicate_distribution': dict(Counter(predicates).most_common(10)),
            'paper_distribution': dict(Counter(papers))
        }
