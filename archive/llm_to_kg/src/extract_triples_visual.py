from transformers import AutoProcessor, AutoModelForImageTextToText
from pathlib import Path
from PIL import Image
import torch, json, os, gc

def extract_triples_visual(input_dir="data/images", output_dir="data/triples_visual",
                           model_name="Qwen/Qwen3-VL-4B-Instruct"):

    print("Scanning input directory:", Path(input_dir).resolve())
    print("Found subfolders:", [d.name for d in Path(input_dir).iterdir()])

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ✅ 环境变量设置（防止显存碎片化）
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    # ✅ 加载模型
    processor = AutoProcessor.from_pretrained(model_name)
    model = AutoModelForImageTextToText.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch.float16
    )
    print(f"Using {model_name} on device {model.device}")

    for pdf_dir in Path(input_dir).iterdir():
        if not pdf_dir.is_dir():
            continue

        meta_path = pdf_dir / "figures_metadata.json"
        if not meta_path.exists():
            print(f"[⚠️ Skip] {pdf_dir.name}: no metadata file found.")
            continue

        out_file = Path(output_dir) / f"{pdf_dir.name}_visual_triples.json"
        if out_file.exists() and os.path.getsize(out_file) > 0:
            print(f"[Skip] {pdf_dir.name}: visual triples already exist.")
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            figures_meta = json.load(f)

        if not figures_meta:
            print(f"[⚠️ Skip] {pdf_dir.name}: no figures listed in metadata.")
            continue

        triples_all = []
        print(f"Processing {pdf_dir.name} ({len(figures_meta)} figures)...")

        for fig in figures_meta:
            img_path = Path(fig["image_path"])
            caption = fig.get("caption", "")

            if not img_path.exists():
                print(f"[⚠️ Skip] Missing image: {img_path}")
                continue

            image = Image.open(img_path).convert("RGB")

            # 限制分辨率，防止爆显存
            image.thumbnail((1280, 1280))

            # 包含 caption 信息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {
                            "type": "text",
                            "text": (
                                "You are a scientific reasoning assistant.\n"
                                "Analyze this figure together with its caption, and extract factual triples "
                                "in the format (subject, relation, object).\n"
                                "Focus on scientific entities and relationships.\n"
                                f"Caption: {caption}\n\nOutput JSON list only:"
                            ),
                        },
                    ],
                }
            ]

            # 构造 prompt
            text_prompt = processor.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            inputs = processor(text=[text_prompt], images=[image], return_tensors="pt").to(model.device)

            try:
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_new_tokens=512)
                decoded = processor.batch_decode(outputs, skip_special_tokens=True)[0]

                try:
                    json_part = decoded[decoded.index("["): decoded.rindex("]") + 1]
                    triples = json.loads(json_part)
                except Exception:
                    triples = [{"raw_output": decoded}]

            except Exception as e:
                print(f"[❌ Error] {pdf_dir.name} - {img_path.name}: {e}")
                triples = [{"error": str(e)}]

            triples_all.append({
                "page": fig.get("page"),
                "caption": caption,
                "triples": triples
            })

            # 显存释放
            del inputs, outputs
            torch.cuda.empty_cache()
            gc.collect()

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(triples_all, f, ensure_ascii=False, indent=2)
        print(f"✅ Visual triples extracted for {pdf_dir.name}")

        # 每个论文结束后也释放显存
        torch.cuda.empty_cache()
        gc.collect()

    print(f"✅ All visual triples saved to {output_dir}")


if __name__ == "__main__":
    extract_triples_visual()
