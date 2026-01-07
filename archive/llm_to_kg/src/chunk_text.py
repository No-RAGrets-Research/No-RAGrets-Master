import os
import json
import glob
from pathlib import Path
from textwrap import wrap

def split_texts(input_dir="data/parsed_json", output_dir="data/chunks", chunk_size=1000):
    """
    Extract text from Docling JSON (containing "texts" array) and split into chunks.
    Automatically skip already processed files.
    """
    os.makedirs(output_dir, exist_ok=True)

    json_files = sorted(glob.glob(os.path.join(input_dir, "*.json")))
    print(f"🧩 Found {len(json_files)} parsed JSON files in {input_dir}")

    success, skipped, failed = 0, 0, 0  # Statistics counters

    for path in json_files:
        name = Path(path).stem
        chunk_path = os.path.join(output_dir, f"{name}_chunks.json")

        # Skip already existing chunks
        if os.path.exists(chunk_path):
            print(f"[⏩ Skip] {name} already chunked.")
            skipped += 1
            continue

        try:
            # === Load JSON ===
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # === Extract text blocks ===
            if "texts" not in data or not isinstance(data["texts"], list):
                print(f"[⚠️ Skip] {name} — no valid 'texts' field found")
                failed += 1
                continue

            all_texts = []
            for block in data["texts"]:
                # docling keys are sometimes "text", sometimes "content"
                if isinstance(block, dict):
                    txt = block.get("text") or block.get("content") or ""
                    txt = txt.strip()
                    if txt:
                        all_texts.append(txt)

            if not all_texts:
                print(f"[⚠️ Empty] {name} — no usable text extracted")
                failed += 1
                continue

            # === Concatenate and chunk ===
            full_text = "\n".join(all_texts)
            chunks = wrap(full_text, chunk_size)

            # === Write output ===
            with open(chunk_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)

            print(f"[✅ OK] {name}: {len(chunks)} chunks created.")
            success += 1

        except Exception as e:
            print(f"[❌ FAIL] {name}: {e}")
            failed += 1

    # === Summary ===
    print("\n==================== SUMMARY ====================")
    print(f"✅ Successfully chunked: {success}")
    print(f"⏩ Skipped (already done): {skipped}")
    print(f"❌ Failed or empty: {failed}")
    print(f"📂 Output folder: {output_dir}")
    print("=================================================")


if __name__ == "__main__":
    split_texts()
