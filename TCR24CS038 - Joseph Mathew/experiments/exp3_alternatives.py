"""Experiment 3: Alternative Implementations Analysis.

Section 7.3:
Provide capabilities that produce similar effects through different mechanisms:
- CreateOrder_API (POST /orders)
- CreateOrder_Database (INSERT orders)
- CreateOrder_GUI (CLICK submit_button)

Test whether the embedding captures their functional relationship without
incorrectly treating their implementations as identical.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

from src.data.ecommerce_dataset import build_ecommerce_domain
from src.embedding.encoder import CapabilityEncoder
from src.embedding.metrics import (
    cosine_similarity, functional_similarity, mechanism_similarity
)


def run_experiment_3(save_plot: bool = True):
    print("=" * 60)
    print("EXPERIMENT 3: Alternative Implementations (API, DB, GUI)")
    print("=" * 60)

    domain = build_ecommerce_domain()
    schema = domain["schema"]
    encoder = CapabilityEncoder(schema)
    caps = domain["named_capabilities"]

    c_api = caps["CreateOrder"]  # API
    c_db = caps["CreateOrder_Database"]
    c_gui = caps["CreateOrder_GUI"]

    v_api = encoder.encode_capability(c_api)
    v_db = encoder.encode_capability(c_db)
    v_gui = encoder.encode_capability(c_gui)

    triplets = [
        ("API vs DB", v_api, v_db),
        ("API vs GUI", v_api, v_gui),
        ("DB vs GUI", v_db, v_gui),
    ]

    metrics = []
    print(f"{'Pair':<15} | {'Functional Sim':<15} | {'Mechanism Sim':<15} | {'Overall Cosine':<15} | {'Euclidean Dist':<15}")
    print("-" * 80)

    for name, v_x, v_y in triplets:
        fun_sim = functional_similarity(v_x, v_y, schema)
        mech_sim = mechanism_similarity(v_x, v_y, schema)
        ovr_sim = cosine_similarity(v_x, v_y)
        dist = float(np.linalg.norm(v_x - v_y))
        print(f"{name:<15} | {fun_sim:<15.4f} | {mech_sim:<15.4f} | {ovr_sim:<15.4f} | {dist:<15.4f}")
        metrics.append({
            "pair": name,
            "functional_sim": fun_sim,
            "mechanism_sim": mech_sim,
            "overall_sim": ovr_sim,
            "euclidean_dist": dist
        })

    if save_plot:
        pairs = [m["pair"] for m in metrics]
        f_scores = [m["functional_sim"] for m in metrics]
        m_scores = [m["mechanism_sim"] for m in metrics]

        x = np.arange(len(pairs))
        width = 0.35

        fig, ax = plt.subplots(figsize=(7, 4.5))
        rects1 = ax.bar(x - width/2, f_scores, width, label='Functional Similarity (Substitutability)', color='#10b981')
        rects2 = ax.bar(x + width/2, m_scores, width, label='Mechanism Similarity (Technical Realization)', color='#ef4444')

        ax.set_ylabel('Similarity Score [-1, 1]', fontweight='bold')
        ax.set_title('Decoupled Semantic vs Mechanism Similarity for Alternative Implementations', pad=15, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(pairs, fontweight='bold')
        ax.set_ylim(-0.2, 1.15)
        ax.legend(loc='upper right')
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for rect in rects1 + rects2:
            h = rect.get_height()
            ax.annotate(f'{h:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold')

        plt.tight_layout()
        plt.savefig("results/figures/exp3_alternative_implementations.png", dpi=200)
        plt.close()
        print("  -> Saved plot: results/figures/exp3_alternative_implementations.png")

    return metrics


if __name__ == "__main__":
    run_experiment_3()
