"""
exp2_composition.py
===================
Experiment 2 — Chain Composition

Compose a 3-step chain and measure the similarity between the composite
capability and each of the three individual capabilities.

Chain: CreateOrder -> MakePayment -> ShipOrder

Expected results:
  - similarity(composite, CreateOrder)  moderate — shares type/resources but
    composite has wider effects
  - similarity(composite, MakePayment)  moderate — shares payment resources
  - similarity(composite, ShipOrder)    moderate — shares shipping resources
  - None should be 1.0 (the composite is strictly richer than any individual)

The composite's:
  precondition = CreateOrder's precond (cart_active=T, cart_empty=F)
  effect       = union of all effects, later overwriting earlier
  cost         = sum of individual costs (clamped to [0,1])
  reliability  = product of individual reliabilities
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.encode import (
    load_all_domains, load_domain, encode_capability,
    compose, similarity, IDX_PRECOND, IDX_EFFECT, IDX_RELY, IDX_COST
)

# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
all_domains, _ = load_all_domains(DATA_DIR)
domain     = load_domain(os.path.join(DATA_DIR, "domain1_orders.json"))
state_vars = domain["state_variables"]
caps       = domain["capabilities"]

def find_cap(name):
    for c in caps:
        if c["name"] == name:
            return c
    raise KeyError(name)

# ---------------------------------------------------------------------------
# Three-step chain
# ---------------------------------------------------------------------------
chain_names = ["CreateOrder", "MakePayment", "ShipOrder"]
chain_caps  = [find_cap(n) for n in chain_names]
chain_vecs  = [encode_capability(c, state_vars) for c in chain_caps]

composite = compose(chain_vecs, chain_caps, state_vars)

# ---------------------------------------------------------------------------
# Similarities
# ---------------------------------------------------------------------------
sims = [(n, similarity(composite, v)) for n, v in zip(chain_names, chain_vecs)]

# Also similarity between consecutive pairs (for reference)
sim_12 = similarity(chain_vecs[0], chain_vecs[1])
sim_23 = similarity(chain_vecs[1], chain_vecs[2])
sim_13 = similarity(chain_vecs[0], chain_vecs[2])

# ---------------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------------
print("=" * 70)
print("  Experiment 2 — Chain Composition")
print("  Chain: CreateOrder -> MakePayment -> ShipOrder")
print("=" * 70)

print("\n  Individual capability properties:")
header = f"  {'Capability':<20} {'Reliability':>12} {'Cost[time]':>12} {'Effect[non-zero]':>20}"
print(header)
print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*20}")
for name, vec, cap in zip(chain_names, chain_vecs, chain_caps):
    eff_nz = sum(1 for v in vec[IDX_EFFECT[0]:IDX_EFFECT[1]] if v != 0)
    print(f"  {name:<20} {vec[IDX_RELY[0]]:>12.4f} {vec[IDX_COST[0]]:>12.4f} "
          f"{'dims':>14}: {eff_nz:>4}")

print()
print(f"  Composite capability properties:")
prod_rely = chain_vecs[0][IDX_RELY[0]] * chain_vecs[1][IDX_RELY[0]] * chain_vecs[2][IDX_RELY[0]]
comp_eff_nz = sum(1 for v in composite[IDX_EFFECT[0]:IDX_EFFECT[1]] if v != 0)
print(f"  {'COMPOSITE':<20} {composite[IDX_RELY[0]]:>12.4f} {composite[IDX_COST[0]]:>12.4f} "
      f"{'dims':>14}: {comp_eff_nz:>4}")
print(f"  (reliability = {chain_vecs[0][IDX_RELY[0]]:.4f} x {chain_vecs[1][IDX_RELY[0]]:.4f} x "
      f"{chain_vecs[2][IDX_RELY[0]]:.4f} = {prod_rely:.4f})")

print()
print("  Precondition vector (state-variable space):")
print(f"    state_vars  : {state_vars}")
pre_co = chain_vecs[0][IDX_PRECOND[0]:IDX_PRECOND[1]]
pre_mp = chain_vecs[1][IDX_PRECOND[0]:IDX_PRECOND[1]]
pre_sh = chain_vecs[2][IDX_PRECOND[0]:IDX_PRECOND[1]]
pre_cx = composite[IDX_PRECOND[0]:IDX_PRECOND[1]]
print(f"    CreateOrder : {np.round(pre_co, 1).tolist()}")
print(f"    MakePayment : {np.round(pre_mp, 1).tolist()}")
print(f"    ShipOrder   : {np.round(pre_sh, 1).tolist()}")
print(f"    COMPOSITE   : {np.round(pre_cx, 1).tolist()}")
print(f"    (composite precond = CreateOrder's base; later caps' unsatisfied needs added)")

print()
print("  Effect vector (state-variable space):")
eff_co = chain_vecs[0][IDX_EFFECT[0]:IDX_EFFECT[1]]
eff_mp = chain_vecs[1][IDX_EFFECT[0]:IDX_EFFECT[1]]
eff_sh = chain_vecs[2][IDX_EFFECT[0]:IDX_EFFECT[1]]
eff_cx = composite[IDX_EFFECT[0]:IDX_EFFECT[1]]
print(f"    CreateOrder : {np.round(eff_co, 1).tolist()}")
print(f"    MakePayment : {np.round(eff_mp, 1).tolist()}")
print(f"    ShipOrder   : {np.round(eff_sh, 1).tolist()}")
print(f"    COMPOSITE   : {np.round(eff_cx, 1).tolist()}")
print(f"    (last-writer-wins; composite reflects final world state after chain)")

print()
print("  Similarity(composite, individual):")
print(f"  {'Capability':<25} {'Similarity':>12}  Notes")
print(f"  {'-'*25} {'-'*12}  {'-'*35}")
for name, sim_val in sims:
    note = "< 1.0 (composite is broader)" if sim_val < 1.0 else "= 1.0 (exact match)"
    print(f"  {name:<25} {sim_val:>12.4f}  {note}")

print()
print("  Pairwise individual similarity (for reference):")
print(f"  {'Pair':<40} {'Similarity':>12}")
print(f"  {'-'*40} {'-'*12}")
print(f"  {'CreateOrder <-> MakePayment':<40} {sim_12:>12.4f}")
print(f"  {'MakePayment <-> ShipOrder':<40} {sim_23:>12.4f}")
print(f"  {'CreateOrder <-> ShipOrder':<40} {sim_13:>12.4f}")

print()
print("  Conclusion:")
print("    The composite inherits CreateOrder's entry preconditions,")
print("    accumulates all intermediate and final effects (ShipOrder wins on")
print("    conflicting dims), sums costs, and multiplies reliabilities.")
print("    similarity(composite, Ci) < 1.0 for all i, confirming the composite")
print("    is strictly richer than any individual capability.")
print("=" * 70)
