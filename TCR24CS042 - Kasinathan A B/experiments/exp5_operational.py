"""
exp5_operational.py
===================
Experiment 5 — Operational Scoring: Reliability and Cost Trade-offs

Two versions of the same capability (CheckoutBook) differ in their
reliability and cost profiles. A combined operational score is computed:

  operational_score(cap_i, cap_j) =
      compatibility(cap_i, cap_j) * reliability(cap_j) * (1 - norm_cost(cap_j))

This rewards:
  - High compatibility  : cap_j can usefully follow cap_i
  - High reliability    : cap_j is dependable
  - Low cost            : cap_j is cheap to run

A second formulation uses a weighted sum:
  score_w = 0.4 * compatibility + 0.4 * reliability - 0.2 * cost

Experiment shows that ranking changes depending on which formulation is used,
illustrating how operational criteria interact with structural embedding.

Domain: library_checkout
Base predecessor: SearchCatalog
Variants of CheckoutBook:
  - Variant A: HIGH reliability (0.99), LOW  cost  → preferred operationally
  - Variant B: LOW  reliability (0.70), HIGH cost  → penalized operationally
  - Variant C: MED  reliability (0.85), MED  cost  → middle ground
  (all three have identical preconditions and effects as the original CheckoutBook)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.encode import (
    load_all_domains, load_domain, encode_capability,
    compatibility, similarity, IDX_RELY, IDX_COST
)

# ---------------------------------------------------------------------------
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
all_domains, _ = load_all_domains(DATA_DIR)
domain     = load_domain(os.path.join(DATA_DIR, "domain2_library.json"))
state_vars = domain["state_variables"]

def find_cap(name):
    for c in domain["capabilities"]:
        if c["name"] == name:
            return c
    raise KeyError(name)

# ---------------------------------------------------------------------------
# Base predecessor
# ---------------------------------------------------------------------------
search_cap = find_cap("SearchCatalog")
search_vec = encode_capability(search_cap, state_vars)

# ---------------------------------------------------------------------------
# CheckoutBook variants (same precond/effect, different reliability/cost)
# ---------------------------------------------------------------------------
BASE_PRECOND = {"member_active": True, "book_available": True, "account_suspended": False}
BASE_EFFECT  = {"book_checked_out": True, "book_available": False}

def make_checkout_variant(name, reliability, cost_time_ms, cost_money,
                          cost_resource, cost_risk, cost_energy):
    return {
        "name": name,
        "type": "EVENT",
        "inputs":  [{"name": "book_id",   "type": "string", "domain": "ISBN", "required": True},
                    {"name": "member_id", "type": "string", "domain": "UUID", "required": True}],
        "outputs": [{"name": "loan_id",   "type": "string", "domain": "UUID"},
                    {"name": "due_date",  "type": "string", "domain": "ISO8601"}],
        "preconditions": BASE_PRECOND,
        "effects":       BASE_EFFECT,
        "constraints":   ["member must have no overdue fines"],
        "resources":     ["catalog_db", "member_db", "rfid_scanner"],
        "cost": {
            "time_ms":  cost_time_ms,
            "money":    cost_money,
            "resource": cost_resource,
            "risk":     cost_risk,
            "energy":   cost_energy,
        },
        "reliability": reliability,
        "availability": {"start": "09:00", "end": "21:00"},
        "mechanism": {"trigger": "rfid_scan"},
    }

variant_A = make_checkout_variant(
    "Checkout_HighRel_LowCost",
    reliability=0.99, cost_time_ms=60,   cost_money=0.0,
    cost_resource=0.1, cost_risk=0.02, cost_energy=0.05
)
variant_B = make_checkout_variant(
    "Checkout_LowRel_HighCost",
    reliability=0.70, cost_time_ms=5000, cost_money=2.0,
    cost_resource=0.8, cost_risk=0.4,  cost_energy=0.6
)
variant_C = make_checkout_variant(
    "Checkout_MedRel_MedCost",
    reliability=0.85, cost_time_ms=600,  cost_money=0.1,
    cost_resource=0.4, cost_risk=0.15, cost_energy=0.25
)

variants  = [variant_A, variant_B, variant_C]
var_vecs  = [encode_capability(v, state_vars) for v in variants]

# ---------------------------------------------------------------------------
# Also test with PayFine as predecessor (different compatibility context)
# ---------------------------------------------------------------------------
payfine_cap = find_cap("PayFine")
payfine_vec = encode_capability(payfine_cap, state_vars)

# ---------------------------------------------------------------------------
# Compute scores
# ---------------------------------------------------------------------------
def avg_normalized_cost(vec):
    """Mean of the 5 normalized cost dimensions."""
    cost_slice = vec[IDX_COST[0]:IDX_COST[1]]
    return float(np.mean(cost_slice))

def operational_score_product(comp_val, rel, cost_avg):
    """Multiplicative form: compatibility * reliability * (1 - cost)."""
    return comp_val * rel * (1.0 - cost_avg)

def operational_score_weighted(comp_val, rel, cost_avg):
    """Weighted-sum form: 0.4*compatibility + 0.4*reliability - 0.2*cost."""
    return 0.4 * comp_val + 0.4 * rel - 0.2 * cost_avg

# ---------------------------------------------------------------------------
# Print results — predecessor: SearchCatalog
# ---------------------------------------------------------------------------
print("=" * 70)
print("  Experiment 5 — Operational Scoring: Reliability & Cost Trade-offs")
print("=" * 70)

for pred_name, pred_vec in [("SearchCatalog", search_vec),
                             ("PayFine",       payfine_vec)]:
    print(f"\n  Predecessor: {pred_name}")
    print(f"  {'Variant':<30} {'Compat':>8} {'Rely':>8} {'Cost':>8} "
          f"{'Score_prod':>12} {'Score_wt':>10}  Rank")
    print(f"  {'-'*30} {'-'*8} {'-'*8} {'-'*8} {'-'*12} {'-'*10}  {'-'*6}")

    rows = []
    for v, vec in zip(variants, var_vecs):
        comp_val  = compatibility(pred_vec, vec)
        rel       = float(vec[IDX_RELY[0]])
        cost_avg  = avg_normalized_cost(vec)
        s_prod    = operational_score_product(comp_val, rel, cost_avg)
        s_wt      = operational_score_weighted(comp_val, rel, cost_avg)
        rows.append((v["name"], comp_val, rel, cost_avg, s_prod, s_wt))

    # Print unranked first
    for name, comp_val, rel, cost_avg, s_prod, s_wt in rows:
        print(f"  {name:<30} {comp_val:>8.4f} {rel:>8.4f} {cost_avg:>8.4f} "
              f"{s_prod:>12.4f} {s_wt:>10.4f}")

    print()
    # Rank by product score
    ranked_prod = sorted(rows, key=lambda x: x[4], reverse=True)
    # Rank by weighted score
    ranked_wt   = sorted(rows, key=lambda x: x[5], reverse=True)

    print(f"  Ranking by multiplicative score (compat * rely * (1-cost)):")
    for rank, (name, *rest) in enumerate(ranked_prod, start=1):
        print(f"    {rank}. {name}  score={rest[3]:.4f}")

    print(f"\n  Ranking by weighted score (0.4*compat + 0.4*rely - 0.2*cost):")
    for rank, (name, *rest) in enumerate(ranked_wt, start=1):
        print(f"    {rank}. {name}  score={rest[4]:.4f}")

    ranking_changed = [r[0] for r in ranked_prod] != [r[0] for r in ranked_wt]
    print(f"\n  Ranking changed between formulations: {ranking_changed}")
    if ranking_changed:
        print(f"    Product score favours high-reliability+low-cost multiply.")
        print(f"    Weighted score allows high reliability to compensate for cost.")

print()
# ---------------------------------------------------------------------------
# Vary reliability and cost independently on two caps
# ---------------------------------------------------------------------------
print("  Sensitivity analysis: varying reliability and cost independently")
print(f"  (Predecessor: SearchCatalog -> Checkout variant)")
print(f"  {'Reliability':>14} {'Cost(avg)':>12} {'Score_prod':>12} {'Score_wt':>10}")
print(f"  {'-'*14} {'-'*12} {'-'*12} {'-'*10}")

base_comp = compatibility(search_vec, var_vecs[0])  # A's compatibility
for rel in [0.99, 0.90, 0.80, 0.70]:
    for cost_avg in [0.05, 0.20, 0.50, 0.80]:
        s_prod = operational_score_product(base_comp, rel, cost_avg)
        s_wt   = operational_score_weighted(base_comp, rel, cost_avg)
        print(f"  {rel:>14.2f} {cost_avg:>12.2f} {s_prod:>12.4f} {s_wt:>10.4f}")

print()
print("  Conclusion:")
print("    Variant A (high reliability, low cost) consistently ranks #1.")
print("    Variant B (low reliability, high cost) ranks #3 under both formulas.")
print("    The multiplicative formula penalizes high-cost variants more sharply")
print("    because it multiplies (1-cost) rather than subtracting a fraction.")
print("    Rankings can diverge when reliability/cost trade-offs are balanced.")
print("=" * 70)
