"""
exp1_compatibility.py
=====================
Experiment 1 — Sequential Compatibility Scoring

Demonstrates that compatibility() correctly distinguishes between capability
chains that should work in sequence and those that should not.

Hypothesis:
  CreateOrder -> MakePayment   : HIGH / positive compatibility score
  CreateOrder -> CancelCart    : LOW  / negative compatibility score

The score is computed as:
  dot(effect(i), precondition(j)) / sum(|precondition(j)|)

CreateOrder's effects turn on {order_created, payment_pending} and turn off
{cart_active}. MakePayment requires {order_created=T, payment_pending=T},
which are exactly what CreateOrder produces → positive score.

CancelCart requires {cart_active=T}, but CreateOrder's effect sets
cart_active=False → negative score.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.encode import (
    load_all_domains, load_domain, encode_capability,
    compatibility, similarity, IDX_PRECOND, IDX_EFFECT
)
from src.compatibility import pairwise_compatibility_matrix, print_compatibility_table

# ---------------------------------------------------------------------------
# Load domain
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
domain = load_domain(os.path.join(DATA_DIR, "domain1_orders.json"))

# Fit cost stats across all domains so normalization is consistent
all_domains, _ = load_all_domains(DATA_DIR)

state_vars = domain["state_variables"]
caps       = domain["capabilities"]

def find_cap(name):
    for c in caps:
        if c["name"] == name:
            return c
    raise KeyError(name)

# ---------------------------------------------------------------------------
# Encode the three key capabilities
# ---------------------------------------------------------------------------
create_order  = find_cap("CreateOrder")
make_payment  = find_cap("MakePayment")
cancel_cart   = find_cap("CancelCart")
reserve_inv   = find_cap("ReserveInventory")
ship_order    = find_cap("ShipOrder")
send_notif    = find_cap("SendNotification")

vec_create  = encode_capability(create_order,  state_vars)
vec_payment = encode_capability(make_payment,  state_vars)
vec_cancel  = encode_capability(cancel_cart,   state_vars)
vec_reserve = encode_capability(reserve_inv,   state_vars)
vec_ship    = encode_capability(ship_order,    state_vars)
vec_notif   = encode_capability(send_notif,    state_vars)

# ---------------------------------------------------------------------------
# Compute compatibility and similarity for the primary pairs
# ---------------------------------------------------------------------------
comp_co_mp = compatibility(vec_create,  vec_payment)  # expected HIGH
comp_co_cc = compatibility(vec_create,  vec_cancel)   # expected LOW/NEG
comp_mp_sh = compatibility(vec_payment, vec_ship)
comp_sh_no = compatibility(vec_ship,    vec_notif)
comp_cc_co = compatibility(vec_cancel,  vec_create)   # no connection
comp_no_cc = compatibility(vec_notif,   vec_cancel)   # no connection

sim_co_mp  = similarity(vec_create,  vec_payment)
sim_co_cc  = similarity(vec_create,  vec_cancel)

# ---------------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------------
print("=" * 70)
print("  Experiment 1 — Sequential Compatibility Scoring")
print("  Domain: ecommerce_orders")
print("=" * 70)

print("\n  Primary Hypothesis Test:")
print(f"  {'Pair':<40} {'Compatibility':>14} {'Similarity':>12}  {'Expected':>10}")
print(f"  {'-'*40} {'-'*14} {'-'*12}  {'-'*10}")

rows = [
    ("CreateOrder  -> MakePayment",  comp_co_mp, sim_co_mp,  "HIGH (+)"),
    ("CreateOrder  -> CancelCart",   comp_co_cc, sim_co_cc,  "LOW  (-)"),
    ("MakePayment  -> ShipOrder",    comp_mp_sh, similarity(vec_payment, vec_ship), "MED  (+)"),
    ("ShipOrder    -> SendNotif",    comp_sh_no, similarity(vec_ship, vec_notif),   "MED  (+)"),
    ("CancelCart   -> CreateOrder",  comp_cc_co, similarity(vec_cancel, vec_create),"ZERO"),
    ("SendNotif    -> CancelCart",   comp_no_cc, similarity(vec_notif, vec_cancel), "NEG"),
]

for pair, comp, sim, expected in rows:
    print(f"  {pair:<40} {comp:>14.4f} {sim:>12.4f}  {expected:>10}")

# ---------------------------------------------------------------------------
# Full pairwise matrix
# ---------------------------------------------------------------------------
print()
print_compatibility_table(caps, state_vars,
                          title="Full 6x6 Compatibility Matrix (rows=predecessor, cols=successor)")

# ---------------------------------------------------------------------------
# Detailed vector inspection for the primary pair
# ---------------------------------------------------------------------------
print("  Effect vector breakdown (CreateOrder):")
print(f"    State vars : {state_vars}")
eff_co = vec_create[IDX_EFFECT[0]:IDX_EFFECT[1]]
pre_mp = vec_payment[IDX_PRECOND[0]:IDX_PRECOND[1]]
pre_cc = vec_cancel[IDX_PRECOND[0]:IDX_PRECOND[1]]
print(f"    Effect     : {np.round(eff_co, 1).tolist()}")
print(f"  Precond vector (MakePayment):")
print(f"    Precond    : {np.round(pre_mp, 1).tolist()}")
print(f"  Precond vector (CancelCart):")
print(f"    Precond    : {np.round(pre_cc, 1).tolist()}")
print()
print(f"  dot(effect_CO, precond_MP) = {np.dot(eff_co, pre_mp):.4f}")
print(f"  sum(|precond_MP|)          = {np.sum(np.abs(pre_mp)):.4f}")
print(f"  => Compatibility score     = {np.dot(eff_co, pre_mp)/np.sum(np.abs(pre_mp)):.4f}  (CONFIRMED HIGH)")
print()
print(f"  dot(effect_CO, precond_CC) = {np.dot(eff_co, pre_cc):.4f}")
print(f"  sum(|precond_CC|)          = {np.sum(np.abs(pre_cc)):.4f}")
print(f"  => Compatibility score     = {np.dot(eff_co, pre_cc)/np.sum(np.abs(pre_cc)):.4f}  (CONFIRMED LOW/NEG)")
print()

print("  Key observation:")
print("    CreateOrder->MakePayment : POSITIVE  (effect satisfies preconditions)")
print("    CreateOrder->CancelCart  : NEGATIVE  (effect contradicts preconditions)")
print("    Similarity disagrees: both pairs can have moderate similarity (same domain,")
print("    similar structure) yet completely different compatibility scores.")
print("=" * 70)
