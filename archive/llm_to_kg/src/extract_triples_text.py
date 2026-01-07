import os
import json
import glob
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def extract_triples_text(
    chunk_dir="data/chunks",
    output_dir="data/triples_text",
    model_name="Qwen/Qwen2.5-1.5B-Instruct",
    limit=None,  # Limit processing to first N files
):
    os.makedirs(output_dir, exist_ok=True)

    # === Load model ===
    print(f"Loading model {model_name} ...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    if torch.cuda.is_available():
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        print(f"Initial memory allocated: {torch.cuda.memory_allocated(0)/1024**3:.2f} GB")
    else:
        print("⚠️ CUDA not detected — running on CPU")


    # === Get chunk files ===
    chunk_files = sorted(glob.glob(os.path.join(chunk_dir, "*.json")))
    if limit:
        chunk_files = chunk_files[:limit]
    print(f"Found {len(chunk_files)} chunk files in {chunk_dir}")

    # === Main loop ===
    for file in chunk_files:
        name = os.path.basename(file).replace("_chunks.json", "")
        out_path = os.path.join(output_dir, f"{name}_triples.json")

        # Skip logic: if file exists and is not empty, skip it
        if os.path.exists(out_path):
            try:
                if os.path.getsize(out_path) > 100:  # Over 100 bytes means it has content
                    print(f"[Skip] {name}: triples already exist.")
                    continue
            except OSError:
                pass

        try:
            with open(file, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            triples_all = []
            print(f"Processing {name} ({len(chunks)} chunks)...")

            batch_size = 2
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                valid_batch = [ch if isinstance(ch, str) else ch.get("text", "") for ch in batch]
                valid_batch = [t.strip() for t in valid_batch if t.strip()]
                if not valid_batch:
                    continue

                print(f"[{i+1}/{len(chunks)}] Generating triples batch for {name}...")

                prompts = [
                    (
                        "Extract all factual triples (subject, relation, object) from the text below.\n"
                        "Return them as a list of triples.\n\n"
                        f"Text:\n{text}\n\nOutput:"
                    )
                    for text in valid_batch
                ]

                inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True).to(model.device)
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=128,
                    do_sample=False,
                    num_beams=1,
                    use_cache=True
                )

                decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)

                for j, text in enumerate(valid_batch):
                    triples_all.append({
                        "chunk_index": i + j,
                        "triples_raw": decoded[j].strip()
                    })

                if (i // batch_size) % 5 == 0:
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(triples_all, f, ensure_ascii=False, indent=2)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(triples_all, f, ensure_ascii=False, indent=2)

            print(f"[✅ OK] {name}: {len(triples_all)} triples extracted.")

        except Exception as e:
            print(f"[❌ FAIL] {name}: {e}")

    print(f"\n✅ All triples saved to {output_dir}")


if __name__ == "__main__":
    extract_triples_text()  # Test with two articles first, remove limit after confirming it works
