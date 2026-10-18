"""Experiment 1: Capability Compatibility.

Section 7.1:
Given C1, C2, C3, where C1 composes with C2 but not C3:
- C1: CreateOrder (Effect: OrderExists = true)
- C2: MakePayment (Precondition: OrderExists = true)
- C3: CancelCart (Precondition: OrderExists = false)

Investigates whether the representation distinguishes compatible vs incompatible pairs.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

from src.data.ecommerce_dataset import build_ecommerce_domain
from src.embedding.encoder import CapabilityEncoder
from src.embedding.metrics import composability_score, functional_similarity


def run_experiment_1(save_plot: bool = True):
    print("=" * 60)
    print("EXPERIMENT 1: Capability Compatibility Analysis")
    print("=" * 60)

    domain = build_ecommerce_domain()
    schema = domain["schema"]
    encoder = CapabilityEncoder(schema)
    caps = domain["named_capabilities"]

    c1 = caps["CreateOrder"]
    c2 = caps["MakePayment"]
    c3 = caps["CancelCart"]

    v1 = encoder.encode_capability(c1)
    v2 = encoder.encode_capability(c2)
    v3 = encoder.encode_capability(c3)

    # 1. Evaluate directed composability
    score_12, breakdown_12 = composability_score(v1, v2, schema)
    score_13, breakdown_13 = composability_score(v1, v3, schema)
    score_21, breakdown_21 = composability_score(v2, v1, schema)  # reverse direction

    # 2. Evaluate functional similarity
    sim_12 = functional_similarity(v1, v2, schema)
    sim_13 = functional_similarity(v1, v3, schema)

    print(f"[C1 -> C2] (CreateOrder -> MakePayment):")
    print(f"  Composability Score: {score_12:+.4f} (State Compat: {breakdown_12['state_compatibility']:+.2f}, Data Compat: {breakdown_12['data_compatibility']:+.2f})")
    print(f"  Functional Similarity: {sim_12:+.4f}")
    print()
    print(f"[C1 -> C3] (CreateOrder -> CancelCart):")
    print(f"  Composability Score: {score_13:+.4f} (State Compat: {breakdown_13['state_compatibility']:+.2f}, Data Compat: {breakdown_13['data_compatibility']:+.2f})")
    print(f"  Functional Similarity: {sim_13:+.4f}")
    print()
    print(f"[C2 -> C1] (MakePayment -> CreateOrder - Directional Asymmetry Check):")
    print(f"  Composability Score: {score_21:+.4f} (State Compat: {breakdown_21['state_compatibility']:+.2f}, Data Compat: {breakdown_21['data_compatibility']:+.2f})")

    # Full pairwise composability matrix
    test_cap_names = ["CreateOrder", "MakePayment", "CancelCart", "SendNotification", "ReserveInventory"]
    matrix = np.zeros((len(test_cap_names), len(test_cap_names)))
    
    for i, name_i in enumerate(test_cap_names):
        vi = encoder.encode_capability(caps[name_i])
        for j, name_j in enumerate(test_cap_names):
            vj = encoder.encode_capability(caps[name_j])
            s, _ = composability_score(vi, vj, schema)
            matrix[i, j] = s

    if save_plot:
        fig, ax = plt.subplots(figsize=(7, 6))
        cax = ax.matshow(matrix, cmap="RdYlGn", vmin=-1.0, vmax=1.0)
        fig.colorbar(cax)
        ax.set_xticks(range(len(test_cap_names)))
        ax.set_yticks(range(len(test_cap_names)))
        ax.set_xticklabels(test_cap_names, rotation=45, ha="left")
        ax.set_yticklabels(test_cap_names)
        ax.set_title("Directed Capability Composability Matrix C(Ci -> Cj)", pad=20, fontweight="bold")
        
        for i in range(len(test_cap_names)):
            for j in range(len(test_cap_names)):
                ax.text(j, i, f"{matrix[i, j]:+.2f}", ha="center", va="center", color="black", fontsize=9, fontweight="bold")
        
        plt.tight_layout()
        plt.savefig("results/figures/exp1_compatibility_matrix.png", dpi=200)
        plt.close()
        print("  -> Saved heatmap: results/figures/exp1_compatibility_matrix.png")

    results = {
        "score_c1_c2": score_12,
        "score_c1_c3": score_13,
        "score_c2_c1": score_21,
        "sim_c1_c2": sim_12,
        "sim_c1_c3": sim_13,
        "pairwise_matrix": matrix.tolist(),
        "matrix_labels": test_cap_names
    }
    return results


if __name__ == "__main__":
    run_experiment_1()
