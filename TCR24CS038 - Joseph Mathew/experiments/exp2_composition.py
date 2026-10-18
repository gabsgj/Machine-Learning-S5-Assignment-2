"""Experiment 2: Capability Composition Analysis.

Section 7.2:
Given C1 -> C2 -> C3:
- C1: CreateOrder
- C2: MakePayment
- C3: SendNotification

Construct the composite capability and investigate how its vector relates
to the vectors of C1, C2, C3.
Evaluates:
- Associativity: (C3 o C2) o C1 == C3 o (C2 o C1)
- Homomorphism: phi(C_sym) vs v_alg
- Subspace progression (preconditions consumed, effects accumulated, cost added, reliability multiplied)
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

from src.data.ecommerce_dataset import build_ecommerce_domain
from src.embedding.encoder import CapabilityEncoder
from src.embedding.composition import compose_capabilities, compose_sequence, compose_vectors
from src.embedding.metrics import cosine_similarity


def run_experiment_2(save_plot: bool = True):
    print("=" * 60)
    print("EXPERIMENT 2: Capability Composition & Vector Relations")
    print("=" * 60)

    domain = build_ecommerce_domain()
    schema = domain["schema"]
    encoder = CapabilityEncoder(schema)
    caps = domain["named_capabilities"]

    c1 = caps["CreateOrder"]
    c2 = caps["MakePayment"]
    c3 = caps["SendNotification"]

    v1 = encoder.encode_capability(c1)
    v2 = encoder.encode_capability(c2)
    v3 = encoder.encode_capability(c3)

    # 1. Sequential symbolic composition: C12 = C2 o C1; C123 = C3 o C12
    c12_sym = compose_capabilities(c1, c2)
    c123_sym = compose_capabilities(c12_sym, c3)

    # 2. Algebraic composition in vector space
    v12_alg = compose_vectors(v1, v2, schema)
    v123_alg = compose_vectors(v12_alg, v3, schema)

    # 3. Direct encoding of symbolic composite
    v123_sym_enc = encoder.encode_capability(c123_sym)

    # Compare algebraic vs symbolic encoding (Homomorphism fidelity)
    overall_sim = cosine_similarity(v123_alg, v123_sym_enc)
    mae = float(np.mean(np.abs(v123_alg - v123_sym_enc)))

    print(f"Composite Capability: '{c123_sym.name}'")
    print(f"  Total Steps: {c123_sym.sub_capabilities}")
    print(f"  Preconditions required at start: {[f'{p.variable}={p.value}' for p in c123_sym.preconditions]}")
    print(f"  Effects achieved at end: {[f'{e.variable}={e.value}' for e in c123_sym.effects]}")
    print(f"  Cumulative Cost: ${c123_sym.cost.monetary_cost:.3f}, Time: {c123_sym.cost.execution_time_ms} ms")
    print(f"  Compound Reliability: {c123_sym.reliability:.4f} (0.99 * 0.98 * 0.995 = {0.99 * 0.98 * 0.995:.4f})")
    print(f"  Bottleneck Availability: {c123_sym.availability:.2f}")
    print()
    print(f"Vector Homomorphism Evaluation:")
    print(f"  Cosine Similarity between phi(C123_sym) and v123_alg: {overall_sim:.5f}")
    print(f"  Mean Absolute Error (MAE): {mae:.5f}")

    # 4. Associativity Verification: (C3 o C2) o C1 vs C3 o (C2 o C1)
    c23_sym = compose_capabilities(c2, c3)
    c_left_assoc = compose_capabilities(c1, c23_sym)   # (C3 o C2) o C1
    c_right_assoc = compose_capabilities(c12_sym, c3)  # C3 o (C2 o C1)

    v_assoc_left = encoder.encode_capability(c_left_assoc)
    v_assoc_right = encoder.encode_capability(c_right_assoc)
    assoc_diff = float(np.linalg.norm(v_assoc_left - v_assoc_right))
    print(f"Associativity Test || v_((C3 o C2) o C1) - v_(C3 o (C2 o C1)) ||: {assoc_diff:.6f}")

    # Plot Subspace Decomposition Comparison
    if save_plot:
        subspaces = ["Precond", "Effects", "Inputs", "Outputs", "Functional", "Mechanism", "Operational", "Resources"]
        slices = [
            schema.slice_preconditions, schema.slice_effects, schema.slice_inputs,
            schema.slice_outputs, schema.slice_functional, schema.slice_mechanism,
            schema.slice_operational, schema.slice_resources
        ]

        cos_sims = []
        for sl in slices:
            s_alg = v123_alg[sl]
            s_sym = v123_sym_enc[sl]
            sim = cosine_similarity(s_alg, s_sym) if (np.linalg.norm(s_alg) > 1e-6 and np.linalg.norm(s_sym) > 1e-6) else 1.0
            cos_sims.append(sim)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        bars = ax.bar(subspaces, cos_sims, color="#2563eb", edgecolor="black", alpha=0.85)
        ax.set_ylim(0.0, 1.1)
        ax.set_ylabel("Subspace Cosine Fidelity", fontweight="bold")
        ax.set_title("Homomorphic Fidelity of Vector Composition Across Subspaces", pad=15, fontweight="bold")
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.2f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8, fontweight="bold")
        plt.tight_layout()
        plt.savefig("results/figures/exp2_composition_fidelity.png", dpi=200)
        plt.close()
        print("  -> Saved plot: results/figures/exp2_composition_fidelity.png")

    results = {
        "overall_sim": overall_sim,
        "mae": mae,
        "associativity_diff": assoc_diff,
        "compound_reliability": c123_sym.reliability,
        "cumulative_cost": c123_sym.cost.monetary_cost,
        "cumulative_time_ms": c123_sym.cost.execution_time_ms
    }
    return results


if __name__ == "__main__":
    run_experiment_2()
