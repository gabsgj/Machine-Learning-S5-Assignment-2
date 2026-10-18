"""Experiment 4: Irrelevant Capabilities Analysis.

Section 7.4:
Introduce capabilities that do not contribute to the specified goal.
Test whether the representation distinguishes useful capabilities from irrelevant ones.
Goal G: Order.exists = true, Payment.status = SUCCESS, Notification.sent = true.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

from src.data.ecommerce_dataset import build_ecommerce_domain
from src.embedding.encoder import CapabilityEncoder
from src.embedding.metrics import goal_relevance_score


def run_experiment_4(save_plot: bool = True):
    print("=" * 60)
    print("EXPERIMENT 4: Goal Relevance & Irrelevant Capability Filtering")
    print("=" * 60)

    domain = build_ecommerce_domain()
    schema = domain["schema"]
    encoder = CapabilityEncoder(schema)
    goal = domain["goal"]
    init_state = domain["initial_state"]
    caps = domain["capabilities"]

    v_goal = encoder.encode_goal(goal)
    v_init = encoder.encode_state(init_state)

    results = []
    print(f"{'Capability':<28} | {'Type':<12} | {'Goal Relevance':<15} | {'Category'}")
    print("-" * 75)

    for c in caps:
        v_c = encoder.encode_capability(c)
        rel = goal_relevance_score(v_c, v_goal, v_init, schema)
        
        if rel > 0.3:
            category = "HIGHLY_USEFUL"
        elif rel > 0.05:
            category = "SUPPORTING"
        elif rel >= -0.05:
            category = "IRRELEVANT"
        else:
            category = "COUNTER_PRODUCTIVE"
            
        print(f"{c.name:<28} | {c.capability_type.value:<12} | {rel:<+15.4f} | {category}")
        results.append({
            "name": c.name,
            "type": c.capability_type.value,
            "relevance": rel,
            "category": category
        })

    # Sort by relevance descending
    results.sort(key=lambda x: x["relevance"], reverse=True)

    if save_plot:
        names = [r["name"] for r in results]
        scores = [r["relevance"] for r in results]
        colors = ['#16a34a' if s > 0.2 else ('#eab308' if s > 0 else ('#9ca3af' if s == 0 else '#dc2626')) for s in scores]

        fig, ax = plt.subplots(figsize=(9, 5))
        y_pos = np.arange(len(names))
        bars = ax.barh(y_pos, scores, color=colors, edgecolor='black', alpha=0.85)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontweight='bold')
        ax.invert_yaxis()  # Highest at top
        ax.set_xlabel('Goal Relevance Projection Score [-1, 1]', fontweight='bold')
        ax.set_title('Goal Alignment: Distinguishing Useful vs Irrelevant Capabilities', pad=15, fontweight='bold')
        ax.axvline(0, color='gray', linestyle='--', linewidth=1)
        ax.set_xlim(-0.6, 1.0)

        for bar in bars:
            w = bar.get_width()
            offset = 0.02 if w >= 0 else -0.08
            ax.text(w + offset, bar.get_y() + bar.get_height()/2, f"{w:+.2f}",
                    va='center', fontsize=8, fontweight='bold')

        plt.tight_layout()
        plt.savefig("results/figures/exp4_goal_relevance.png", dpi=200)
        plt.close()
        print("  -> Saved plot: results/figures/exp4_goal_relevance.png")

    return results


if __name__ == "__main__":
    run_experiment_4()
