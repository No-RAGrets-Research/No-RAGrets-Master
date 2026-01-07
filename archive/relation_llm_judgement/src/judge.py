"""
Ollama Judge Interface

Provides methods to run multiple Ollama models as judges and collect their responses.
"""

import ollama
from typing import List, Dict, Any, Optional
import time
from prompts import PromptTemplates


class OllamaJudge:
    """Interface for using Ollama models to judge relation quality."""
    
    def __init__(self, models: Optional[List[str]] = None):
        """
        Initialize the judge with specified models.
        
        Args:
            models: List of Ollama model names. Defaults to pilot models.
        """
        self.models = models or [
            "llama3.2:3b",
            "mistral:7b",
            "llama3.1:8b"
        ]
        self.prompt_templates = PromptTemplates()
    
    def check_model_availability(self) -> Dict[str, bool]:
        """
        Check which models are available locally.
        
        Returns:
            Dictionary mapping model names to availability status
        """
        available_models = {}
        
        try:
            model_list = ollama.list()
            # Handle both dict response and object response
            if hasattr(model_list, 'models'):
                models = model_list.models
            else:
                models = model_list.get('models', [])
            
            # Extract model names
            local_models = []
            for m in models:
                if isinstance(m, dict):
                    local_models.append(m.get('name', ''))
                elif hasattr(m, 'model'):
                    local_models.append(m.model)
                else:
                    local_models.append(str(m))
            
            for model in self.models:
                # Check if model is in local list (exact match or base name match)
                is_available = any(
                    model in local or local.startswith(model.split(':')[0])
                    for local in local_models
                )
                available_models[model] = is_available
        
        except Exception as e:
            print(f"Error checking model availability: {e}")
            for model in self.models:
                available_models[model] = False
        
        return available_models
    
    def pull_model_if_needed(self, model: str) -> bool:
        """
        Pull a model if it's not available locally.
        
        Args:
            model: Model name
            
        Returns:
            True if model is ready, False otherwise
        """
        try:
            print(f"Pulling model {model}...")
            ollama.pull(model)
            print(f"Model {model} ready")
            return True
        except Exception as e:
            print(f"Error pulling model {model}: {e}")
            return False
    
    def judge_text_based(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Run text-based judging with a single model.
        
        Args:
            prompt: The prompt to send
            model: Model name
            temperature: Sampling temperature (0.0 = deterministic)
            max_retries: Number of retries on failure
            
        Returns:
            Dictionary with raw response and parsed fields
        """
        result = {
            "model": model,
            "raw_response": None,
            "parsed": None,
            "error": None,
            "inference_time": None
        }
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                response = ollama.generate(
                    model=model,
                    prompt=prompt,
                    options={
                        "temperature": temperature
                    }
                )
                
                inference_time = time.time() - start_time
                
                raw_response = response.get('response', '')
                result["raw_response"] = raw_response
                result["inference_time"] = inference_time
                
                # Parse the response
                parsed = self.prompt_templates.parse_text_based_response(raw_response)
                result["parsed"] = parsed
                
                return result
            
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} for model {model}")
                    time.sleep(1)
                else:
                    result["error"] = str(e)
                    return result
        
        return result
    
    def judge_image_based(
        self,
        prompt: str,
        image_path: str,
        model: str,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Run image-based judging with a vision model.
        
        Args:
            prompt: The prompt to send
            image_path: Path to the image file
            model: Vision model name
            temperature: Sampling temperature
            max_retries: Number of retries on failure
            
        Returns:
            Dictionary with raw response and parsed fields
        """
        result = {
            "model": model,
            "raw_response": None,
            "parsed": None,
            "error": None,
            "inference_time": None
        }
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                response = ollama.generate(
                    model=model,
                    prompt=prompt,
                    images=[image_path],
                    options={
                        "temperature": temperature
                    }
                )
                
                inference_time = time.time() - start_time
                
                raw_response = response.get('response', '')
                result["raw_response"] = raw_response
                result["inference_time"] = inference_time
                
                # Parse the response
                parsed = self.prompt_templates.parse_image_based_response(raw_response)
                result["parsed"] = parsed
                
                return result
            
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} for model {model}")
                    time.sleep(1)
                else:
                    result["error"] = str(e)
                    return result
        
        return result
    
    def judge_relation_text(
        self,
        relation: Dict[str, Any],
        models: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Judge a single relation with multiple text-based models.
        
        Args:
            relation: Enriched relation dictionary with source_span
            models: List of model names (uses self.models if not provided)
            
        Returns:
            Dictionary mapping model names to judgment results
        """
        models_to_use = models or self.models
        
        # Create prompt from relation
        prompt = self.prompt_templates.create_text_prompt_from_relation(relation)
        
        if not prompt:
            return {model: {"error": "Could not create prompt from relation"} for model in models_to_use}
        
        results = {}
        
        for model in models_to_use:
            print(f"Judging with {model}...")
            result = self.judge_text_based(prompt=prompt, model=model)
            results[model] = result
        
        return results
    
    def judge_relation_image(
        self,
        relation: Dict[str, Any],
        models: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Judge a single relation with multiple vision models.
        
        Args:
            relation: Relation dictionary with image_path
            models: List of vision model names
            
        Returns:
            Dictionary mapping model names to judgment results
        """
        vision_models = models or ["llama3.2-vision:11b"]
        
        # Create prompt from relation
        prompt = self.prompt_templates.create_image_prompt_from_relation(relation)
        image_path = relation.get("image_path")
        
        if not prompt or not image_path:
            return {model: {"error": "Missing prompt or image"} for model in vision_models}
        
        results = {}
        
        for model in vision_models:
            print(f"Judging with vision model {model}...")
            result = self.judge_image_based(
                prompt=prompt,
                image_path=image_path,
                model=model
            )
            results[model] = result
        
        return results
    
    def batch_judge_relations(
        self,
        relations: List[Dict[str, Any]],
        text_models: Optional[List[str]] = None,
        use_vision: bool = False,
        vision_models: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Judge multiple relations with multiple models.
        
        Args:
            relations: List of enriched relation dictionaries
            text_models: List of text model names
            use_vision: Whether to also use vision models
            vision_models: List of vision model names
            
        Returns:
            List of relations with added judgment fields
        """
        judged_relations = []
        
        for i, relation in enumerate(relations):
            print(f"\nJudging relation {i+1}/{len(relations)}...")
            
            judged_rel = relation.copy()
            
            # Text-based judging
            text_judgments = self.judge_relation_text(relation, models=text_models)
            judged_rel["text_judgments"] = text_judgments
            
            # Vision-based judging (if requested and image available)
            if use_vision and relation.get("image_path"):
                vision_judgments = self.judge_relation_image(relation, models=vision_models)
                judged_rel["vision_judgments"] = vision_judgments
            
            judged_relations.append(judged_rel)
        
        return judged_relations
