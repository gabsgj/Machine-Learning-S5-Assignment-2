"""
Experiment 1: Capability Compatibility Analysis.
Investigates whether the vector embedding distinguishes compatible pairs (C1 -> C2)
from incompatible pairs (C1 -> C3), evaluates directional asymmetry (C1 -> C2 vs C2 -> C1),
and contrasts with naive flat cosine similarity.

Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from typing import Dict, Any
import numpy as np

from src.models import Capability
from src.embedding import CapabilityEmbeddingSpace
from dataset.dataset import build_benchmark_dataset


def run_experiment_1() -> Dict[str, Any]:
    dataset = build_benchmark_dataset()
    space = CapabilityEmbeddingSpace(
        state_variables=dataset["state_variables"],
        io_vocab=dataset["io_vocab"],
    )

    c1 = dataset["capabilities"]["C1_CreateOrder_API"]
    c2 = dataset["capabilities"]["C2_MakePayment"]
    c3 = dataset["capabilities"]["C3_CancelCart"]

    # 1. Evaluate directional compatibility
    comp_12 = space.compatibility(c1, c2)  # C1 -> C2
    comp_13 = space.compatibility(c1, c3)  # C1 -> C3
    comp_21 = space.compatibility(c2, c1)  # C2 -> C1 (Reverse order)
    comp_23 = space.compatibility(c2, c3)  # C2 -> C3

    # 2. Vector representations
    v1 = space.encode_capability(c1)
    v2 = space.encode_capability(c2)
    v3 = space.encode_capability(c3)

    # 3. Naive flat cosine similarity (to show why naive similarity fails for composability)
    def flat_cosine(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    naive_sim_12 = flat_cosine(v1, v2)
    naive_sim_13 = flat_cosine(v1, v3)

    results = {
        "C1_name": c1.name,
        "C2_name": c2.name,
        "C3_name": c3.name,
        "pair_C1_C2": comp_12,
        "pair_C1_C3": comp_13,
        "pair_C2_C1": comp_21,
        "pair_C2_C3": comp_23,
        "naive_similarity_C1_C2": round(naive_sim_12, 4),
        "naive_similarity_C1_C3": round(naive_sim_13, 4),
        "asymmetry_12_vs_21": round(abs(comp_12["compatibility_score"] - comp_21["compatibility_score"]), 4),
    }

    return results


if __name__ == "__main__":
    res = run_experiment_1()
    print("=" * 80)
    print("EXPERIMENT 1: CAPABILITY COMPATIBILITY & ASYMMETRY")
    print("=" * 80)
    print(f"C1: {res['C1_name']}")
    print(f"C2: {res['C2_name']}")
    print(f"C3: {res['C3_name']}\n")

    print(f"[*] C1 -> C2 (CreateOrder -> MakePayment):")
    print(f"    Compatibility Score : {res['pair_C1_C2']['compatibility_score']:+.4f}")
    print(f"    Precondition Match  : {res['pair_C1_C2']['precondition_match_score']:.4f}")
    print(f"    Conflict Penalty    : {res['pair_C1_C2']['conflict_penalty']:.4f}")
    print(f"    Is Compatible?      : {res['pair_C1_C2']['is_compatible']}")
    print(f"    Reasons             : {res['pair_C1_C2']['reasons']}\n")

    print(f"[*] C1 -> C3 (CreateOrder -> CancelCart):")
    print(f"    Compatibility Score : {res['pair_C1_C3']['compatibility_score']:+.4f}")
    print(f"    Conflict Penalty    : {res['pair_C1_C3']['conflict_penalty']:.4f}")
    print(f"    Is Compatible?      : {res['pair_C1_C3']['is_compatible']}")
    print(f"    Reasons             : {res['pair_C1_C3']['reasons']}\n")

    print(f"[*] Directional Asymmetry Check:")
    print(f"    Score(C1 -> C2) : {res['pair_C1_C2']['compatibility_score']:+.4f}")
    print(f"    Score(C2 -> C1) : {res['pair_C2_C1']['compatibility_score']:+.4f}")
    print(f"    Absolute Delta  : {res['asymmetry_12_vs_21']:.4f}  (Confirms directed asymmetric compatibility)\n")

    print(f"[*] Naive Undirected Cosine Similarity (Flat Vector Baseline):")
    print(f"    Cosine(C1, C2) : {res['naive_similarity_C1_C2']}")
    print(f"    Cosine(C1, C3) : {res['naive_similarity_C1_C3']}")
    print("    Critique: Naive flat similarity cannot detect precondition conflicts or asymmetric flow.")
    print("=" * 80)
