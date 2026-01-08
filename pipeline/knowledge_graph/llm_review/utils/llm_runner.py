from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Tuple

load_dotenv()

def get_llm_client() -> Tuple[OpenAI, str]:
    """
    Initialize LLM client based on environment configuration.
    
    Returns:
        tuple: (OpenAI client, model name)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "ollama":
        # Ollama uses OpenAI-compatible API
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        client = OpenAI(
            base_url=base_url,
            api_key="ollama"  # Dummy key required but not validated
        )
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    else:
        # Standard OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    return client, model

# Lazy initialization - only create when needed
_client = None
_model = None

def _ensure_initialized():
    """Ensure LLM client is initialized."""
    global _client, _model
    if _client is None:
        _client, _model = get_llm_client()

def run_llm(prompt: str, temperature: float = 0.7) -> str:
    """
    Execute prompt with configured LLM provider.
    
    Args:
        prompt: The prompt to send to the LLM
        temperature: Sampling temperature (0.0-2.0)
    
    Returns:
        str: LLM response text
    """
    _ensure_initialized()
    completion = _client.chat.completions.create(
        model=_model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    
    return completion.choices[0].message.content
