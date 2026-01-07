"""
Compare results between Phase 1 (pilot) and Phase 2 (enhanced sampling).

Analyzes differences in:
- Model agreement rates
- Accuracy distributions
- Faithfulness scores
- Per-predicate performance
- Per-paper performance
- Sampling strategy effectiveness
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List


def load_experiment_results(results_dir: str) -> Dict[str, Any]:
    """Load experiment results from a directory."""
    results_path = Path(results_dir)
    
    # Load full results
    with open(results_path / "results_full.json", 'r') as f:
        full_results = json.load(f)
    
    # Load statistics if available
    stats_path = results_path / "statistics.json"
    if stats_path.exists():
        with open(stats_path, 'r') as f:
            statistics = json.load(f)
    else:
        statistics = {}
    
    # Load sampling report if available (Phase 2 only)
    sampling_path = results_path / "sampling_report.json"
    if sampling_path.exists():
        with open(sampling_path, 'r') as f:
            sampling_report = json.load(f)
    else:
        sampling_report = {}
    
    return {
        'results': full_results,
        'statistics': statistics,
        'sampling_report': sampling_report,
        'path': str(results_path)
    }


def analyze_agreement(results: List[Dict[str, Any]], models: List[str]) -> Dict[str, Any]:
    """Analyze inter-model agreement."""
    agreement_stats = {
        'two_way': defaultdict(int),
        'three_way': 0,
        'disagreements': []
    }
    
    total = len(results)
    
    for rel in results:
        text_judgments = rel.get('text_judgments', {})
        
        # Get accuracy verdicts for each model
        accuracies = {
            model: text_judgments.get(model, {}).get('parsed', {}).get('accuracy', None)
            for model in models
        }
        
        # Skip if any model didn't provide judgment
        if None in accuracies.values():
            continue
        
        # Check pairwise agreement
        model_pairs = [
            (models[0], models[1]),
            (models[0], models[2]),
            (models[1], models[2])
        ]
        
        for m1, m2 in model_pairs:
            if accuracies[m1] == accuracies[m2]:
                agreement_stats['two_way'][f"{m1}↔{m2}"] += 1
        
        # Check three-way agreement
        if len(set(accuracies.values())) == 1:
            agreement_stats['three_way'] += 1
        else:
            agreement_stats['disagreements'].append({
                'relation_id': rel.get('id'),
                'triple': f"{rel.get('subject', {}).get('name')} → {rel.get('predicate')} → {rel.get('object', {}).get('name')}",
                'judgments': accuracies
            })
    
    # Convert to percentages
    agreement_stats['two_way_pct'] = {
        pair: (count / total * 100) for pair, count in agreement_stats['two_way'].items()
    }
    agreement_stats['three_way_pct'] = agreement_stats['three_way'] / total * 100
    agreement_stats['total_relations'] = total
    
    return agreement_stats


def analyze_by_predicate(results: List[Dict[str, Any]], models: List[str]) -> pd.DataFrame:
    """Analyze performance grouped by predicate."""
    by_predicate = defaultdict(lambda: {
        'count': 0,
        'accuracy_sum': defaultdict(int),
        'faithfulness_sum': defaultdict(float),
        'disagreements': 0
    })
    
    for rel in results:
        predicate = rel.get('predicate', 'UNKNOWN')
        text_judgments = rel.get('text_judgments', {})
        
        by_predicate[predicate]['count'] += 1
        
        # Collect judgments
        accuracies = []
        for model in models:
            judgment = text_judgments.get(model, {}).get('parsed', {})
            accuracy = judgment.get('accuracy')
            faithfulness = judgment.get('faithfulness')
            
            if accuracy is not None:
                by_predicate[predicate]['accuracy_sum'][model] += (1 if accuracy == 'ACCURATE' else 0)
                accuracies.append(accuracy)
            if faithfulness is not None:
                by_predicate[predicate]['faithfulness_sum'][model] += faithfulness
        
        # Check for disagreement
        if len(set(accuracies)) > 1:
            by_predicate[predicate]['disagreements'] += 1
    
    # Convert to DataFrame
    rows = []
    for predicate, stats in by_predicate.items():
        count = stats['count']
        row = {
            'predicate': predicate,
            'count': count,
            'disagreement_rate': stats['disagreements'] / count if count > 0 else 0
        }
        
        for model in models:
            row[f'{model}_accuracy'] = stats['accuracy_sum'][model] / count if count > 0 else 0
            row[f'{model}_faithfulness'] = stats['faithfulness_sum'][model] / count if count > 0 else 0
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df = df.sort_values('count', ascending=False)
    return df


def analyze_by_sampling_strategy(results: List[Dict[str, Any]], models: List[str]) -> pd.DataFrame:
    """Analyze performance by sampling strategy (Phase 2 only)."""
    by_strategy = defaultdict(lambda: {
        'count': 0,
        'accuracy_sum': defaultdict(int),
        'faithfulness_sum': defaultdict(float),
        'disagreements': 0
    })
    
    for rel in results:
        strategy = rel.get('sampling_strategy', 'unknown')
        text_judgments = rel.get('text_judgments', {})
        
        by_strategy[strategy]['count'] += 1
        
        # Collect judgments
        accuracies = []
        for model in models:
            judgment = text_judgments.get(model, {}).get('parsed', {})
            accuracy = judgment.get('accuracy')
            faithfulness = judgment.get('faithfulness')
            
            if accuracy is not None:
                by_strategy[strategy]['accuracy_sum'][model] += (1 if accuracy == 'ACCURATE' else 0)
                accuracies.append(accuracy)
            if faithfulness is not None:
                by_strategy[strategy]['faithfulness_sum'][model] += faithfulness
        
        # Check for disagreement
        if len(set(accuracies)) > 1:
            by_strategy[strategy]['disagreements'] += 1
    
    # Convert to DataFrame
    rows = []
    for strategy, stats in by_strategy.items():
        count = stats['count']
        row = {
            'sampling_strategy': strategy,
            'count': count,
            'disagreement_rate': stats['disagreements'] / count if count > 0 else 0
        }
        
        for model in models:
            row[f'{model}_accuracy'] = stats['accuracy_sum'][model] / count if count > 0 else 0
            row[f'{model}_faithfulness'] = stats['faithfulness_sum'][model] / count if count > 0 else 0
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df = df.sort_values('count', ascending=False)
    return df


def compare_experiments(phase1_dir: str, phase2_dir: str) -> None:
    """Compare Phase 1 and Phase 2 experiments."""
    
    print("=" * 80)
    print("PHASE 1 VS PHASE 2 COMPARISON")
    print("=" * 80)
    print()
    
    # Load results
    phase1 = load_experiment_results(phase1_dir)
    phase2 = load_experiment_results(phase2_dir)
    
    models = ['llama3.2:3b', 'mistral:7b', 'llama3.1:8b']
    
    # Basic stats
    print("SAMPLE SIZE")
    print("-" * 80)
    print(f"Phase 1: {len(phase1['results'])} relations")
    print(f"Phase 2: {len(phase2['results'])} relations")
    print(f"Increase: {len(phase2['results']) - len(phase1['results'])} relations ({len(phase2['results']) / len(phase1['results']):.1f}x)")
    print()
    
    # Agreement analysis
    print("INTER-MODEL AGREEMENT")
    print("-" * 80)
    
    phase1_agreement = analyze_agreement(phase1['results'], models)
    phase2_agreement = analyze_agreement(phase2['results'], models)
    
    print("Phase 1:")
    print(f"  Three-way agreement: {phase1_agreement['three_way_pct']:.1f}%")
    for pair, pct in phase1_agreement['two_way_pct'].items():
        print(f"  {pair}: {pct:.1f}%")
    print(f"  Disagreements: {len(phase1_agreement['disagreements'])}")
    print()
    
    print("Phase 2:")
    print(f"  Three-way agreement: {phase2_agreement['three_way_pct']:.1f}%")
    for pair, pct in phase2_agreement['two_way_pct'].items():
        print(f"  {pair}: {pct:.1f}%")
    print(f"  Disagreements: {len(phase2_agreement['disagreements'])}")
    print()
    
    # Model performance comparison
    print("MODEL PERFORMANCE")
    print("-" * 80)
    
    for model in models:
        print(f"\n{model}:")
        
        p1_stats = phase1['statistics'].get('by_model', {}).get(model, {})
        p2_stats = phase2['statistics'].get('by_model', {}).get(model, {})
        
        p1_acc = p1_stats.get('text_accuracy_rate', 0)
        p2_acc = p2_stats.get('text_accuracy_rate', 0)
        print(f"  Accuracy: {p1_acc:.1%} → {p2_acc:.1%} (Δ {p2_acc - p1_acc:+.1%})")
        
        p1_faith = p1_stats.get('text_avg_faithfulness', 0)
        p2_faith = p2_stats.get('text_avg_faithfulness', 0)
        print(f"  Faithfulness: {p1_faith:.2f} → {p2_faith:.2f} (Δ {p2_faith - p1_faith:+.2f})")
        
        p1_bound = p1_stats.get('text_avg_boundary', 0)
        p2_bound = p2_stats.get('text_avg_boundary', 0)
        print(f"  Boundary: {p1_bound:.2f} → {p2_bound:.2f} (Δ {p2_bound - p1_bound:+.2f})")
    
    print()
    
    # Predicate analysis
    print("PREDICATE DISTRIBUTION & PERFORMANCE")
    print("-" * 80)
    
    phase1_by_pred = analyze_by_predicate(phase1['results'], models)
    phase2_by_pred = analyze_by_predicate(phase2['results'], models)
    
    print("Phase 1 - Top predicates:")
    print(phase1_by_pred[['predicate', 'count', 'disagreement_rate']].head(10).to_string(index=False))
    print()
    
    print("Phase 2 - Top predicates:")
    print(phase2_by_pred[['predicate', 'count', 'disagreement_rate']].head(10).to_string(index=False))
    print()
    
    # Sampling strategy analysis (Phase 2 only)
    if 'sampling_strategy' in phase2['results'][0]:
        print("SAMPLING STRATEGY ANALYSIS (PHASE 2)")
        print("-" * 80)
        
        phase2_by_strategy = analyze_by_sampling_strategy(phase2['results'], models)
        print(phase2_by_strategy.to_string(index=False))
        print()
    
    # Diversity comparison
    print("SAMPLE DIVERSITY")
    print("-" * 80)
    
    p1_preds = len(set(r.get('predicate') for r in phase1['results']))
    p2_preds = len(set(r.get('predicate') for r in phase2['results']))
    print(f"Unique predicates: {p1_preds} → {p2_preds} (Δ {p2_preds - p1_preds:+})")
    
    p1_papers = len(set(r.get('paper_id', 'UNKNOWN') for r in phase1['results']))
    p2_papers = len(set(r.get('paper_id', 'UNKNOWN') for r in phase2['results']))
    print(f"Unique papers: {p1_papers} → {p2_papers} (Δ {p2_papers - p1_papers:+})")
    print()
    
    # Key insights
    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    
    agreement_change = phase2_agreement['three_way_pct'] - phase1_agreement['three_way_pct']
    if agreement_change < -5:
        print(f"⚠️  Agreement decreased by {abs(agreement_change):.1f}% - more diverse sample reveals edge cases")
    elif agreement_change > 5:
        print(f"✓ Agreement increased by {agreement_change:.1f}% - models more consistent on varied data")
    else:
        print(f"→ Agreement stable ({agreement_change:+.1f}%) - consistent model behavior")
    
    print()
    
    # Check if any model had significant performance change
    for model in models:
        p1_acc = phase1['statistics'].get('by_model', {}).get(model, {}).get('text_accuracy_rate', 0)
        p2_acc = phase2['statistics'].get('by_model', {}).get(model, {}).get('text_accuracy_rate', 0)
        acc_change = p2_acc - p1_acc
        
        if acc_change < -0.10:
            print(f"⚠️  {model} accuracy dropped {abs(acc_change):.1%} - struggling with diverse samples")
        elif acc_change > 0.10:
            print(f"✓ {model} accuracy improved {acc_change:.1%} - better generalization")
    
    print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python compare_phases.py <phase1_dir> <phase2_dir>")
        print("\nExample:")
        print("  python compare_phases.py results/pilot_20251119_193809 results/phase2_20251119_210000")
        sys.exit(1)
    
    phase1_dir = sys.argv[1]
    phase2_dir = sys.argv[2]
    
    compare_experiments(phase1_dir, phase2_dir)
