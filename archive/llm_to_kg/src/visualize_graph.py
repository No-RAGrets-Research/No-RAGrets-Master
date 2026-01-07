import matplotlib.pyplot as plt
import networkx as nx
import pickle

def visualize_graph(graph_path="outputs/knowledge_graph.gpickle", out_file="outputs/graph_visualization.png"):
    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    if G.number_of_nodes() == 0:
        print("⚠️ Graph is empty — no nodes or edges to visualize.")
        return

    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G, k=0.3)
    nx.draw(G, pos, with_labels=True, node_size=50, font_size=6, edge_color="gray")
    plt.savefig(out_file, dpi=300)
    plt.close()

    print(f"✅ Graph visualization saved to {out_file}")
