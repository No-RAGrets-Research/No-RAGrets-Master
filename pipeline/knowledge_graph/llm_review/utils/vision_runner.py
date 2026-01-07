"""
Vision Model Runner for Figure Analysis

Provides abstraction layer for vision-capable models (GPT-4o, Qwen-VL, etc.)
Similar to llm_runner.py but handles multimodal image+text inputs.
"""

import os
from typing import Optional, Union
from pathlib import Path
import base64


def get_vision_client():
    """
    Get the appropriate vision-capable client based on environment variables.
    
    Environment Variables:
        VISION_PROVIDER: 'openai', 'qwen', or 'ollama_vision'
        VISION_MODEL: Model name (e.g., 'gpt-4o', 'qwen-vl-chat', 'llava')
        VISION_BASE_URL: Optional base URL for local models
        OPENAI_API_KEY: Required if VISION_PROVIDER=openai
    
    Returns:
        Configured client for vision model
    """
    provider = os.getenv("VISION_PROVIDER", "openai")
    
    if provider == "openai":
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        
        model = os.getenv("VISION_MODEL", "gpt-4o")
        client = OpenAI(api_key=api_key)
        return client, model, "openai"
    
    elif provider == "qwen":
        # For Qwen-VL via Ollama (qwen3-vl, qwen2-vl, etc.)
        from openai import OpenAI
        base_url = os.getenv("VISION_BASE_URL", "http://localhost:11434/v1")
        model = os.getenv("VISION_MODEL", "qwen3-vl:4b")
        
        # Ollama uses OpenAI-compatible API
        client = OpenAI(
            base_url=base_url,
            api_key="ollama"  # Ollama doesn't need real key
        )
        return client, model, "qwen"
    
    elif provider == "ollama_vision":
        # For Ollama with vision-capable models (LLaVA, etc.)
        from openai import OpenAI
        base_url = os.getenv("VISION_BASE_URL", "http://localhost:11434/v1")
        model = os.getenv("VISION_MODEL", "llava")
        
        # Ollama uses OpenAI-compatible API
        client = OpenAI(
            base_url=base_url,
            api_key="ollama"  # Ollama doesn't need real key
        )
        return client, model, "ollama_vision"
    
    else:
        raise ValueError(
            f"Unknown VISION_PROVIDER: {provider}. "
            "Supported: 'openai', 'qwen', 'ollama_vision'"
        )


def encode_image_to_base64(image_path: Union[str, Path]) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Base64 encoded string
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def run_vision_model(
    prompt: str,
    image_path: Optional[Union[str, Path]] = None,
    image_base64: Optional[str] = None,
    image_url: Optional[str] = None
) -> str:
    """
    Run vision model on image + text prompt.
    
    Args:
        prompt: Text prompt for the model
        image_path: Path to local image file
        image_base64: Base64-encoded image string
        image_url: URL to image (for OpenAI)
    
    Returns:
        Model's text response
    
    Note:
        Provide exactly one of: image_path, image_base64, or image_url
    """
    client, model, provider = get_vision_client()
    
    # Prepare image content
    if image_path:
        img_b64 = encode_image_to_base64(image_path)
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        }
    elif image_base64:
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
        }
    elif image_url:
        image_content = {
            "type": "image_url",
            "image_url": {"url": image_url}
        }
    else:
        raise ValueError("Must provide one of: image_path, image_base64, or image_url")
    
    # Construct messages with multimodal content
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                image_content
            ]
        }
    ]
    
    # Call the model
    if provider in ["openai", "ollama_vision", "qwen"]:
        # OpenAI-compatible API (works for OpenAI, Ollama, and Qwen via Ollama)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2000
        )
        
        # Extract content and handle None
        content = response.choices[0].message.content
        if content is None:
            print(f"Warning: Vision model returned None. Response: {response}")
            return ""
        return content
    
    else:
        raise NotImplementedError(f"Provider {provider} not implemented")


def analyze_figure(
    figure_image_path: Union[str, Path],
    figure_caption: str,
    rubric_prompt: str,
    paper_context: Optional[str] = None
) -> str:
    """
    Analyze a single figure using vision model and rubric.
    
    Args:
        figure_image_path: Path to figure image
        figure_caption: Caption text for the figure
        rubric_prompt: Quality assessment rubric
        paper_context: Optional context about the paper (section, etc.)
    
    Returns:
        Assessment text from vision model
    """
    # Build comprehensive prompt
    prompt_parts = [rubric_prompt]
    
    if paper_context:
        prompt_parts.append(f"\n\nPaper Context:\n{paper_context}")
    
    prompt_parts.append(f"\n\nFigure Caption:\n{figure_caption}")
    
    prompt_parts.append(
        "\n\nPlease analyze the figure above according to the rubric criteria. "
        "Provide a tier assessment (1-3) and specific feedback on clarity, "
        "labels, appropriateness, and any issues."
    )
    
    full_prompt = "\n".join(prompt_parts)
    
    # Run vision model
    print(f"[DEBUG] Calling vision model with prompt length: {len(full_prompt)} chars")
    print(f"[DEBUG] Image path: {figure_image_path}")
    
    result = run_vision_model(
        prompt=full_prompt,
        image_path=figure_image_path
    )
    
    print(f"[DEBUG] Vision model returned: {len(result) if result else 0} chars")
    if not result:
        print(f"[DEBUG] WARNING: Empty result from vision model!")
    
    return result


# For testing
if __name__ == "__main__":
    # Quick test to verify configuration
    try:
        client, model, provider = get_vision_client()
        print(f"✓ Vision client configured: {provider}/{model}")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
