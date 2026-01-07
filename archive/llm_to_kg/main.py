from src.pdf_to_text import parse_pdfs
from src.pdf_to_image import extract_images
from src.chunk_text import split_texts
from src.extract_triples_text import extract_triples_text
from src.extract_triples_visual import extract_triples_visual
from src.merge_triples import merge_triples
from src.merge_clean_graph import build_graph
from src.visualize_graph import visualize_graph

if __name__ == "__main__":
    print("Step 1A: Parsing PDFs to text...")
    parse_pdfs()

    print("Step 1B: Extracting figures from PDFs...")
    extract_images()

    print("Step 2: Splitting text into chunks...")
    split_texts()

    print("Step 3A: Extracting textual triples with Qwen2.5...")
    extract_triples_text()

    print("Step 3B: Extracting visual triples with Qwen3-VL...")
    extract_triples_visual()

    print("Step 4: Merging text + visual triples...")
    merged = merge_triples()

    print("Step 5: Building knowledge graph...")
    G = build_graph(triple_dir="data/triples_merged")

    print("Step 6: Visualizing graph...")
    visualize_graph()

    print("✅ Dual-channel Graph RAG pipeline completed successfully.")
