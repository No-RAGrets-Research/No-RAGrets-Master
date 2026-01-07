"""
Prompt Templates for LLM Judges

Defines structured prompts for evaluating relation extraction quality.
"""

from typing import Dict, Any, Optional


class PromptTemplates:
    """Collection of prompt templates for judging relation quality."""
    
    @staticmethod
    def text_based_judge_prompt(
        subject: str,
        predicate: str,
        obj: str,
        sentence_text: str,
        subject_positions: Optional[list] = None,
        object_positions: Optional[list] = None
    ) -> str:
        """
        Generate a text-based judging prompt.
        
        Args:
            subject: Subject entity
            predicate: Relationship type
            obj: Object entity
            sentence_text: Source sentence text
            subject_positions: List of subject character positions
            object_positions: List of object character positions
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are evaluating a knowledge extraction system. Given a sentence and an extracted relation, assess if the extraction is correct.

**Extracted Relation:**
Subject: {subject}
Predicate: {predicate}
Object: {obj}

**Source Sentence:**
{sentence_text}
"""
        
        if subject_positions and len(subject_positions) > 0:
            pos = subject_positions[0]
            prompt += f"\n**Subject Position:** Characters {pos.get('start')}-{pos.get('end')}: \"{pos.get('matched_text')}\""
        
        if object_positions and len(object_positions) > 0:
            pos = object_positions[0]
            prompt += f"\n**Object Position:** Characters {pos.get('start')}-{pos.get('end')}: \"{pos.get('matched_text')}\""
        
        prompt += """

**Questions:**
1. Is this relation accurately represented in the sentence? (Answer: Yes or No)
2. Faithfulness: How directly is this relation stated in the source? (Answer: 1-5 where 1=Hallucinated, 3=Partially supported, 5=Directly stated)
3. Are the entity boundaries (subject and object) correctly identified? (Answer: 1-5 where 1=Completely wrong, 5=Perfect)
4. Provide a brief justification for your ratings (1-2 sentences).

Please respond in this exact format:
ACCURACY: [Yes/No]
FAITHFULNESS: [1-5]
BOUNDARY_QUALITY: [1-5]
JUSTIFICATION: [Your explanation]
"""
        
        return prompt
    
    @staticmethod
    def image_based_judge_prompt(
        subject: str,
        predicate: str,
        obj: str
    ) -> str:
        """
        Generate an image-based judging prompt (for vision models).
        
        Args:
            subject: Subject entity
            predicate: Relationship type
            obj: Object entity
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are shown a PDF page section with a highlighted region. An extraction system identified a relation from this text.

**Extracted Relation:**
{subject} → {predicate} → {obj}

**Task:**
1. Can you find this relation in the highlighted text? (Answer: Yes or No)
2. Is it accurately extracted? Rate the extraction quality (1-5 where 1=Completely wrong, 5=Perfect)
3. Provide a brief explanation (1-2 sentences).

Please respond in this exact format:
FOUND: [Yes/No]
QUALITY: [1-5]
EXPLANATION: [Your explanation]
"""
        
        return prompt
    
    @staticmethod
    def parse_text_based_response(response: str) -> Dict[str, Any]:
        """
        Parse the structured response from text-based judging.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Dictionary with parsed fields
        """
        result = {
            "accuracy": None,
            "faithfulness": None,
            "boundary_quality": None,
            "justification": None,
            "parse_error": None
        }
        
        try:
            lines = response.strip().split('\n')
            
            for line in lines:
                # Remove markdown bold markers and extra whitespace
                line = line.replace('**', '').strip()
                
                if line.upper().startswith("ACCURACY"):
                    value = line.split(":", 1)[1].strip().lower()
                    result["accuracy"] = value in ["yes", "true", "correct"]
                
                elif line.upper().startswith("FAITHFULNESS"):
                    value = line.split(":", 1)[1].strip()
                    try:
                        result["faithfulness"] = int(value)
                    except ValueError:
                        result["parse_error"] = f"Invalid faithfulness: {value}"
                
                elif line.upper().startswith("BOUNDARY_QUALITY") or line.upper().startswith("BOUNDARY QUALITY"):
                    value = line.split(":", 1)[1].strip()
                    try:
                        result["boundary_quality"] = int(value)
                    except ValueError:
                        result["parse_error"] = f"Invalid boundary quality: {value}"
                
                elif line.upper().startswith("JUSTIFICATION"):
                    result["justification"] = line.split(":", 1)[1].strip()
        
        except Exception as e:
            result["parse_error"] = str(e)
        
        return result
    
    @staticmethod
    def parse_image_based_response(response: str) -> Dict[str, Any]:
        """
        Parse the structured response from image-based judging.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Dictionary with parsed fields
        """
        result = {
            "found": None,
            "quality": None,
            "explanation": None,
            "parse_error": None
        }
        
        try:
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("FOUND:"):
                    value = line.split(":", 1)[1].strip().lower()
                    result["found"] = value in ["yes", "true"]
                
                elif line.startswith("QUALITY:"):
                    value = line.split(":", 1)[1].strip()
                    try:
                        result["quality"] = int(value)
                    except ValueError:
                        result["parse_error"] = f"Invalid quality: {value}"
                
                elif line.startswith("EXPLANATION:"):
                    result["explanation"] = line.split(":", 1)[1].strip()
        
        except Exception as e:
            result["parse_error"] = str(e)
        
        return result
    
    @staticmethod
    def create_text_prompt_from_relation(relation: Dict[str, Any]) -> Optional[str]:
        """
        Create a text-based prompt from a relation dictionary.
        
        Args:
            relation: Enriched relation dictionary with source_span
            
        Returns:
            Formatted prompt string or None if missing data
        """
        subject = relation.get("subject", {}).get("name")
        predicate = relation.get("predicate")
        obj = relation.get("object", {}).get("name")
        
        source_span = relation.get("source_span", {})
        source_span_data = source_span.get("source_span", {})
        
        sentence_text = source_span_data.get("text_evidence")
        subject_positions = source_span_data.get("subject_positions", [])
        object_positions = source_span_data.get("object_positions", [])
        
        if not all([subject, predicate, obj, sentence_text]):
            return None
        
        return PromptTemplates.text_based_judge_prompt(
            subject=subject,
            predicate=predicate,
            obj=obj,
            sentence_text=sentence_text,
            subject_positions=subject_positions,
            object_positions=object_positions
        )
    
    @staticmethod
    def create_image_prompt_from_relation(relation: Dict[str, Any]) -> Optional[str]:
        """
        Create an image-based prompt from a relation dictionary.
        
        Args:
            relation: Relation dictionary
            
        Returns:
            Formatted prompt string or None if missing data
        """
        subject = relation.get("subject", {}).get("name")
        predicate = relation.get("predicate")
        obj = relation.get("object", {}).get("name")
        
        if not all([subject, predicate, obj]):
            return None
        
        return PromptTemplates.image_based_judge_prompt(
            subject=subject,
            predicate=predicate,
            obj=obj
        )
