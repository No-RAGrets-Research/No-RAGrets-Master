from transformers import AutoModel, AutoTokenizer
import torch
import os
import shutil
from pathlib import Path

# Clear corrupted cache first
def clear_deepseek_cache():
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    deepseek_dirs = list(cache_dir.glob("*deepseek*"))
    for dir_path in deepseek_dirs:
        try:
            shutil.rmtree(dir_path)
            print(f"Cleared cache: {dir_path}")
        except:
            pass

print("Clearing corrupted cache...")
clear_deepseek_cache()

model_name = 'deepseek-ai/DeepSeek-OCR'

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    model_name, 
    trust_remote_code=True,
    force_download=True
)

print("Loading model...")
model = AutoModel.from_pretrained(
    model_name, 
    trust_remote_code=True, 
    use_safetensors=True,
    torch_dtype=torch.float32,
    device_map="cpu"
)
model = model.eval()

prompt = "<image>\n<|grounding|>Convert the document to markdown. "
image_file = 'deepseek_images/page_001.png'
output_path = 'deepseek_images/output/page_001_output'

print("Running inference...")
res = model.infer(tokenizer, prompt=prompt, image_file=image_file, output_path = output_path, base_size = 1024, image_size = 640, crop_mode=True, save_results = True, test_compress = True)

print(f"Processing complete! Result: {res}")