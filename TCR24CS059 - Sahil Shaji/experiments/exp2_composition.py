"""
Experiment 2: Capability Composition (Section 7 Experiment 2).
Investigates C1 -> C2 -> C3 sequential composition:
  - Vector relation between composite capability and atomic components
  - Weakest precondition absorption and effect accumulation
  - Operational attribute composition fidelity (latency additivity, reliability multiplicativity)
  - Associativity verification: (z1 o z2) o z3 == z1 o (z2 o z3)
  - State space trajectory projection
"""

import os
import sys
from typing import Dict, Any
import numpy as np
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from capability_embedding import (
    CapabilityEmbeddingSystem,
    compose_sequence,
    compose_embeddings,
    compose_vector_sequence,
    functional_similarity
)
from datasets.ecommerce import get_ecommerce_capabilities, get_ecommerce_initial_state, get_ecommerce_goal
from capability_embedding.visualization.plots import plot_composition_trajectory


def run_experiment_2(figures_dir: str = "figures") -> Dict[str, Any]:
    print("=" * 60)
    print("Running Experiment 2: Capability Composition Analysis")
    print("=" * 60)

    caps = get_ecommerce_capabilities()
    system = CapabilityEmbeddingSystem()

    state_init = get_ecommerce_initial_state()
    goal = get_ecommerce_goal()
    system.schema.auto_register_from_domain(
        states=[state_init],
        capabilities=list(caps.values()),
        goals=[goal]
    )

    # Sequence: C1 (CreateOrder) -> C2 (MakePayment) -> C3 (SendNotification)
    c1 = caps["CreateOrder_API"]
    c2 = caps["MakePayment"]
    c3 = caps["SendNotification"]

    # 1. Symbolic Composition
    c12 = compose_sequence([c1, c2], name="C12_CompletePayment")
    c123 = compose_sequence([c1, c2, c3], name="C123_CompletePurchase")

    # 2. Vector Space Composition
    z1 = system.encode_capability(c1)
    z2 = system.encode_capability(c2)
    z3 = system.encode_capability(c3)

    z12_vec = compose_embeddings(z1, z2)
    z123_vec = compose_embeddings(z12_vec, z3)

    # Test Associativity: (z1 o z2) o z3 vs z1 o (z2 o z3)
    z23_vec = compose_embeddings(z2, z3)
    z_assoc = compose_embeddings(z1, z23_vec)
    assoc_diff = float(np.linalg.norm(z123_vec.raw - z_assoc.raw))

    # Test Homomorphism / Fidelity: encode(C123_symbolic) vs z123_vec
    z123_symbolic_encoded = system.encode_capability(c123)
    fidelity_diff = float(np.linalg.norm(z123_symbolic_encoded.delta_vector - z123_vec.delta_vector))

    print(f"\n[Symbolic vs Vector Composition]")
    print(f"C1 Effects: {c1.effects}")
    print(f"C2 Effects: {c2.effects}")
    print(f"C3 Effects: {c3.effects}")
    print(f"Composite Effects: {c123.effects}")
    print(f"Composite Preconditions: {c123.preconditions} (Internal preconditions absorbed!)")
    print(f"Associativity Norm Difference ||(z1 o z2) o z3 - z1 o (z2 o z3)||: {assoc_diff:.6f}")
    print(f"Effect Subspace Fidelity ||encode(C_symb) - z_vec||: {fidelity_diff:.6f}")

    # Operational attributes
    print(f"\n[Operational Aggregation]")
    print(f"C1 Latency: {c1.quality.execution_time_ms} ms | Rel: {c1.quality.reliability}")
    print(f"C2 Latency: {c2.quality.execution_time_ms} ms | Rel: {c2.quality.reliability}")
    print(f"C3 Latency: {c3.quality.execution_time_ms} ms | Rel: {c3.quality.reliability}")
    print(f"Composite Latency (Symbolic): {c123.quality.execution_time_ms} ms | Vector Decoded: {z123_vec.execution_time} ms")
    print(f"Composite Rel (Symbolic): {c123.quality.reliability:.4f} | Vector Decoded: {z123_vec.reliability:.4f}")

    # 3. Trajectory of States through execution
    s0 = state_init
    s1 = c1.apply(s0)
    s2 = c2.apply(s1)
    s3 = c3.apply(s2)

    z_s0 = system.encode_state(s0, name="S0 (Initial)")
    z_s1 = system.encode_state(s1, name="S1 (Order Created)")
    z_s2 = system.encode_state(s2, name="S2 (Payment Confirmed)")
    z_s3 = system.encode_state(s3, name="S3 (Order Fulfilled)")
    z_g = system.encode_goal(goal, name="Goal")

    state_vectors = np.array([z_s0.raw, z_s1.raw, z_s2.raw, z_s3.raw, z_g.raw])
    pca = PCA(n_components=2, random_state=42)
    coords_2d = pca.fit_transform(state_vectors)

    labels = ["S0: Initial State", "S1: Order Created", "S2: Paid", "S3: Notified", "Target Goal G"]

    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "exp2_composition_trajectory.png")
    plot_composition_trajectory(coords_2d, labels, fig_path)
    print(f"\n[Plot Saved] State space trajectory -> {fig_path}")

    return {
        "assoc_norm_diff": assoc_diff,
        "fidelity_diff": fidelity_diff,
        "c123_latency_ms": z123_vec.execution_time,
        "c123_reliability": z123_vec.reliability,
        "c123_preconditions": c123.preconditions,
        "c123_effects": c123.effects,
        "figure_path": fig_path
    }


if __name__ == "__main__":
    run_experiment_2()
