"""
Phase 2 Experiment: Large-scale relation quality evaluation with enhanced sampling.

This expands on the pilot study with:
- 100-200 relations (vs 30 in pilot)
- Multiple sampling strategies (predicate, paper, confidence, error-pattern)
- Same judgment criteria for comparison
- Enhanced diversity analysis
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_client import KnowledgeGraphClient
from enhanced_sampler import EnhancedSampler
from judge import OllamaJudge
from storage import ResultsStorage


def main():
    """Run Phase 2 large-scale experiment."""
    
    # Load environment
    load_dotenv()
    api_base_url = os.getenv('KNOWLEDGE_GRAPH_API_URL', 'http://localhost:8001/api')
    
    # Configuration
    TARGET_SAMPLE_SIZE = 100  # Can increase to 200 for Phase 2B
    MODELS_TO_TEST = [
        'llama3.2:3b',   # Best performer from pilot
        'mistral:7b',    # For comparison
        'llama3.1:8b'    # For comparison
    ]
    
    # Multi-strategy distribution
    STRATEGY_DISTRIBUTION = {
        'predicate_stratified': 40,   # 40 relations across predicates
        'paper_stratified': 30,       # 30 relations across papers (15 per paper × 2 papers)
        'confidence_stratified': 0,   # 0 (confidence field is None for all)
        'error_patterns': 0,          # 0 for now (slow - requires fetching source text)
        'random_baseline': 30         # 30 completely random
    }
    
    print("=" * 70)
    print("PHASE 2 EXPERIMENT: ENHANCED SAMPLING")
    print("=" * 70)
    print(f"Target sample size: {TARGET_SAMPLE_SIZE}")
    print(f"Models: {', '.join(MODELS_TO_TEST)}")
    print(f"Strategies: {STRATEGY_DISTRIBUTION}")
    print("=" * 70)
    print()
    
    # Initialize components
    print("Phase 1: Initialize components")
    print("-" * 70)
    client = KnowledgeGraphClient(api_base_url)
    sampler = EnhancedSampler(client, seed=42)
    judge = OllamaJudge(models=MODELS_TO_TEST)  # Initialize with target models
    
    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/phase2_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    storage = ResultsStorage(results_dir)
    print(f"✓ Results directory: {results_dir}")
    print()
    
    # Phase 2: Analyze available data
    print("Phase 2: Analyze available relations")
    print("-" * 70)
    print("Predicate distribution:")
    predicate_dist = sampler.get_predicate_distribution()
    for pred, count in sorted(predicate_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {pred}: {count}")
    print(f"  ... ({len(predicate_dist)} total predicates)")
    print()
    
    print("Paper distribution:")
    paper_dist = sampler.get_paper_distribution()
    for paper, count in sorted(paper_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {paper}: {count}")
    print(f"  ... ({len(paper_dist)} total papers)")
    print()
    
    # Phase 3: Multi-strategy sampling
    print("Phase 3: Multi-strategy sampling")
    print("-" * 70)
    sample_result = sampler.sample_multi_strategy(**STRATEGY_DISTRIBUTION)
    sampled_relations = sample_result['all']
    
    # Trim to target size if needed
    if len(sampled_relations) > TARGET_SAMPLE_SIZE:
        print(f"Trimming sample from {len(sampled_relations)} to {TARGET_SAMPLE_SIZE}")
        sampled_relations = sampled_relations[:TARGET_SAMPLE_SIZE]
    
    print(f"✓ Final sample size: {len(sampled_relations)}")
    print()
    
    # Phase 4: Analyze sample diversity
    print("Phase 4: Analyze sample diversity")
    print("-" * 70)
    diversity = sampler.analyze_sample_diversity(sampled_relations)
    print(f"Total relations: {diversity['total_relations']}")
    print(f"Unique predicates: {diversity['unique_predicates']}")
    print(f"Unique papers: {diversity['unique_papers']}")
    print(f"Confidence range: {diversity['confidence_stats']['min']:.3f} - {diversity['confidence_stats']['max']:.3f}")
    print(f"Mean confidence: {diversity['confidence_stats']['mean']:.3f}")
    print()
    
    print("Top predicates in sample:")
    for pred, count in sorted(diversity['predicate_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {pred}: {count}")
    print()
    
    print("Papers in sample:")
    for paper, count in sorted(diversity['paper_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {paper}: {count}")
    print()
    
    # Save sampling report
    sampling_report = {
        'timestamp': timestamp,
        'target_size': TARGET_SAMPLE_SIZE,
        'actual_size': len(sampled_relations),
        'strategy_distribution': STRATEGY_DISTRIBUTION,
        'diversity_metrics': diversity,
        'strategy_summary': sample_result['summary']
    }
    storage.save_sampling_report(sampling_report)
    print(f"✓ Saved sampling report to {results_dir}/sampling_report.json")
    print()
    
    # Phase 5: Check model availability
    print("Phase 5: Check model availability")
    print("-" * 70)
    
    # Check availability for all models
    availability = judge.check_model_availability()
    for model_name, is_available in availability.items():
        if not is_available:
            print(f"  Pulling {model_name}...")
            judge.pull_model_if_needed(model_name)
        else:
            print(f"  ✓ {model_name} available")
    print()
    
    # Phase 6: Batch judgment (text-based only)
    print("Phase 6: Batch judgment")
    print("-" * 70)
    print(f"Judging {len(sampled_relations)} relations × {len(MODELS_TO_TEST)} models")
    print(f"Estimated time: ~{len(sampled_relations) * len(MODELS_TO_TEST) * 5 / 60:.1f} minutes")
    print()
    
    # Enrich relations with source span data before judging
    print("Enriching relations with source spans...")
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
                
                # Only include if we have text evidence
                if text_evidence and text_evidence.strip():
                    rel['source_span'] = source_data
                    valid_relations.append(rel)
                else:
                    skipped_count += 1
                    print(f"  Skipping relation {rel_id}: no text evidence")
            except Exception as e:
                skipped_count += 1
                if '500' in str(e):
                    print(f"  Skipping relation {rel_id}: API error (500)")
                else:
                    print(f"  Skipping relation {rel_id}: {e}")
    
    print(f"✓ Enriched {len(valid_relations)} valid relations ({skipped_count} skipped due to missing source spans)")
    print()
    
    if len(valid_relations) == 0:
        print("ERROR: No valid relations with source spans found!")
        return
    
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
    
    # Save full results
    storage.save_results_full(results)
    print(f"✓ Saved full results to {results_dir}/results_full.json")
    
    # Save summary CSV
    storage.save_results_csv(results)
    print(f"✓ Saved summary to {results_dir}/results_summary.csv")
    
    # Generate statistics
    stats = storage.generate_statistics(results)
    print(f"✓ Saved statistics to {results_dir}/statistics.json")
    print()
    
    # Phase 8: Print summary
    print("=" * 70)
    print("PHASE 2 EXPERIMENT COMPLETE")
    print("=" * 70)
    print(f"Relations sampled: {len(sampled_relations)}")
    print(f"Relations with valid source spans: {len(results)}")
    print(f"Relations skipped (no source span): {len(sampled_relations) - len(results)}")
    print(f"Models used: {len(MODELS_TO_TEST)}")
    print(f"Total judgments: {len(results) * len(MODELS_TO_TEST)}")
    print()
    
    print("Model Performance Summary:")
    for model_name, model_stats in stats['by_model'].items():
        print(f"\n{model_name}:")
        print(f"  Accuracy: {model_stats['text_accuracy_rate']:.1%}")
        print(f"  Faithfulness: {model_stats['text_avg_faithfulness']:.2f}/5")
        print(f"  Boundary Quality: {model_stats['text_avg_boundary']:.2f}/5")
        print(f"  Avg time: {model_stats['text_avg_inference_time']:.2f}s")
    
    print()
    print(f"Results saved to: {results_dir}/")
    print()
    
    # Compare to Phase 1 if available
    print("=" * 70)
    print("COMPARISON TO PHASE 1 (PILOT)")
    print("=" * 70)
    print("Phase 1 (30 relations):")
    print("  - Hub entity sampling only")
    print("  - 90% three-way agreement")
    print("  - High faithfulness (4.80-5.00/5)")
    print()
    print("Phase 2 ({} relations):".format(len(results)))
    print("  - Multi-strategy sampling (predicate, paper, confidence, random)")
    print("  - {} unique predicates (vs ~3 in Phase 1)".format(diversity['unique_predicates']))
    print("  - {} unique papers (vs ~1 in Phase 1)".format(diversity['unique_papers']))
    print("  - More challenging sample expected")
    print()
    print("Next steps:")
    print("  1. Analyze disagreements and failure patterns")
    print("  2. Compare metrics across sampling strategies")
    print("  3. Manual annotation of disagreements")
    print("  4. Consider Phase 2B expansion to 200 relations")
    print()


if __name__ == '__main__':
    main()
