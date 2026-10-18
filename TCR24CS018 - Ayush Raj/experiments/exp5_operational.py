"""
Experiment 5: Operational Attributes and Multi-Objective Evaluation.
Investigates:
1. Additive log-reliability in vector space: -ln(Rel) across varying chain lengths
2. Multi-objective utility trade-offs (Latency vs. Cost vs. Reliability)
3. Resource requirement contention and conflict detection in vector space
"""

from __future__ import annotations
import math
import numpy as np
from typing import Dict, Any, List

from capembed.core import OperationalProfile
from capembed.pipeline import CapabilityEmbeddingSystem
from capembed.metrics import operational_utility
from datasets.ecommerce_domain import get_ecommerce_domain


def run_experiment_5() -> Dict[str, Any]:
    print("\n" + "="*70)
    print("EXPERIMENT 5: OPERATIONAL ATTRIBUTES & QUALITY OF SERVICE")
    print("="*70)

    ecom = get_ecommerce_domain()
    system = CapabilityEmbeddingSystem(ecom["schema"])

    c1_api = ecom["alternatives"][0]
    c1_db = ecom["alternatives"][1]
    c1_gui = ecom["alternatives"][2]

    alts = [c1_api, c1_db, c1_gui]
    enc_alts = [system.encode(c) for c in alts]

    print("\n1. Operational Profiles for Functionally Equivalent Alternatives:")
    print(f"  {'Capability':<18} | {'Latency (ms)':<14} | {'Cost ($)':<10} | {'Reliability':<12} | {'Availability':<12}")
    print("  " + "-"*72)
    for c in alts:
        op = c.operational_profile
        print(f"  {c.name:<18} | {op.execution_time_ms:>12.1f}ms | ${op.monetary_cost:>8.4f} | {op.reliability:>10.4f} | {op.availability:>10.2f}")

    # Multi-objective utility under different operational preference profiles
    preference_profiles = {
        "Balanced": {"w_rel": 0.35, "w_avail": 0.15, "w_time": 0.25, "w_cost": 0.25},
        "High-Reliability": {"w_rel": 0.60, "w_avail": 0.25, "w_time": 0.10, "w_cost": 0.05},
        "Low-Latency": {"w_rel": 0.20, "w_avail": 0.10, "w_time": 0.60, "w_cost": 0.10},
        "Low-Cost": {"w_rel": 0.20, "w_avail": 0.10, "w_time": 0.10, "w_cost": 0.60},
    }

    print("\n2. Operational Utility Ranking Under Diverse User Preferences:")
    for prof_name, weights in preference_profiles.items():
        print(f"\n  Preference Profile: {prof_name} (w_rel={weights['w_rel']}, w_time={weights['w_time']}, w_cost={weights['w_cost']})")
        scored = []
        for ec in enc_alts:
            u = operational_utility(
                ec,
                w_rel=weights["w_rel"],
                w_avail=weights["w_avail"],
                w_time=weights["w_time"],
                w_cost=weights["w_cost"],
            )
            scored.append((ec.name, u))
        scored.sort(key=lambda x: x[1], reverse=True)
        for rank, (name, u) in enumerate(scored, 1):
            print(f"    Rank {rank}: {name:<18} -> Utility: {u:.4f}")

    # Reliability Decay vs. Additive Log-Reliability in Vector Space
    print("\n3. Additive Log-Reliability Preservation Under Chaining:")
    c1 = ecom["c1"]
    c2 = ecom["c2"]
    c4 = ecom["c4"]
    c5 = ecom["c5"]

    chain = [c1, c2, c4, c5]
    enc_chain = [system.encode(c) for c in chain]

    print(f"  {'Chain Length':<14} | {'Product Rel':<14} | {'Vector -ln(Rel)':<18} | {'Theoretical -ln(Rel)':<22} | {'Diff':<10}")
    print("  " + "-"*82)

    accum_rel = 1.0
    accum_vec = None

    chain_lengths = []
    product_rels = []
    vector_log_rels = []

    for k in range(1, len(chain) + 1):
        sub_chain = enc_chain[:k]
        comp = system.compose(sub_chain)
        
        prod_rel = 1.0
        for c in chain[:k]:
            prod_rel *= c.operational_profile.reliability

        v_log_rel = comp.v_ops[5]
        expected_log_rel = -math.log(prod_rel)
        diff = abs(v_log_rel - expected_log_rel)

        chain_lengths.append(k)
        product_rels.append(prod_rel)
        vector_log_rels.append(v_log_rel)

        print(f"  {k:<14} | {prod_rel:<14.5f} | {v_log_rel:<18.6f} | {expected_log_rel:<22.6f} | {diff:<10.2e}")

    # Resource Contention Detection
    print("\n4. Resource Contention Detection in Resource Subspace:")
    c_pay = ecom["c2"]   # Requires PaymentGateway, Network
    c_notify = ecom["c5"] # Requires ExternalEmailService, Network
    c_db = ecom["alternatives"][1] # Requires Database

    enc_pay = system.encode(c_pay)
    enc_notify = system.encode(c_notify)
    enc_db = system.encode(c_db)

    # Dot product in resource subspace indicates shared/contended resources
    res_overlap_pay_notify = np.dot(enc_pay.v_res, enc_notify.v_res)
    res_overlap_pay_db = np.dot(enc_pay.v_res, enc_db.v_res)

    print(f"  - Contention between {c_pay.name} & {c_notify.name}: shared resources = {int(res_overlap_pay_notify)} (Network)")
    print(f"  - Contention between {c_pay.name} & {c_db.name}: shared resources = {int(res_overlap_pay_db)} (Independent)")

    return {
        "profiles": preference_profiles,
        "chain_lengths": chain_lengths,
        "product_rels": product_rels,
        "vector_log_rels": vector_log_rels,
        "res_overlap_pay_notify": res_overlap_pay_notify,
        "res_overlap_pay_db": res_overlap_pay_db,
    }


if __name__ == "__main__":
    run_experiment_5()
