"""
Produces pairwise similarity and compatibility matrices across the full
capability set, saved as CSV (for the report appendix) and PNG heatmaps
(for the report figures).
"""

import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dataset import build_capabilities, build_states, build_goals
from embedding import Embedder


def main():
    caps = build_capabilities()
    states = build_states()
    goals = build_goals()
    emb = Embedder(list(caps.values()), extra_states=list(states.values()), extra_goals=list(goals.values()))

    ids = list(caps.keys())
    vecs = {cid: emb.encode_capability(c) for cid, c in caps.items()}

    n = len(ids)
    sim_full = np.zeros((n, n))
    sim_pure = np.zeros((n, n))
    compat = np.zeros((n, n))  # compat[i][j] = score of i -> j

    for a_i, a in enumerate(ids):
        for b_i, b in enumerate(ids):
            sim_full[a_i, b_i] = emb.similarity(vecs[a], vecs[b], block="full")
            sim_pure[a_i, b_i] = emb.similarity(vecs[a], vecs[b], block="pure_function")
            compat[a_i, b_i] = emb.compatibility(caps[a], caps[b])["score"]

    # ---- CSV export ----
    for name, mat in [("similarity_full", sim_full), ("similarity_pure_function", sim_pure),
                        ("compatibility_score", compat)]:
        with open(f"{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([""] + ids)
            for i, row_id in enumerate(ids):
                w.writerow([row_id] + [f"{v:.3f}" for v in mat[i]])
        print(f"wrote {name}.csv")

    # ---- Heatmaps ----
    def heatmap(mat, title, fname, cmap="viridis"):
        fig, ax = plt.subplots(figsize=(9, 8))
        im = ax.imshow(mat, cmap=cmap, vmin=0, vmax=1)
        ax.set_xticks(range(n)); ax.set_xticklabels(ids, rotation=90, fontsize=8)
        ax.set_yticks(range(n)); ax.set_yticklabels(ids, fontsize=8)
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        print(f"wrote {fname}")

    heatmap(sim_full, "Full-vector cosine similarity (incl. operational attributes)", "heatmap_similarity_full.png")
    heatmap(sim_pure, "Pure-function cosine similarity (P/E/I/O/K/R only)", "heatmap_similarity_pure_function.png")
    heatmap(compat, "Directed compatibility score  (row -> column)", "heatmap_compatibility.png", cmap="magma")


if __name__ == "__main__":
    main()
