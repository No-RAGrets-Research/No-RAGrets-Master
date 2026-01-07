import os
from .llm_runner import run_llm

def merge_results(rubric_outputs):
    """Legacy function for backward compatibility."""
    merged = "\n\n".join(rubric_outputs)
    return merged

def merge_rubric_outputs(rubric_responses):
    """
    Merge multiple rubric responses into a single text.
    
    Args:
        rubric_responses: List of dicts with 'rubric_name' and 'response' keys
    
    Returns:
        str: Merged text from all rubrics
    """
    merged_sections = []
    for rubric in rubric_responses:
        section = f"### {rubric['rubric_name']}\n\n{rubric['response']}"
        merged_sections.append(section)
    
    return "\n\n---\n\n".join(merged_sections)

def synthesize_review(merged_text):
    """
    Generate final synthesis from merged rubric outputs.
    
    Args:
        merged_text: Combined text from all rubrics
    
    Returns:
        str: Final synthesized review
    """
    # Load synthesizer prompt
    synthesizer_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "prompts",
        "synthesizer.txt"
    )
    
    with open(synthesizer_path, 'r') as f:
        synthesizer_prompt = f.read()
    
    full_prompt = f"{synthesizer_prompt}\n\n---MERGED RUBRIC OUTPUTS---\n{merged_text}"
    
    return run_llm(full_prompt)

