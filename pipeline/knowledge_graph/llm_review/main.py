# main.py
from pathlib import Path
from utils.text_loader import load_paper
from utils.llm_runner import run_llm
from utils.result_merger import merge_results

# === Configuration ===
PAPERS_DIR = Path("../../data/papers")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

RUBRICS = [
    "prompts/rubric1_methodology.txt",
    "prompts/rubric2_reproducibility.txt",
    "prompts/rubric3_rigor.txt",
    "prompts/rubric4_data.txt",
    "prompts/rubric5_presentation.txt",
    "prompts/rubric6_references.txt"
]
SYNTH_PATH = "prompts/synthesizer.txt"

# === Find all PDF files ===
pdf_files = sorted(PAPERS_DIR.glob("*.pdf"))
if not pdf_files:
    raise FileNotFoundError("❌ No PDF files found in /papers directory.")

print(f"📚 Found {len(pdf_files)} PDF file(s):")
for f in pdf_files:
    print(f"   - {f.name}")

# === Process each paper ===
for pdf_path in pdf_files:
    print("\n" + "="*80)
    print(f"📄 Processing paper: {pdf_path.name}")
    print("="*80)

    # 1️⃣ Create per-paper output folder
    paper_output_dir = OUTPUT_DIR / pdf_path.stem
    paper_output_dir.mkdir(exist_ok=True)
    print(f"📁 Created output folder: {paper_output_dir}")

    # 2️⃣ Load paper text (Docling parser inside load_paper)
    paper_text = load_paper(str(pdf_path))
    print(f"✅ Loaded paper successfully: {pdf_path.name}")

    # 3️⃣ Run each rubric
    rubric_outputs = []
    for rubric_path in RUBRICS:
        rubric_name = Path(rubric_path).stem
        rubric_prompt = Path(rubric_path).read_text(encoding="utf-8")

        print(f"🔍 Running rubric: {rubric_name} ...")
        result = run_llm(rubric_prompt + "\n\n" + paper_text)
        rubric_outputs.append(result)

        # Save individual rubric result inside paper folder
        output_file = paper_output_dir / f"{rubric_name}_output.md"
        output_file.write_text(result, encoding="utf-8")
        print(f"💾 Saved: {output_file}")

    # 4️⃣ Merge rubric results
    print("🧩 Merging rubric outputs...")
    merged_text = merge_results(rubric_outputs)

    # Save merged intermediate text
    merged_file = paper_output_dir / "merged_results.md"
    merged_file.write_text(merged_text, encoding="utf-8")

    # 5️⃣ Generate final synthesized review
    print("🧠 Generating final evidence-based summary...")
    synth_prompt = Path(SYNTH_PATH).read_text(encoding="utf-8")
    final_summary = run_llm(synth_prompt + "\n\n" + merged_text)

    final_file = paper_output_dir / "final_summary.md"
    final_file.write_text(final_summary, encoding="utf-8")

    print(f"✅ Review complete for {pdf_path.name}")
    print(f"📄 Final summary saved to: {final_file}")
