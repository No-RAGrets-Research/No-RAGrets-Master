import json
import re
import networkx as nx
from pathlib import Path
import matplotlib.pyplot as plt

def parse_triples(raw_text):
    """
    Extract (subject, relation, object) triples from string
    """
    triples = []

    if not raw_text:
        return triples

    # ('A', 'B', 'C')
    pattern_tuple = re.findall(r"\(['\"](.*?)['\"],\s*['\"](.*?)['\"],\s*['\"](.*?)['\"]\)", raw_text)
    for s, r, o in pattern_tuple:
        triples.append((s.strip(), r.strip(), o.strip()))

    # A, B, C
    pattern_csv = re.findall(r"([\w\s\-]+),\s*([\w\s\-]*),\s*([\w\s\-\(\)~0-9]+)", raw_text)
    for s, r, o in pattern_csv:
        if s and o:
            triples.append((s.strip(), r.strip(), o.strip()))

    # A is B / A are B / A means B
    pattern_is = re.findall(r"([A-Z][A-Za-z0-9_\s\-]+?)\s+(is|are|means)\s+([^\.]+)", raw_text)
    for s, r, o in pattern_is:
        triples.append((s.strip(), r.strip(), o.strip()))

    return triples


def build_graph(triple_dir="data/triples_merged", output_dir="data/graph_per_paper"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # === Build graph for each paper separately ===
    for f in Path(triple_dir).glob("*.json"):
        if f.stem == "merged_triples":  # Skip the merged file
            continue

        paper_name = f.stem
        print(f"\nBuilding graph for: {paper_name}")

        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        G = nx.DiGraph()
        triple_count = 0

        for item in data:
            raw = item.get("triples_raw", "")
            triples = parse_triples(raw)
            for s, r, o in triples:
                if s and o:
                    G.add_edge(s, o, label=r)
                    triple_count += 1

        print(f"Graph built for {paper_name}: {len(G.nodes())} nodes, {len(G.edges())} edges")

        if len(G) == 0:
            print("⚠️ Empty graph, skipped visualization.")
            continue

        plt.figure(figsize=(14, 10))
        pos = nx.spring_layout(G, k=0.4)
        nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=400)
        nx.draw_networkx_edges(G, pos, edge_color="gray", alpha=0.3)
        nx.draw_networkx_labels(G, pos, font_size=8)
        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)

        out_path = Path(output_dir) / f"{paper_name}.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()  # Fixed the typo

if __name__ == "__main__":
    build_graph()
