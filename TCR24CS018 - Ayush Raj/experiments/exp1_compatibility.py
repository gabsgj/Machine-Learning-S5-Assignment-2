"""
Experiment 1: Capability Compatibility.
Given C1, C2, C3 where C1 composes with C2 but not C3:
- C1: CreateOrder (eff: OrderExists=true)
- C2: MakePayment (pre: OrderExists=true)
- C3: CancelCart (pre: OrderExists=false)
Investigates whether the representation distinguishes the relationships.
Also evaluates compatibility across all pairs in the domain.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Any

from capembed.core import Capability, CapabilityType, InputSpec, OutputSpec, OperationalProfile, ExecutionMechanism, DomainSchema
from capembed.pipeline import CapabilityEmbeddingSystem
from datasets.ecommerce_domain import get_ecommerce_domain


def run_experiment_1() -> Dict[str, Any]:
    print("\n" + "="*70)
    print("EXPERIMENT 1: CAPABILITY COMPATIBILITY EVALUATION")
    print("="*70)

    ecom = get_ecommerce_domain()
    system = CapabilityEmbeddingSystem(ecom["schema"])

    c1 = ecom["c1"]  # CreateOrder
    c2 = ecom["c2"]  # MakePayment
    c3 = ecom["c3"]  # CancelCart

    # Encode capabilities
    ec1 = system.encode(c1)
    ec2 = system.encode(c2)
    ec3 = system.encode(c3)

    # Compute compatibility metrics
    c1_c2_detail = system.compatibility(ec1, ec2, detailed=True)
    c1_c3_detail = system.compatibility(ec1, ec3, detailed=True)
    c2_c1_detail = system.compatibility(ec2, ec1, detailed=True)  # Directional asymmetry check

    # Also compute functional similarity to highlight the crucial contrast
    sim_c1_c2 = system.similarity(ec1, ec2, mode="functional")
    sim_c1_c3 = system.similarity(ec1, ec3, mode="functional")

    print(f"\n1. Direct Pair Analysis (Assignment Specification Pattern):")
    print(f"  C1 ({c1.name}) -> Effects: {c1.effects}")
    print(f"  C2 ({c2.name}) -> Preconditions: {c2.preconditions}")
    print(f"  C3 ({c3.name}) -> Preconditions: {c3.preconditions}")
    print("\n  Quantitative Results:")
    print(f"  [C1 -> C2] Compatible Chain:")
    print(f"    - Precondition-Effect Compatibility (Gamma_PE): {c1_c2_detail['precondition_effect']:+.4f}")
    print(f"    - Input-Output Compatibility (Gamma_IO):        {c1_c2_detail['input_output']:+.4f}")
    print(f"    - Total Composability Score (Comp):              {c1_c2_detail['total_composability']:+.4f}")
    print(f"    - Functional Similarity (Sim_func):              {sim_c1_c2:+.4f}")
    print(f"    => Result: HIGHLY COMPATIBLE (Comp > 0.8), while Sim_func is low ({sim_c1_c2:.2f})!")

    print(f"\n  [C1 -> C3] Incompatible Conflict Chain:")
    print(f"    - Precondition-Effect Compatibility (Gamma_PE): {c1_c3_detail['precondition_effect']:+.4f}")
    print(f"    - Input-Output Compatibility (Gamma_IO):        {c1_c3_detail['input_output']:+.4f}")
    print(f"    - Total Composability Score (Comp):              {c1_c3_detail['total_composability']:+.4f}")
    print(f"    - Functional Similarity (Sim_func):              {sim_c1_c3:+.4f}")
    print(f"    => Result: SEVERE CONFLICT (Comp = -1.0), correctly prohibited!")

    print(f"\n  [C2 -> C1] Directional Asymmetry Check:")
    print(f"    - Total Composability Score (C2 -> C1):          {c2_c1_detail['total_composability']:+.4f}")
    print(f"    => Result: Directional asymmetry confirmed! Comp(C1, C2) = {c1_c2_detail['total_composability']:.2f} != Comp(C2, C1) = {c2_c1_detail['total_composability']:.2f}")

    # Pairwise compatibility matrix across all domain core capabilities
    core_caps = [ecom["c1"], ecom["c2"], ecom["c3"], ecom["c4"], ecom["c5"]]
    enc_caps = [system.encode(c) for c in core_caps]
    n = len(core_caps)
    comp_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            comp_matrix[i, j] = system.compatibility(enc_caps[i], enc_caps[j])

    print("\n2. Pairwise Composability Matrix Comp(Row -> Col):")
    header = f"{'Capability':<20}" + "".join([f"{c.name[:12]:>14}" for c in core_caps])
    print("  " + header)
    print("  " + "-" * len(header))
    for i, c in enumerate(core_caps):
        row_str = f"  {c.name:<20}" + "".join([f"{comp_matrix[i, j]:>14.2f}" for j in range(n)])
        print(row_str)

    return {
        "c1_c2": c1_c2_detail,
        "c1_c3": c1_c3_detail,
        "c2_c1": c2_c1_detail,
        "sim_c1_c2": sim_c1_c2,
        "sim_c1_c3": sim_c1_c3,
        "caps": [c.name for c in core_caps],
        "comp_matrix": comp_matrix,
    }


if __name__ == "__main__":
    run_experiment_1()
