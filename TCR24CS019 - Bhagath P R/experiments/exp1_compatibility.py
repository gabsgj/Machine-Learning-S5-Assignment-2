#!/usr/bin/env python3
"""
Experiment 1: Capability Compatibility
Investigates whether the vector embedding and compatibility metric
distinguish between compatible capabilities (C1 -> C2) and incompatible ones (C1 -> C3).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

from src.dataset.loader import BenchmarkLoader
from src.embedding import EmbeddingSystem


def run_experiment_1(save_plot: bool = True):
    print("=" * 80)
    print("  EXPERIMENT 1: CAPABILITY COMPATIBILITY EVALUATION")
    print("=" * 80)

    loader = BenchmarkLoader()
    problem = loader.load_ecommerce_benchmark()

    # Initialize Embedding System with problem's state variables
    from src.embedding.schema import EmbeddingSchema
    schema = EmbeddingSchema(state_variables=problem.state_variables)
    emb_system = EmbeddingSystem(schema)

    c1 = problem.get_capability("C1_CreateOrder")
    c2 = problem.get_capability("C2_MakePayment")
    c3 = problem.get_capability("C3_CancelCart")
    c4 = problem.get_capability("C4_SendNotification")
    c5 = problem.get_capability("C5_ApplyDiscount")

    assert c1 and c2 and c3 and c4 and c5, "Required capabilities not found in benchmark"

    # Evaluate the canonical trio from Assignment 2 Section 7.1:
    # C1 -> C2: Compatible (Order.exists=True enables Order.exists=True)
    # C1 -> C3: Incompatible (Order.exists=True conflicts with Order.exists=False)
    score_1_2 = emb_system.compatibility(c1, c2)
    score_1_3 = emb_system.compatibility(c1, c3)
    score_2_4 = emb_system.compatibility(c2, c4)
    score_5_1 = emb_system.compatibility(c5, c1)

    table_data = [
        ["C1 (CreateOrder) -> C2 (MakePayment)", "OrderExists=True (Satisfied)", "YES", f"{score_1_2.total_score:.4f}", f"{score_1_2.pe_score:.4f}", f"{score_1_2.io_score:.4f}", "Compatible"],
        ["C1 (CreateOrder) -> C3 (CancelCart)", "OrderExists=False (CONTRADICTION)", "NO", f"{score_1_3.total_score:.4f}", f"{score_1_3.pe_score:.4f}", f"{score_1_3.io_score:.4f}", score_1_3.explanation],
        ["C2 (MakePayment) -> C4 (SendNotification)", "Payment.status=SUCCESS (Satisfied)", "YES", f"{score_2_4.total_score:.4f}", f"{score_2_4.pe_score:.4f}", f"{score_2_4.io_score:.4f}", "Compatible"],
        ["C5 (ApplyDiscount) -> C1 (CreateOrder)", "Cart.exists=True (Preserved)", "YES", f"{score_5_1.total_score:.4f}", f"{score_5_1.pe_score:.4f}", f"{score_5_1.io_score:.4f}", "Compatible"],
    ]

    headers = ["Pair (Ci -> Cj)", "Precondition/Effect Overlap", "Compatible?", "Total Score", "PE Score", "IO Score", "Details"]
    print("\n1. CANONICAL COMPATIBILITY BENCHMARK RESULTS:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Compute pairwise compatibility matrix across all capabilities
    all_caps = [c1, c2, c3, c4, c5]
    cap_ids = [c.name for c in all_caps]
    n = len(all_caps)
    compat_matrix = np.zeros((n, n), dtype=np.float32)

    for i in range(n):
        for j in range(n):
            if i == j:
                compat_matrix[i, j] = 0.0  # self-transition not measured
            else:
                sc = emb_system.compatibility(all_caps[i], all_caps[j])
                compat_matrix[i, j] = sc.total_score

    print("\n2. FULL PAIRWISE COMPATIBILITY MATRIX:")
    matrix_headers = ["Source \\ Target"] + cap_ids
    matrix_rows = []
    for i in range(n):
        row = [cap_ids[i]] + [f"{compat_matrix[i, j]:.2f}" for j in range(n)]
        matrix_rows.append(row)
    print(tabulate(matrix_rows, headers=matrix_headers, tablefmt="grid"))

    if save_plot:
        os.makedirs("figures", exist_ok=True)
        plt.figure(figsize=(8, 6))
        plt.imshow(compat_matrix, cmap="YlGnBu", interpolation="nearest")
        plt.colorbar(label="Compatibility Score")
        plt.xticks(range(n), cap_ids, rotation=35, ha="right", fontsize=9)
        plt.yticks(range(n), cap_ids, fontsize=9)
        plt.title("Pairwise Capability Directional Compatibility Matrix (Ci -> Cj)", fontsize=11, fontweight="bold")

        for i in range(n):
            for j in range(n):
                text_col = "white" if compat_matrix[i, j] > 0.5 else "black"
                plt.text(j, i, f"{compat_matrix[i, j]:.2f}", ha="center", va="center", color=text_col, fontweight="bold")

        plt.tight_layout()
        out_path = "figures/exp1_compatibility_matrix.png"
        plt.savefig(out_path, dpi=200)
        plt.close()
        print(f"\n[Saved figure]: {out_path}")

    return {
        "score_1_2": score_1_2,
        "score_1_3": score_1_3,
        "compat_matrix": compat_matrix
    }


if __name__ == "__main__":
    run_experiment_1()
