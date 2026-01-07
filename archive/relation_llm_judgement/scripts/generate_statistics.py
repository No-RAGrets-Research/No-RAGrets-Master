"""
Generate statistics for an existing Phase 2 results directory.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage import ResultsStorage

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python generate_statistics.py <results_dir>")
        print("\nExample:")
        print("  python generate_statistics.py results/phase2_20251119_210025")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    
    print(f"Loading results from {results_dir}...")
    storage = ResultsStorage(results_dir)
    results = storage.load_results_full()
    
    print(f"Loaded {len(results)} relations")
    print("Generating statistics...")
    
    stats = storage.generate_statistics(results)
    
    print("\n" + "=" * 70)
    print("STATISTICS GENERATED")
    print("=" * 70)
    print(f"Saved to: {results_dir}/statistics.json")
    print()
    
    print("Model Performance Summary:")
    for model_name, model_stats in stats['by_model'].items():
        print(f"\n{model_name}:")
        print(f"  Accuracy: {model_stats.get('text_accuracy_rate', 0):.1%}")
        print(f"  Faithfulness: {model_stats.get('text_avg_faithfulness', 0):.2f}/5")
        print(f"  Boundary Quality: {model_stats.get('text_avg_boundary', 0):.2f}/5")
        print(f"  Avg time: {model_stats.get('text_avg_inference_time', 0):.2f}s")
