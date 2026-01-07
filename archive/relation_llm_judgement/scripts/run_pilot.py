#!/usr/bin/env python3
"""
Pilot Experiment Script

Runs Phase 1 of the LLM judge experiment:
- Fetch top 5 hub entities
- Sample 25-50 relations
- Run 2-3 judge models
- Save results
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_client import KnowledgeGraphClient
from sampler import RelationSampler
from alternative_sampler import AlternativeSampler
from judge import OllamaJudge
from storage import ResultsStorage
import json


def main():
    """Run the pilot experiment."""
    
    print("=" * 60)
    print("PILOT EXPERIMENT: LLM Judges for Relation Extraction")
    print("=" * 60)
    
    # Configuration
    NUM_HUB_ENTITIES = 20  # Fetch more initially, some may not have relations
    TARGET_RELATIONS = 30
    PER_ENTITY_MAX = 10
    
    TEXT_MODELS = [
        "llama3.2:3b",
        "mistral:7b",
        "llama3.1:8b"
    ]
    
    # Initialize components
    print("\n[1/7] Initializing API client...")
    client = KnowledgeGraphClient()
    
    # Health check
    try:
        health = client.health_check()
        print(f"   ✓ API Status: {health.get('status')}")
    except Exception as e:
        print(f"   ✗ Error connecting to API: {e}")
        print("   Make sure the Knowledge Graph API is running on http://localhost:8001")
        return
    
    print("\n[2/7] Sampling relations (using alternative method due to API limitations)...")
    # Use alternative sampler that works around API filter bugs
    alt_sampler = AlternativeSampler(client)
    sampled_relations = alt_sampler.sample_from_top_entities(
        n_entities=5,
        target_relations=TARGET_RELATIONS,
        per_entity_max=PER_ENTITY_MAX,
        max_fetch=1000
    )
    
    if not sampled_relations:
        print("   ✗ Error: No relations could be sampled")
        print("   This may indicate an issue with the API")
        return
    
    print(f"   ✓ Sampled {len(sampled_relations)} relations")
    
    # Analyze diversity (still need original sampler for this)
    sampler = RelationSampler(client)
    diversity = sampler.analyze_sample_diversity(sampled_relations)
    print(f"   - Unique predicates: {diversity['unique_predicates']}")
    print(f"   - Unique papers: {diversity['unique_papers']}")
    print(f"   - Unique sections: {diversity['unique_sections']}")
    
    print("\n[4/7] Enriching relations with context...")
    
    # Create output directory
    exp_dir = ResultsStorage.create_experiment_directory()
    image_dir = os.path.join(exp_dir, "images")
    
    enriched_relations = sampler.enrich_relations_with_context(
        relations=sampled_relations,
        include_source_span=True,
        include_provenance=True,
        include_image=False,  # Set to True if you want images for vision models
        image_output_dir=image_dir
    )
    
    print(f"   ✓ Enriched {len(enriched_relations)} relations")
    
    print("\n[5/7] Checking Ollama models...")
    judge = OllamaJudge(models=TEXT_MODELS)
    availability = judge.check_model_availability()
    
    print("   Model availability:")
    for model, available in availability.items():
        status = "✓" if available else "✗"
        print(f"      {status} {model}")
    
    # Pull missing models
    missing_models = [m for m, avail in availability.items() if not avail]
    if missing_models:
        print(f"\n   Pulling {len(missing_models)} missing models...")
        for model in missing_models:
            judge.pull_model_if_needed(model)
    
    print("\n[6/7] Running judgments...")
    print(f"   (This may take several minutes for {len(enriched_relations)} relations × {len(TEXT_MODELS)} models)")
    
    judged_relations = judge.batch_judge_relations(
        relations=enriched_relations,
        text_models=TEXT_MODELS,
        use_vision=False  # Set to True if you have vision models and images
    )
    
    print(f"   ✓ Completed {len(judged_relations)} relation judgments")
    
    print("\n[7/7] Saving results...")
    
    # Save full JSON
    json_path = os.path.join(exp_dir, "results_full.json")
    ResultsStorage.save_to_json(judged_relations, json_path)
    
    # Save flattened CSV
    csv_path = os.path.join(exp_dir, "results.csv")
    ResultsStorage.save_to_csv(judged_relations, csv_path)
    
    # Save diversity report
    diversity_path = os.path.join(exp_dir, "diversity_report.json")
    ResultsStorage.save_diversity_report(diversity, diversity_path)
    
    # Generate and save summary stats
    import pandas as pd
    df = pd.read_csv(csv_path)
    summary_stats = ResultsStorage.generate_summary_stats(df)
    
    summary_path = os.path.join(exp_dir, "summary_stats.json")
    with open(summary_path, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    print(f"\n   ✓ Results saved to: {exp_dir}")
    print(f"      - results.csv (flattened data)")
    print(f"      - results_full.json (complete data)")
    print(f"      - diversity_report.json")
    print(f"      - summary_stats.json")
    
    print("\n" + "=" * 60)
    print("PILOT EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Relations judged: {len(judged_relations)}")
    print(f"  - Hub entities used: 5")
    print(f"  - Models used: {len(TEXT_MODELS)}")
    print(f"  - Model agreement rate: {summary_stats.get('text_model_agreement_rate', 0):.2%}")
    print(f"\nNext steps:")
    print(f"  1. Review results in {csv_path}")
    print(f"  2. Manually annotate a subset for ground truth")
    print(f"  3. Analyze model performance and agreement")
    print(f"  4. Proceed to Phase 2 with more hub entities and relations")


if __name__ == "__main__":
    main()
