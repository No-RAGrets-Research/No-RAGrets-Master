import json
from pathlib import Path

def merge_triples(text_dir="data/triples_text", visual_dir="data/triples_visual", output_dir="data/triples_merged"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Collect all text triples
    text_files = {f.stem.replace("_triples", ""): f for f in Path(text_dir).glob("*.json")}
    visual_files = {f.stem.replace("_visual_triples", ""): f for f in Path(visual_dir).glob("*.json")}

    # Iterate through each paper
    paper_names = sorted(set(text_files.keys()) | set(visual_files.keys()))
    total_count = 0

    for paper in paper_names:
        merged = []

        # Read text triples
        if paper in text_files:
            with open(text_files[paper], "r", encoding="utf-8") as f:
                data = json.load(f)
                for t in data:
                    t["source"] = "text"
                merged.extend(data)

        # Read visual triples (if exists)
        if paper in visual_files:
            with open(visual_files[paper], "r", encoding="utf-8") as f:
                data = json.load(f)
                for t in data:
                    t["source"] = "visual"
                merged.extend(data)

        # Save the merged file for this paper
        out_path = Path(output_dir) / f"{paper}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        print(f"✅ Merged {len(merged)} triples into {out_path}")
        total_count += len(merged)

    print(f"\n Finished merging all papers — total {total_count} triples across {len(paper_names)} papers.")
    return output_dir


if __name__ == "__main__":
    merge_triples()
