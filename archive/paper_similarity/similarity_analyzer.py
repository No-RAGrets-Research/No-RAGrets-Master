import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import sys

class SimilarityAnalyzer:
    def __init__(self):
        print("Loading Granite 4 model...")
        
        # Check for GPU availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-4.0-micro")
        self.model = AutoModelForCausalLM.from_pretrained(
            "ibm-granite/granite-4.0-micro",
            dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        print("Model loaded successfully!")
    
    def load_all_objectives(self):
        """Load all paper objectives"""
        objectives_dir = Path("paper_objectives")
        if not objectives_dir.exists():
            print("Error: paper_objectives folder not found!")
            return {}
        
        objectives = {}
        for json_file in objectives_dir.glob("*_objective.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    objectives[data['filename']] = data
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        print(f"Loaded {len(objectives)} paper objectives")
        return objectives
    
    def compare_papers(self, paper1_data, paper2_data):
        """Use Granite to compare two papers"""
        
        summary1 = paper1_data['objective_summary'][:500]
        summary2 = paper2_data['objective_summary'][:500]
        
        prompt = f"""Compare these research papers:

Paper A: {paper1_data['title']}
Summary: {summary1}

Paper B: {paper2_data['title']}
Summary: {summary2}

Analyze their similarity:
SIMILARITY_SCORE: High/Medium/Low
REASONING: Why are they similar or different (focus on objectives, methods, claims)

Response:"""

        return self._query_granite(prompt, max_tokens=300)
    
    def _query_granite(self, prompt, max_tokens=300):
        """Query Granite model with GPU optimization"""
        try:
            messages = [{"role": "user", "content": prompt}]
            inputs = self.tokenizer.apply_chat_template(
                messages, 
                add_generation_prompt=True, 
                tokenize=True, 
                return_dict=True, 
                return_tensors="pt"
            )
            
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=max_tokens, 
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            result = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])
            
            # Clean up result
            cleaned = result.strip()
            for token in ["</s>", "<|end_of_text|>", "<|endoftext|>"]:
                cleaned = cleaned.replace(token, "")
            
            return cleaned.strip()
            
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def parse_comparison_result(self, raw_result):
        """Extract similarity score and reasoning from Granite response - IMPROVED VERSION"""
        
        # First, try to find structured format
        lines = raw_result.split('\n')
        similarity_score = "Unknown"
        reasoning = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('SIMILARITY_SCORE:') or line.startswith('SIMILARITY:'):
                similarity_score = line.split(':', 1)[1].strip()
            elif line.startswith('REASONING:') or line.startswith('REASON:'):
                reasoning = line.split(':', 1)[1].strip()
        
        # If structured parsing failed, try to extract from the raw text
        if similarity_score == "Unknown":
            raw_lower = raw_result.lower()
            
            # Look for common patterns in the responses
            if any(phrase in raw_lower for phrase in [
                'similarity score between paper a and paper b is high',
                'similarity score is high',
                'similarity: high',
                'high similarity'
            ]):
                similarity_score = "High"
            elif any(phrase in raw_lower for phrase in [
                'similarity score between paper a and paper b is medium',
                'similarity score is medium', 
                'similarity: medium',
                'medium similarity'
            ]):
                similarity_score = "Medium"
            elif any(phrase in raw_lower for phrase in [
                'similarity score between paper a and paper b is low',
                'similarity score is low',
                'similarity: low',
                'low similarity'
            ]):
                similarity_score = "Low"
            else:
                # Last resort - look for the words themselves in context
                if 'high' in raw_lower and ('similar' in raw_lower or 'score' in raw_lower):
                    similarity_score = "High"
                elif 'medium' in raw_lower and ('similar' in raw_lower or 'score' in raw_lower):
                    similarity_score = "Medium"
                elif 'low' in raw_lower and ('similar' in raw_lower or 'score' in raw_lower):
                    similarity_score = "Low"
        
        # Normalize similarity score one more time
        similarity_lower = similarity_score.lower()
        if 'high' in similarity_lower:
            similarity_score = "High"
        elif 'medium' in similarity_lower:
            similarity_score = "Medium"  
        elif 'low' in similarity_lower:
            similarity_score = "Low"
        
        # Extract reasoning - try multiple approaches
        if not reasoning:
            # Look for reasoning section
            if 'reasoning:' in raw_result.lower():
                parts = raw_result.lower().split('reasoning:')
                if len(parts) > 1:
                    reasoning = parts[1].strip()
            elif 'reason:' in raw_result.lower():
                parts = raw_result.lower().split('reason:')
                if len(parts) > 1:
                    reasoning = parts[1].strip()
            else:
                # Use first substantial paragraph as reasoning
                sentences = raw_result.split('.')
                for sentence in sentences:
                    if len(sentence.strip()) > 50:  # Find substantial content
                        reasoning = sentence.strip()
                        break
                
                if not reasoning:
                    reasoning = raw_result[:200] + "..." if len(raw_result) > 200 else raw_result
        
        return similarity_score, reasoning
    
    def create_safe_filename(self, filename):
        """Create safe filename for JSON output"""
        return filename.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('&', 'and').replace('.pdf', '').replace('.docx', '')
    
    def run_pairwise_analysis(self, max_papers=None):
        """Run complete pairwise analysis and save individual files"""
        
        objectives = self.load_all_objectives()
        if len(objectives) < 2:
            print("Need at least 2 papers to compare!")
            return
        
        paper_list = list(objectives.items())
        total_available = len(paper_list)
        
        # Limit papers if specified
        if max_papers is not None:
            paper_list = paper_list[:max_papers]
            print(f"Limited to first {len(paper_list)} papers (out of {total_available} available)")
        
        total_papers = len(paper_list)
        
        # Create output directory
        output_dir = Path("paper_similarities")
        output_dir.mkdir(exist_ok=True)
        
        # Check which papers already have similarity files
        existing_files = set()
        skipped_papers = []
        for similarity_file in output_dir.glob("*_similarities.json"):
            # Extract the base filename to match against papers
            base_name = similarity_file.stem.replace('_similarities', '')
            existing_files.add(base_name)
        
        print(f"Starting pairwise analysis of {total_papers} papers")
        print(f"Each paper will be compared to {total_available - 1} others")
        
        if existing_files:
            print(f"Found {len(existing_files)} existing similarity files - will skip those papers")
        
        print(f"Will create similarity files for remaining papers")
        total_comparisons = total_papers * (total_available - 1)
        print(f"Total comparisons: {total_comparisons}")
        print("="*60)
        
        # Get all papers for comparison (always compare against full dataset)
        all_papers = list(objectives.items())
        
        processed_count = 0
        
        # Process each paper against all others
        for i, (target_filename, target_data) in enumerate(paper_list):
            # Check if this paper already has a similarity file
            safe_filename = self.create_safe_filename(target_filename)
            output_file = output_dir / f"{safe_filename}_similarities.json"
            
            if output_file.exists():
                print(f"\n[{i+1}/{total_papers}] SKIPPING: {target_data['title'][:60]}...")
                print(f"  Similarity file already exists: {output_file.name}")
                skipped_papers.append(target_data['title'])
                continue
            
            processed_count += 1
            print(f"\n[{i+1}/{total_papers}] Processing: {target_data['title'][:60]}...")
            
            paper_similarities = {
                'target_paper': {
                    'filename': target_filename,
                    'title': target_data['title'],
                    'objective_summary': target_data['objective_summary']
                },
                'comparisons': [],
                'summary': {
                    'total_comparisons': total_available - 1,
                    'high_similarity_count': 0,
                    'medium_similarity_count': 0,
                    'low_similarity_count': 0,
                    'error_count': 0
                }
            }
            
            # Compare against all other papers (not just the limited set)
            comparison_count = 0
            for j, (other_filename, other_data) in enumerate(all_papers):
                if target_filename != other_filename:  # Don't compare paper to itself
                    comparison_count += 1
                    
                    # Show progress every 10 comparisons
                    if comparison_count % 10 == 0:
                        progress = (comparison_count / (total_available - 1)) * 100
                        print(f"    Progress: {comparison_count}/{total_available - 1} ({progress:.1f}%)")
                    
                    try:
                        # Get comparison from Granite
                        raw_comparison = self.compare_papers(target_data, other_data)
                        similarity_score, reasoning = self.parse_comparison_result(raw_comparison)
                        
                        comparison_result = {
                            'compared_paper': {
                                'filename': other_filename,
                                'title': other_data['title']
                            },
                            'similarity_score': similarity_score,
                            'reasoning': reasoning,
                            'raw_response': raw_comparison
                        }
                        
                        paper_similarities['comparisons'].append(comparison_result)
                        
                        # Update summary counts
                        if similarity_score == "High":
                            paper_similarities['summary']['high_similarity_count'] += 1
                            print(f"  HIGH SIMILARITY with: {other_data['title'][:50]}...")
                            print(f"    Reason: {reasoning[:100]}...")
                        elif similarity_score == "Medium":
                            paper_similarities['summary']['medium_similarity_count'] += 1
                        elif similarity_score == "Low":
                            paper_similarities['summary']['low_similarity_count'] += 1
                        else:
                            paper_similarities['summary']['error_count'] += 1
                        
                    except Exception as e:
                        error_result = {
                            'compared_paper': {
                                'filename': other_filename,
                                'title': other_data['title']
                            },
                            'similarity_score': "Error",
                            'reasoning': f"Analysis failed: {str(e)}",
                            'raw_response': str(e)
                        }
                        paper_similarities['comparisons'].append(error_result)
                        paper_similarities['summary']['error_count'] += 1
            
            # Save individual paper similarity file
            safe_filename = self.create_safe_filename(target_filename)
            output_file = output_dir / f"{safe_filename}_similarities.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(paper_similarities, f, indent=2, ensure_ascii=False)
            
            # Print summary for this paper
            summary = paper_similarities['summary']
            print(f"  Completed {summary['total_comparisons']} comparisons")
            print(f"  High: {summary['high_similarity_count']}, Medium: {summary['medium_similarity_count']}, Low: {summary['low_similarity_count']}")
            print(f"  Saved: {output_file.name}")
        
        print(f"\nAnalysis complete!")
        print(f"Processed {processed_count} new papers")
        if skipped_papers:
            print(f"Skipped {len(skipped_papers)} papers with existing similarity files:")
            for paper in skipped_papers[:5]:  # Show first 5
                print(f"  - {paper[:60]}...")
            if len(skipped_papers) > 5:
                print(f"  ... and {len(skipped_papers) - 5} more")
        
        total_files = len(list(output_dir.glob("*_similarities.json")))
        print(f"Total similarity files in {output_dir}/ folder: {total_files}")
        
        # Create overall summary
        self.create_overall_summary(output_dir, total_papers)
    
    def create_overall_summary(self, output_dir, total_papers):
        """Create summary of all similarities"""
        
        print("Creating overall summary...")
        
        all_high_similarities = []
        total_high = 0
        total_medium = 0
        total_low = 0
        total_errors = 0
        
        # Collect data from all individual files
        for similarity_file in output_dir.glob("*_similarities.json"):
            try:
                with open(similarity_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    summary = data['summary']
                    total_high += summary['high_similarity_count']
                    total_medium += summary['medium_similarity_count']
                    total_low += summary['low_similarity_count']
                    total_errors += summary['error_count']
                    
                    # Collect high similarity pairs with reasoning
                    for comparison in data['comparisons']:
                        if comparison['similarity_score'] == "High":
                            all_high_similarities.append({
                                'paper1': data['target_paper']['title'],
                                'paper2': comparison['compared_paper']['title'],
                                'reasoning': comparison['reasoning']
                            })
                            
            except Exception as e:
                print(f"Error reading {similarity_file}: {e}")
        
        overall_summary = {
            'analysis_info': {
                'total_papers_analyzed': len(list(output_dir.glob("*_similarities.json"))),
                'total_papers_in_dataset': total_papers,
                'total_pairwise_comparisons': total_high + total_medium + total_low + total_errors
            },
            'similarity_distribution': {
                'high_similarity_total': total_high,
                'medium_similarity_total': total_medium,
                'low_similarity_total': total_low,
                'error_total': total_errors
            },
            'high_similarity_pairs_with_reasoning': all_high_similarities
        }
        
        summary_file = output_dir / "overall_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(overall_summary, f, indent=2, ensure_ascii=False)
        
        print(f"Overall summary saved to: {summary_file}")
        print(f"Found {len(all_high_similarities)} high similarity pairs")

def parse_arguments():
    """Parse command line arguments"""
    if len(sys.argv) == 1:
        # No arguments - interactive mode
        return None
    
    arg = sys.argv[1].lower()
    
    if arg in ['all', 'full']:
        return None  # Process all papers
    elif arg.isdigit():
        count = int(arg)
        if count > 0:
            return count
        else:
            print("Error: Count must be greater than 0")
            sys.exit(1)
    else:
        print("Usage:")
        print("  python similarity_analyzer.py          # Interactive mode")
        print("  python similarity_analyzer.py all      # Process all papers")
        print("  python similarity_analyzer.py 5        # Process first 5 papers")
        print("  python similarity_analyzer.py 10       # Process first 10 papers")
        sys.exit(1)

def main():
    print("Paper Similarity Analyzer")
    print("="*50)
    
    # Parse command line arguments
    max_papers = parse_arguments()
    
    analyzer = SimilarityAnalyzer()
    
    if max_papers is None:
        if len(sys.argv) == 1:
            # Interactive mode
            print("Available options:")
            print("  all   - Process all 50 papers")
            print("  N     - Process first N papers (e.g., 5, 10)")
            
            choice = input("Enter your choice: ").strip().lower()
            
            if choice in ['all', 'full', '']:
                max_papers = None
                print("Will process ALL 50 papers")
            elif choice.isdigit():
                max_papers = int(choice)
                print(f"Will process first {max_papers} papers")
            else:
                print("Invalid choice. Exiting.")
                return
        else:
            # Command line specified 'all'
            print("Will process ALL 50 papers")
    else:
        print(f"Will process first {max_papers} papers")
    
    if max_papers is None:
        print("Each of the 50 papers will be compared to all 49 others")
        print("Will create 50 similarity files")
        print("Total comparisons: 2,450")
        print("Estimated time: 20-40 minutes on GPU")
    else:
        print(f"Each of the {max_papers} papers will be compared to all 49 others")
        print(f"Will create {max_papers} similarity files")
        total_comps = max_papers * 49
        print(f"Total comparisons: {total_comps}")
        estimated_minutes = total_comps / 100  # Rough estimate
        print(f"Estimated time: {estimated_minutes:.1f} minutes on GPU")
    
    confirm = input("\nContinue with analysis? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Analysis cancelled")
        return
    
    analyzer.run_pairwise_analysis(max_papers=max_papers)
    print("Analysis complete! Check the paper_similarities/ folder for results.")

if __name__ == "__main__":
    main()