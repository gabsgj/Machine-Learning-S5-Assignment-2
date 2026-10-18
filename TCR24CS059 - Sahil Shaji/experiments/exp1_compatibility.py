"""
Experiment 1: Capability Compatibility (Section 7 Experiment 1).
Investigates whether the embedding representation distinguishes:
  - C1 -> C2 (Compatible: CreateOrder -> MakePayment)
  - C1 -> C3 (Incompatible: CreateOrder -> CancelCart)
Also examines the full compatibility matrix vs functional similarity matrix.
"""

import os
import sys
from typing import Dict, Any, Tuple
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from capability_embedding import (
    CapabilityEmbeddingSystem,
    composability,
    functional_similarity,
    precondition_effect_compatibility,
    input_output_compatibility
)
from datasets.ecommerce import get_ecommerce_capabilities, get_ecommerce_initial_state, get_ecommerce_goal
from capability_embedding.visualization.plots import plot_compatibility_matrix


def run_experiment_1(figures_dir: str = "figures") -> Dict[str, Any]:
    """Runs Experiment 1 and returns structured results."""
    print("=" * 60)
    print("Running Experiment 1: Capability Compatibility Analysis")
    print("=" * 60)

    # Initialize domain and embedding system
    caps = get_ecommerce_capabilities()
    system = CapabilityEmbeddingSystem()

    # Register domain entities
    state = get_ecommerce_initial_state()
    goal = get_ecommerce_goal()
    system.schema.auto_register_from_domain(
        states=[state],
        capabilities=list(caps.values()),
        goals=[goal]
    )

    # Encode test capabilities
    c1 = caps["CreateOrder_API"]
    c2 = caps["MakePayment"]
    c3 = caps["CancelCart"]
    c4 = caps["SendNotification"]
    c5 = caps["CheckInventory"]

    z1 = system.encode_capability(c1)
    z2 = system.encode_capability(c2)
    z3 = system.encode_capability(c3)
    z4 = system.encode_capability(c4)
    z5 = system.encode_capability(c5)

    # 1. Test canonical pattern from Section 7: C1 -> C2 vs C1 -> C3
    comp_c1_c2 = composability(z1, z2)
    pe_c1_c2 = precondition_effect_compatibility(z1, z2)

    comp_c1_c3 = composability(z1, z3)
    pe_c1_c3 = precondition_effect_compatibility(z1, z3)

    print(f"\n[Pattern Verification]")
    print(f"C1: {c1.name} (Eff: {c1.effects})")
    print(f"C2: {c2.name} (Pre: {c2.preconditions})")
    print(f"C3: {c3.name} (Pre: {c3.preconditions})")
    print(f"-> Composability(C1, C2): {comp_c1_c2:.4f} (PE: {pe_c1_c2:.4f}) [COMPATIBLE]")
    print(f"-> Composability(C1, C3): {comp_c1_c3:.4f} (PE: {pe_c1_c3:.4f}) [INCOMPATIBLE]")

    # 2. Build full pairwise compatibility & similarity matrices
    test_caps = [c1, c2, c3, c4, c5]
    test_embeddings = [z1, z2, z3, z4, z5]
    labels = ["C1:CreateOrder", "C2:MakePayment", "C3:CancelCart", "C4:Notify", "C5:CheckInv"]
    n = len(test_caps)

    comp_matrix = np.zeros((n, n), dtype=np.float64)
    sim_matrix = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        for j in range(n):
            comp_matrix[i, j] = composability(test_embeddings[i], test_embeddings[j])
            sim_matrix[i, j] = functional_similarity(test_embeddings[i], test_embeddings[j])

    # 3. Save figure
    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "exp1_compatibility_matrix.png")
    plot_compatibility_matrix(labels, comp_matrix, sim_matrix, fig_path)
    print(f"\n[Plot Saved] Pairwise compatibility and similarity heatmaps -> {fig_path}")

    return {
        "comp_c1_c2": float(comp_c1_c2),
        "comp_c1_c3": float(comp_c1_c3),
        "pe_c1_c2": float(pe_c1_c2),
        "pe_c1_c3": float(pe_c1_c3),
        "comp_matrix": comp_matrix.tolist(),
        "sim_matrix": sim_matrix.tolist(),
        "labels": labels,
        "figure_path": fig_path
    }


if __name__ == "__main__":
    run_experiment_1()
