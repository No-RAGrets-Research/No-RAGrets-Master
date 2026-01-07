import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

def load_papers_from_individual_json(json_dir="paper_json_data"):
    """Load all papers from individual JSON files"""
    json_folder = Path(json_dir)
    
    if not json_folder.exists():
        print(f"Error: {json_dir} folder not found!")
        return {}
    
    papers_data = {}
    json_files = list(json_folder.glob("*.json"))
    
    # Filter out error files
    valid_json_files = [f for f in json_files if not f.name.endswith("_ERROR.json")]
    
    print(f"Found {len(valid_json_files)} valid JSON files")
    
    for json_file in valid_json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
                papers_data[paper_data['filename']] = paper_data
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return papers_data

def find_abstract_or_intro(chunks):
    """Find abstract or introduction chunks"""
    for chunk in chunks:
        chunk_lower = chunk.lower()
        if any(keyword in chunk_lower[:100] for keyword in ['abstract', 'introduction', 'summary', 'objective']):
            return chunk[:800]
    
    # Fallback: return first substantial chunk
    for chunk in chunks:
        if len(chunk) > 100:
            return chunk[:800]
    
    return ""

def analyze_objectives():
    """Analyze objectives and save individual files"""
    
    # Load Granite model
    print("Loading Granite 4 model...")
    tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-4.0-micro")
    model = AutoModelForCausalLM.from_pretrained("ibm-granite/granite-4.0-micro")
    print("✓ Model loaded!")
    
    # Load papers data
    papers_data = load_papers_from_individual_json()
    
    if not papers_data:
        print("No papers found. Run experiment_extraction.py first!")
        return
    
    # Create output directory
    output_dir = Path("paper_objectives")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Analyzing {len(papers_data)} papers...")
    
    for i, (filename, paper_data) in enumerate(papers_data.items()):
        print(f"\n{i+1}/{len(papers_data)} Processing: {filename}")
        
        try:
            # Get relevant text
            relevant_text = find_abstract_or_intro(paper_data.get('chunks', []))
            
            if relevant_text:
                title = paper_data.get('filename', '').replace('.pdf', '').replace('.docx', '')
                
                prompt = f"""Based on this research paper excerpt, provide a 1-3 sentence summary of the main research objective and approach.

Paper: {title}

Text excerpt:
{relevant_text}

Summary:"""

                # Query Granite
                messages = [{"role": "user", "content": prompt}]
                inputs = tokenizer.apply_chat_template(
                    messages, 
                    add_generation_prompt=True, 
                    tokenize=True, 
                    return_dict=True, 
                    return_tensors="pt"
                )
                
                outputs = model.generate(**inputs, max_new_tokens=100, do_sample=False, temperature=0.7)
                result = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])
                
                # Clean up the result
                objective = result.strip()
                objective = objective.replace("<|end_of_text|>", "").replace("</s>", "").strip()
                
                # Remove any remaining special tokens
                if objective.startswith("Summary:"):
                    objective = objective[8:].strip()
                if objective.startswith("Objective:"):
                    objective = objective[10:].strip()
                
                # Create result
                paper_result = {
                    'filename': filename,
                    'objective_summary': objective,
                    'title': title
                }
                
                # Save individual file
                safe_filename = filename.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('&', 'and').replace('.pdf', '').replace('.docx', '')
                objective_file = output_dir / f"{safe_filename}_objective.json"
                
                with open(objective_file, 'w', encoding='utf-8') as f:
                    json.dump(paper_result, f, indent=2)
                
                print(f"   Summary: {objective}")
                print(f"   Saved: {objective_file.name}")
                
            else:
                print(f"   No text found")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    print(f"\n✓ Created paper_objectives/ folder with individual objective files")

if __name__ == "__main__":
    analyze_objectives()