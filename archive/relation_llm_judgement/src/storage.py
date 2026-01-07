"""
Data Storage Utilities

Handles saving and loading experiment results in various formats.
"""

import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import os


class ResultsStorage:
    """Handles storage of experiment results."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize ResultsStorage.
        
        Args:
            output_dir: Directory to save results. If None, uses static methods.
        """
        self.output_dir = output_dir
    
    @staticmethod
    def flatten_judgments_for_csv(relations: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Flatten judged relations into a CSV-friendly format.
        
        Args:
            relations: List of relations with judgment data
            
        Returns:
            Pandas DataFrame
        """
        rows = []
        
        for rel in relations:
            # Base relation data
            row = {
                "relation_id": rel.get("id"),
                "subject": rel.get("subject", {}).get("name"),
                "predicate": rel.get("predicate"),
                "object": rel.get("object", {}).get("name"),
                "hub_entity": rel.get("hub_entity"),
                "hub_connectivity": rel.get("hub_connectivity"),
                "confidence": rel.get("confidence"),
                "section": rel.get("section"),
                "source_paper": rel.get("source_paper"),
            }
            
            # Source span info
            source_span = rel.get("source_span", {}).get("source_span", {})
            row["source_text"] = source_span.get("text_evidence")
            
            # Text judgments
            text_judgments = rel.get("text_judgments", {})
            for model_name, judgment in text_judgments.items():
                prefix = f"{model_name.replace(':', '_')}_text"
                parsed = judgment.get("parsed", {})
                
                row[f"{prefix}_accuracy"] = parsed.get("accuracy")
                row[f"{prefix}_faithfulness"] = parsed.get("faithfulness")
                row[f"{prefix}_boundary_quality"] = parsed.get("boundary_quality")
                row[f"{prefix}_justification"] = parsed.get("justification")
                row[f"{prefix}_inference_time"] = judgment.get("inference_time")
                row[f"{prefix}_error"] = judgment.get("error")
            
            # Vision judgments
            vision_judgments = rel.get("vision_judgments", {})
            for model_name, judgment in vision_judgments.items():
                prefix = f"{model_name.replace(':', '_')}_vision"
                parsed = judgment.get("parsed", {})
                
                row[f"{prefix}_found"] = parsed.get("found")
                row[f"{prefix}_quality"] = parsed.get("quality")
                row[f"{prefix}_explanation"] = parsed.get("explanation")
                row[f"{prefix}_inference_time"] = judgment.get("inference_time")
                row[f"{prefix}_error"] = judgment.get("error")
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def save_to_csv(
        relations: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        """
        Save judged relations to CSV.
        
        Args:
            relations: List of relations with judgment data
            output_path: Path to save CSV file
        """
        df = ResultsStorage.flatten_judgments_for_csv(relations)
        df.to_csv(output_path, index=False)
        print(f"Saved results to {output_path}")
    
    @staticmethod
    def save_to_json(
        relations: List[Dict[str, Any]],
        output_path: str,
        indent: int = 2
    ) -> None:
        """
        Save judged relations to JSON (preserves full structure).
        
        Args:
            relations: List of relations with judgment data
            output_path: Path to save JSON file
            indent: JSON indentation level
        """
        with open(output_path, 'w') as f:
            json.dump(relations, f, indent=indent, default=str)
        print(f"Saved full results to {output_path}")
    
    @staticmethod
    def save_diversity_report(
        diversity_stats: Dict[str, Any],
        output_path: str
    ) -> None:
        """
        Save diversity analysis report.
        
        Args:
            diversity_stats: Diversity metrics dictionary
            output_path: Path to save report
        """
        with open(output_path, 'w') as f:
            json.dump(diversity_stats, f, indent=2)
        print(f"Saved diversity report to {output_path}")
    
    def save_sampling_report(self, report: Dict[str, Any]) -> None:
        """
        Save sampling strategy report.
        
        Args:
            report: Sampling report dictionary with strategy distribution and metrics
        """
        output_path = os.path.join(self.output_dir, "sampling_report.json")
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Saved sampling report to {output_path}")
    
    @staticmethod
    def create_experiment_directory(base_dir: str = "results") -> str:
        """
        Create a timestamped directory for experiment results.
        
        Args:
            base_dir: Base directory for results
            
        Returns:
            Path to created directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_dir = os.path.join(base_dir, f"pilot_{timestamp}")
        
        os.makedirs(exp_dir, exist_ok=True)
        os.makedirs(os.path.join(exp_dir, "images"), exist_ok=True)
        
        return exp_dir
    
    @staticmethod
    def load_from_json(input_path: str) -> List[Dict[str, Any]]:
        """
        Load relations from JSON file.
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            List of relation dictionaries
        """
        with open(input_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def load_from_csv(input_path: str) -> pd.DataFrame:
        """
        Load relations from CSV file.
        
        Args:
            input_path: Path to CSV file
            
        Returns:
            Pandas DataFrame
        """
        return pd.read_csv(input_path)
    
    @staticmethod
    def generate_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics from judged relations DataFrame.
        
        Args:
            df: DataFrame with judgment results
            
        Returns:
            Dictionary with summary stats
        """
        stats = {
            "total_relations": len(df),
            "unique_hubs": df["hub_entity"].nunique(),
            "unique_predicates": df["predicate"].nunique(),
            "unique_papers": df["source_paper"].nunique(),
        }
        
        # Calculate agreement metrics for text models
        text_accuracy_cols = [col for col in df.columns if col.endswith("_text_accuracy")]
        
        if text_accuracy_cols:
            # Percentage of relations where all models agreed (accuracy)
            accuracy_agreement = df[text_accuracy_cols].apply(
                lambda row: len(set(row.dropna())) == 1,
                axis=1
            ).mean()
            stats["text_model_agreement_rate"] = accuracy_agreement
            
            # Average accuracy rate across models
            for col in text_accuracy_cols:
                model_name = col.replace("_text_accuracy", "")
                stats[f"{model_name}_accuracy_rate"] = df[col].mean()
        
        return stats
    
    # Instance methods for convenient use with output_dir
    
    def save_results_full(self, relations: List[Dict[str, Any]]) -> None:
        """Save full results to JSON in the output directory."""
        if self.output_dir is None:
            raise ValueError("output_dir not set. Use static methods or initialize with output_dir.")
        output_path = os.path.join(self.output_dir, "results_full.json")
        self.save_to_json(relations, output_path)
    
    def save_results_csv(self, relations: List[Dict[str, Any]]) -> None:
        """Save results summary to CSV in the output directory."""
        if self.output_dir is None:
            raise ValueError("output_dir not set. Use static methods or initialize with output_dir.")
        output_path = os.path.join(self.output_dir, "results_summary.csv")
        self.save_to_csv(relations, output_path)
    
    def load_results_full(self) -> List[Dict[str, Any]]:
        """Load full results from JSON in the output directory."""
        if self.output_dir is None:
            raise ValueError("output_dir not set. Use static methods or initialize with output_dir.")
        input_path = os.path.join(self.output_dir, "results_full.json")
        return self.load_from_json(input_path)
    
    def generate_statistics(self, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate and save statistics in the output directory."""
        if self.output_dir is None:
            raise ValueError("output_dir not set. Use static methods or initialize with output_dir.")
        
        # Flatten to DataFrame
        df = self.flatten_judgments_for_csv(relations)
        
        # Generate stats
        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_relations": len(relations),
            "by_model": {}
        }
        
        # Get unique models
        if relations:
            text_judgments = relations[0].get('text_judgments', {})
            models = list(text_judgments.keys())
            
            for model in models:
                model_stats = {
                    "text_accuracy_rate": 0,
                    "text_avg_faithfulness": 0,
                    "text_avg_boundary": 0,
                    "text_avg_inference_time": 0,
                    "text_error_count": 0
                }
                
                accurate_count = 0
                faith_sum = 0
                bound_sum = 0
                time_sum = 0
                error_count = 0
                valid_count = 0
                
                for rel in relations:
                    judgment = rel.get('text_judgments', {}).get(model, {})
                    parsed = judgment.get('parsed', {})
                    
                    if judgment.get('error'):
                        error_count += 1
                        continue
                    
                    valid_count += 1
                    
                    if parsed.get('accuracy') is True:
                        accurate_count += 1
                    
                    # Handle None values from failed parsing
                    faithfulness = parsed.get('faithfulness')
                    if faithfulness is not None:
                        faith_sum += faithfulness
                    
                    boundary = parsed.get('boundary_quality')
                    if boundary is not None:
                        bound_sum += boundary
                    
                    inference_time = judgment.get('inference_time')
                    if inference_time is not None:
                        time_sum += inference_time
                
                if valid_count > 0:
                    model_stats['text_accuracy_rate'] = accurate_count / valid_count
                    model_stats['text_avg_faithfulness'] = faith_sum / valid_count
                    model_stats['text_avg_boundary'] = bound_sum / valid_count
                    model_stats['text_avg_inference_time'] = time_sum / valid_count
                    model_stats['text_error_count'] = error_count
                
                stats['by_model'][model] = model_stats
        
        # Save to JSON
        output_path = os.path.join(self.output_dir, "statistics.json")
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        return stats
