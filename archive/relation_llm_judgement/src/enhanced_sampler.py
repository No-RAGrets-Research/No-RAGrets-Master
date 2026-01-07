"""
Enhanced sampling strategies for more comprehensive relation evaluation.

Implements:
- Predicate-stratified sampling
- Paper-stratified sampling
- Confidence-stratified sampling
- Error-pattern targeted sampling
- Multi-strategy combination
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
import random
from api_client import KnowledgeGraphClient


class EnhancedSampler:
    """Enhanced sampler with multiple stratification strategies."""
    
    def __init__(self, client: KnowledgeGraphClient, seed: int = 42):
        """
        Initialize enhanced sampler.
        
        Args:
            client: Knowledge graph API client
            seed: Random seed for reproducibility
        """
        self.client = client
        random.seed(seed)
        self._all_relations_cache = None
        
    def _fetch_all_relations(self, limit: int = 2000) -> List[Dict[str, Any]]:
        """Fetch and cache all relations from the API."""
        if self._all_relations_cache is None:
            print(f"Fetching up to {limit} relations from API...")
            self._all_relations_cache = self.client.search_relations(
                limit=limit
            )
            print(f"Cached {len(self._all_relations_cache)} relations")
        return self._all_relations_cache
    
    def get_predicate_distribution(self) -> Dict[str, int]:
        """Get distribution of predicates across all relations."""
        relations = self._fetch_all_relations()
        predicates = [r.get('predicate', 'UNKNOWN') for r in relations]
        return dict(Counter(predicates))
    
    def get_paper_distribution(self) -> Dict[str, int]:
        """Get distribution of relations per paper."""
        relations = self._fetch_all_relations()
        papers = [r.get('source_paper', 'UNKNOWN') for r in relations]
        return dict(Counter(papers))
    
    def sample_by_predicate_stratified(
        self, 
        n_per_predicate: int = 5,
        top_n_predicates: Optional[int] = None,
        include_rare: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Sample evenly across predicate types.
        
        Args:
            n_per_predicate: Number of relations to sample per predicate
            top_n_predicates: Only sample from top N most common predicates (None = all)
            include_rare: If True, also sample rare predicates separately
            
        Returns:
            List of sampled relations with predicate distribution
        """
        relations = self._fetch_all_relations()
        
        # Group by predicate
        by_predicate = defaultdict(list)
        for rel in relations:
            predicate = rel.get('predicate', 'UNKNOWN')
            by_predicate[predicate].append(rel)
        
        # Get predicate ordering by frequency
        predicate_counts = Counter(r.get('predicate', 'UNKNOWN') for r in relations)
        sorted_predicates = [p for p, _ in predicate_counts.most_common()]
        
        sample = []
        
        # Sample from common predicates
        target_predicates = sorted_predicates[:top_n_predicates] if top_n_predicates else sorted_predicates
        
        for predicate in target_predicates:
            rels = by_predicate[predicate]
            n_sample = min(n_per_predicate, len(rels))
            sampled = random.sample(rels, n_sample)
            sample.extend(sampled)
        
        # Optionally add rare predicates
        if include_rare and top_n_predicates:
            rare_predicates = sorted_predicates[top_n_predicates:]
            for predicate in rare_predicates[:5]:  # Top 5 rare predicates
                rels = by_predicate[predicate]
                n_sample = min(n_per_predicate, len(rels))
                sampled = random.sample(rels, n_sample)
                sample.extend(sampled)
        
        print(f"Sampled {len(sample)} relations across {len(set(r.get('predicate') for r in sample))} predicates")
        return sample
    
    def sample_by_paper_stratified(
        self, 
        n_per_paper: int = 10,
        top_n_papers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Sample evenly across papers.
        
        Args:
            n_per_paper: Number of relations to sample per paper
            top_n_papers: Only sample from top N papers with most relations (None = all)
            
        Returns:
            List of sampled relations with paper distribution
        """
        relations = self._fetch_all_relations()
        
        # Group by paper
        by_paper = defaultdict(list)
        for rel in relations:
            paper = rel.get('source_paper', 'UNKNOWN')
            by_paper[paper].append(rel)
        
        # Get papers ordered by number of relations
        paper_counts = Counter(r.get('source_paper', 'UNKNOWN') for r in relations)
        sorted_papers = [p for p, _ in paper_counts.most_common(top_n_papers)]
        
        sample = []
        for paper_id in sorted_papers:
            rels = by_paper[paper_id]
            n_sample = min(n_per_paper, len(rels))
            sampled = random.sample(rels, n_sample)
            sample.extend(sampled)
        
        print(f"Sampled {len(sample)} relations across {len(set(r.get('paper_id') for r in sample))} papers")
        return sample
    
    def sample_by_confidence_stratified(
        self,
        n_per_bucket: int = 25,
        buckets: Optional[List[Tuple[float, float]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Sample across confidence score ranges.
        
        Args:
            n_per_bucket: Number of relations per confidence bucket
            buckets: List of (min, max) confidence ranges. Default:
                     [(0.0, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 1.0)]
            
        Returns:
            List of sampled relations across confidence ranges
        """
        if buckets is None:
            buckets = [(0.0, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 1.0)]
        
        relations = self._fetch_all_relations()
        
        # Group by confidence bucket
        by_bucket = defaultdict(list)
        for rel in relations:
            confidence = rel.get('confidence', 0.0) or 0.0  # Handle None values
            for min_conf, max_conf in buckets:
                if min_conf <= confidence < max_conf:
                    by_bucket[(min_conf, max_conf)].append(rel)
                    break
        
        sample = []
        for bucket in buckets:
            rels = by_bucket[bucket]
            if len(rels) == 0:
                print(f"Warning: No relations in bucket {bucket}")
                continue
            n_sample = min(n_per_bucket, len(rels))
            sampled = random.sample(rels, n_sample)
            sample.extend(sampled)
            print(f"Bucket {bucket}: sampled {n_sample}/{len(rels)} relations")
        
        print(f"Total sampled: {len(sample)} relations across {len(buckets)} confidence buckets")
        return sample
    
    def sample_by_error_patterns(
        self,
        patterns: Optional[List[str]] = None,
        n_per_pattern: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Sample relations containing known error-prone patterns.
        
        Args:
            patterns: List of patterns to search for. Default includes:
                     negations, conditionals, qualifiers, etc.
            n_per_pattern: Number of relations per pattern
            
        Returns:
            List of sampled relations containing target patterns
        """
        if patterns is None:
            patterns = [
                'NOT', 'cannot', 'does not', 'did not',  # Negations
                'if', 'when', 'under', 'conditions',      # Conditionals
                'some', 'most', 'potentially', 'may',     # Qualifiers
                'more than', 'less than', 'higher',       # Comparisons
                'before', 'after', 'during', 'then',      # Temporal
                'causes', 'leads to', 'results in'        # Causal
            ]
        
        relations = self._fetch_all_relations()
        
        # For each relation, fetch source text and check for patterns
        by_pattern = defaultdict(list)
        
        print(f"Analyzing {len(relations)} relations for error patterns...")
        for i, rel in enumerate(relations):
            if i > 0 and i % 100 == 0:
                print(f"  Analyzed {i}/{len(relations)} relations...")
            
            # Get source text
            rel_id = rel.get('id')
            if not rel_id:
                continue
                
            try:
                source_data = self.client.get_relation_source_span(rel_id)
                source_text = source_data.get('source_text', '').lower()
                
                # Check each pattern
                for pattern in patterns:
                    if pattern.lower() in source_text:
                        by_pattern[pattern].append(rel)
            except Exception as e:
                # Skip relations where we can't get source text
                continue
        
        sample = []
        for pattern in patterns:
            rels = by_pattern[pattern]
            if len(rels) == 0:
                print(f"Warning: No relations found with pattern '{pattern}'")
                continue
            n_sample = min(n_per_pattern, len(rels))
            sampled = random.sample(rels, n_sample)
            sample.extend(sampled)
            print(f"Pattern '{pattern}': sampled {n_sample}/{len(rels)} relations")
        
        # Deduplicate (same relation may match multiple patterns)
        seen_ids = set()
        deduplicated = []
        for rel in sample:
            rel_id = rel.get('id')
            if rel_id not in seen_ids:
                seen_ids.add(rel_id)
                deduplicated.append(rel)
        
        print(f"Total sampled: {len(deduplicated)} unique relations across {len(patterns)} patterns")
        return deduplicated
    
    def sample_random_baseline(self, n: int = 20) -> List[Dict[str, Any]]:
        """Sample completely random relations as baseline."""
        relations = self._fetch_all_relations()
        n_sample = min(n, len(relations))
        sample = random.sample(relations, n_sample)
        print(f"Sampled {len(sample)} random relations as baseline")
        return sample
    
    def sample_multi_strategy(
        self,
        predicate_stratified: int = 50,
        paper_stratified: int = 30,
        confidence_stratified: int = 40,
        error_patterns: int = 30,
        random_baseline: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Combine multiple sampling strategies for comprehensive coverage.
        
        Args:
            predicate_stratified: Number of relations for predicate sampling
            paper_stratified: Number for paper sampling
            confidence_stratified: Number for confidence sampling
            error_patterns: Number for error pattern sampling
            random_baseline: Number for random baseline
            
        Returns:
            Dict mapping strategy name to sampled relations
        """
        print("=" * 60)
        print("MULTI-STRATEGY SAMPLING")
        print("=" * 60)
        
        strategies = {}
        
        if predicate_stratified > 0:
            print("\n1. PREDICATE-STRATIFIED SAMPLING")
            print("-" * 60)
            strategies['predicate_stratified'] = self.sample_by_predicate_stratified(
                n_per_predicate=5,
                top_n_predicates=10,
                include_rare=True
            )[:predicate_stratified]
        
        if paper_stratified > 0:
            print("\n2. PAPER-STRATIFIED SAMPLING")
            print("-" * 60)
            strategies['paper_stratified'] = self.sample_by_paper_stratified(
                n_per_paper=15,  # 15 per paper × 2 papers = 30
                top_n_papers=None  # Use all available papers
            )[:paper_stratified]
        
        if confidence_stratified > 0:
            print("\n3. CONFIDENCE-STRATIFIED SAMPLING")
            print("-" * 60)
            strategies['confidence_stratified'] = self.sample_by_confidence_stratified(
                n_per_bucket=10
            )[:confidence_stratified]
        
        if error_patterns > 0:
            print("\n4. ERROR-PATTERN TARGETED SAMPLING")
            print("-" * 60)
            strategies['error_patterns'] = self.sample_by_error_patterns(
                n_per_pattern=5
            )[:error_patterns]
        
        if random_baseline > 0:
            print("\n5. RANDOM BASELINE SAMPLING")
            print("-" * 60)
            strategies['random_baseline'] = self.sample_random_baseline(random_baseline)
        
        # Combine and deduplicate
        all_samples = []
        for strategy_name, samples in strategies.items():
            for rel in samples:
                rel['sampling_strategy'] = strategy_name
                all_samples.append(rel)
        
        # Deduplicate by relation ID
        seen_ids = set()
        deduplicated = []
        strategy_counts = defaultdict(int)
        
        for rel in all_samples:
            rel_id = rel.get('id')
            if rel_id not in seen_ids:
                seen_ids.add(rel_id)
                deduplicated.append(rel)
                strategy_counts[rel['sampling_strategy']] += 1
        
        print("\n" + "=" * 60)
        print("MULTI-STRATEGY SUMMARY")
        print("=" * 60)
        print(f"Total unique relations: {len(deduplicated)}")
        for strategy, count in strategy_counts.items():
            print(f"  {strategy}: {count} relations")
        
        return {
            'all': deduplicated,
            'by_strategy': strategies,
            'summary': dict(strategy_counts)
        }
    
    def analyze_sample_diversity(self, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze diversity of sampled relations.
        
        Args:
            relations: List of relations to analyze
            
        Returns:
            Dict with diversity metrics
        """
        predicates = [r.get('predicate', 'UNKNOWN') for r in relations]
        papers = [r.get('source_paper', 'UNKNOWN') for r in relations]
        confidences = [r.get('confidence', 0.0) or 0.0 for r in relations]
        
        return {
            'total_relations': len(relations),
            'unique_predicates': len(set(predicates)),
            'unique_papers': len(set(papers)),
            'predicate_distribution': dict(Counter(predicates)),
            'paper_distribution': dict(Counter(papers)),
            'confidence_stats': {
                'mean': sum(confidences) / len(confidences) if confidences else 0,
                'min': min(confidences) if confidences else 0,
                'max': max(confidences) if confidences else 0,
            }
        }
