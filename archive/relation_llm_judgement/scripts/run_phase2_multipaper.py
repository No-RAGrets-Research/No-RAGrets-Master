"""
Phase 2 Experiment: Multi-paper sampling with diverse predicates.

Samples relations from 10+ different papers for better generalization.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_client import KnowledgeGraphClient
from multi_paper_sampler import MultiPaperSampler
from judge import OllamaJudge
from storage import ResultsStorage


def main():
    """Run Phase 2 experiment with multi-paper sampling."""
    
    # Load environment
    load_dotenv()
    api_base_url = os.getenv('KNOWLEDGE_GRAPH_API_URL', 'http://localhost:8001/api')
    
    # Configuration
    TARGET_SAMPLE_SIZE = 100
    N_PAPERS = 10  # Sample from 10 different papers
    MODELS_TO_TEST = [
        'llama3.1:8b',         # Meta - Best performer from initial testing
        'mistral:7b',          # Mistral AI - Alternative perspective
        'phi3:3.8b',           # Microsoft - Strong reasoning
        'gemma2:9b',           # Google - Instruction following
        'qwen2.5:1.5b',        # Alibaba - Fast inference
        'deepseek-coder:6.7b'  # DeepSeek - Logical reasoning
    ]
    
    print("=" * 70)
    print("PHASE 2 EXPERIMENT: MULTI-PAPER SAMPLING")
    print("=" * 70)
    print(f"Target sample size: {TARGET_SAMPLE_SIZE}")
    print(f"Number of papers: {N_PAPERS}")
    print(f"Models: {', '.join(MODELS_TO_TEST)}")
    print("=" * 70)
    print()
    
    # Initialize components
    print("Phase 1: Initialize components")
    print("-" * 70)
    client = KnowledgeGraphClient(api_base_url)
    sampler = MultiPaperSampler(client, seed=42)
    judge = OllamaJudge(models=MODELS_TO_TEST)
    
    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/phase2_multipaper_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    storage = ResultsStorage(results_dir)
    print(f"✓ Results directory: {results_dir}")
    print()
    
    # Phase 2: Sample across papers
    print("Phase 2: Sample relations from multiple papers")
    print("-" * 70)
    sampled_relations = sampler.sample_across_papers(
        n_relations=TARGET_SAMPLE_SIZE,
        n_papers=N_PAPERS,
        min_relations_per_paper=10
    )
    print()
    
    # Phase 3: Analyze diversity
    print("Phase 3: Analyze sample diversity")
    print("-" * 70)
    diversity = sampler.analyze_diversity(sampled_relations)
    print(f"Total relations: {diversity['total_relations']}")
    print(f"Unique papers: {diversity['unique_papers']}")
    print(f"Unique predicates: {diversity['unique_predicates']}")
    print()
    print("Top 10 predicates:")
    for pred, count in list(diversity['predicate_distribution'].items())[:10]:
        print(f"  {pred}: {count}")
    print()
    print("Paper distribution:")
    for paper, count in diversity['paper_distribution'].items():
        print(f"  {paper[:50]}...: {count}")
    print()
    
    # Phase 4: Check model availability
    print("Phase 4: Check model availability")
    print("-" * 70)
    availability = judge.check_model_availability()
    for model_name, is_available in availability.items():
        if not is_available:
            print(f"  Pulling {model_name}...")
            judge.pull_model_if_needed(model_name)
        else:
            print(f"  ✓ {model_name} available")
    print()
    
    # Phase 5: Enrich with source spans and filter
    print("Phase 5: Enrich relations with source spans")
    print("-" * 70)
    valid_relations = []
    skipped_count = 0
    
    for i, rel in enumerate(sampled_relations):
        if i > 0 and i % 10 == 0:
            print(f"  Enriched {i}/{len(sampled_relations)} relations... ({len(valid_relations)} valid, {skipped_count} skipped)")
        
        rel_id = rel.get('id')
        if rel_id:
            try:
                source_data = client.get_relation_source_span(rel_id)
                text_evidence = source_data.get('source_span', {}).get('text_evidence')
                
                if text_evidence and text_evidence.strip():
                    rel['source_span'] = source_data
                    valid_relations.append(rel)
                else:
                    skipped_count += 1
            except Exception as e:
                skipped_count += 1
                if i < 10:  # Only print first few errors
                    if '500' in str(e):
                        print(f"  Skipping relation {rel_id}: API error (500)")
    
    print(f"✓ Enriched {len(valid_relations)} valid relations ({skipped_count} skipped)")
    print()
    
    if len(valid_relations) == 0:
        print("ERROR: No valid relations with source spans found!")
        return
    
    # Phase 6: Batch judgment
    print("Phase 6: Batch judgment")
    print("-" * 70)
    print(f"Judging {len(valid_relations)} relations × {len(MODELS_TO_TEST)} models")
    print(f"Estimated time: ~{len(valid_relations) * len(MODELS_TO_TEST) * 5 / 60:.1f} minutes")
    print()
    
    results = judge.batch_judge_relations(
        relations=valid_relations,
        text_models=MODELS_TO_TEST,
        use_vision=False
    )
    
    print()
    print(f"✓ Completed {len(results)} relation judgments")
    print()
    
    # Phase 7: Save results
    print("Phase 7: Save results")
    print("-" * 70)
    
    storage.save_results_full(results)
    print(f"✓ Saved full results")
    
    storage.save_results_csv(results)
    print(f"✓ Saved summary CSV")
    
    stats = storage.generate_statistics(results)
    print(f"✓ Saved statistics")
    print()
    
    # Phase 8: Print summary
    print("=" * 70)
    print("PHASE 2 EXPERIMENT COMPLETE")
    print("=" * 70)
    print(f"Relations sampled: {len(sampled_relations)}")
    print(f"Relations with valid source spans: {len(results)}")
    print(f"Relations skipped: {skipped_count}")
    print(f"Unique papers: {diversity['unique_papers']}")
    print(f"Unique predicates: {diversity['unique_predicates']}")
    print(f"Models used: {len(MODELS_TO_TEST)}")
    print(f"Total judgments: {len(results) * len(MODELS_TO_TEST)}")
    print()
    
    print("Model Performance Summary:")
    for model_name, model_stats in stats['by_model'].items():
        print(f"\n{model_name}:")
        print(f"  Accuracy: {model_stats.get('text_accuracy_rate', 0):.1%}")
        print(f"  Faithfulness: {model_stats.get('text_avg_faithfulness', 0):.2f}/5")
        print(f"  Boundary Quality: {model_stats.get('text_avg_boundary', 0):.2f}/5")
        print(f"  Avg time: {model_stats.get('text_avg_inference_time', 0):.2f}s")
    
    print()
    print(f"Results saved to: {results_dir}/")
    print()


if __name__ == '__main__':
    main()
