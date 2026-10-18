"""
exp3_alt_implementations.py
============================
Experiment 3 — Alternative Implementations of the Same Capability

Three capability variants implement the *same logical operation*
(mark a payment as complete) but through different mechanisms:
  - PAY_API      : type=API    (e.g. REST call to payment gateway)
  - PAY_DATABASE : type=DATABASE (e.g. direct DB update in a monolith)
  - PAY_GUI      : type=GUI    (e.g. clerk enters via admin interface)

Expected behaviour:
  - All three have IDENTICAL preconditions and effects → precond/effect
    segments of their vectors are the same.
  - They differ in type one-hot, resource multi-hot, and cost/reliability.
  - similarity() should be HIGH between all three (close but not 1.0),
    because the structural differences in type/cost/resources pull the
    vectors slightly apart.
  - compatibility() scores should also be similar across variants when
    used as predecessors of the same successor (effect is the same).

This experiment demonstrates that similarity() measures representational
closeness, not just effect identity.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.encode import (
    load_all_domains, load_domain, encode_capability,
    similarity, compatibility,
    IDX_TYPE, IDX_RESOURCE, IDX_COST, IDX_RELY,
    IDX_PRECOND, IDX_EFFECT,
    CAPABILITY_TYPES, GLOBAL_RESOURCE_VOCAB
)

# ---------------------------------------------------------------------------
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
all_domains, _ = load_all_domains(DATA_DIR)
domain     = load_domain(os.path.join(DATA_DIR, "domain1_orders.json"))
state_vars = domain["state_variables"]

# ---------------------------------------------------------------------------
# Build three variants with identical preconditions/effects but different
# type, resources, and cost profiles.
# ---------------------------------------------------------------------------

BASE_PRECOND  = {"order_created": True, "payment_pending": True}
BASE_EFFECTS  = {"payment_complete": True, "payment_pending": False,
                 "inventory_reserved": True}

PAY_API = {
    "name": "MakePayment_API",
    "type": "API",
    "inputs":  [{"name": "order_id",        "type": "string", "domain": "UUID",   "required": True},
                {"name": "payment_method",  "type": "string", "domain": "enum",   "required": True},
                {"name": "amount",          "type": "float",  "domain": "pos_real","required": True}],
    "outputs": [{"name": "transaction_id",  "type": "string", "domain": "UUID"},
                {"name": "receipt_url",     "type": "string", "domain": "URL"}],
    "preconditions": BASE_PRECOND,
    "effects":       BASE_EFFECTS,
    "constraints":   ["order must exist", "amount must be positive"],
    "resources":     ["payment_gateway", "database"],
    "cost":    {"time_ms": 800, "money": 0.25, "resource": 0.4, "risk": 0.15, "energy": 0.2},
    "reliability": 0.95,
    "availability": True,
    "mechanism": {"endpoint": "/api/payments", "method": "POST", "provider": "stripe"},
}

PAY_DATABASE = {
    "name": "MakePayment_DB",
    "type": "DATABASE",
    "inputs":  [{"name": "order_id",    "type": "string", "domain": "UUID",    "required": True},
                {"name": "amount",      "type": "float",  "domain": "pos_real","required": True}],
    "outputs": [{"name": "record_id",   "type": "string", "domain": "UUID"}],
    "preconditions": BASE_PRECOND,
    "effects":       BASE_EFFECTS,
    "constraints":   ["requires direct DB access", "used in legacy systems"],
    "resources":     ["database"],
    "cost":    {"time_ms": 120, "money": 0.005, "resource": 0.15, "risk": 0.2, "energy": 0.08},
    "reliability": 0.93,
    "availability": True,
    "mechanism": {"table": "payments", "operation": "INSERT", "connection_pool": "pgbouncer"},
}

PAY_GUI = {
    "name": "MakePayment_GUI",
    "type": "GUI",
    "inputs":  [{"name": "order_id",    "type": "string", "domain": "UUID",    "required": True},
                {"name": "amount",      "type": "float",  "domain": "pos_real","required": True},
                {"name": "clerk_id",    "type": "string", "domain": "UUID",    "required": True}],
    "outputs": [{"name": "receipt_num", "type": "string", "domain": "alphanumeric"}],
    "preconditions": BASE_PRECOND,
    "effects":       BASE_EFFECTS,
    "constraints":   ["clerk must be authenticated", "used in physical POS terminals"],
    "resources":     ["database", "payment_gateway"],
    "cost":    {"time_ms": 3000, "money": 0.0, "resource": 0.6, "risk": 0.25, "energy": 0.35},
    "reliability": 0.88,
    "availability": {"start": "09:00", "end": "17:00"},
    "mechanism": {"ui": "admin_dashboard", "framework": "React", "endpoint": "/admin/payments"},
}

# ---------------------------------------------------------------------------
# A successor capability to test compatibility with all variants
# ---------------------------------------------------------------------------
SHIP_CAP = {
    "name": "ShipOrder",
    "type": "SERVICE",
    "inputs":  [{"name": "order_id", "type": "string", "domain": "UUID",         "required": True},
                {"name": "address",  "type": "dict",   "domain": "shipping_addr", "required": True}],
    "outputs": [{"name": "tracking_number", "type": "string", "domain": "tracking_code"}],
    "preconditions": {"payment_complete": True, "inventory_reserved": True},
    "effects":       {"order_shipped": True},
    "constraints":   [],
    "resources":     ["shipping_api", "database"],
    "cost":    {"time_ms": 1500, "money": 5.0, "resource": 0.5, "risk": 0.2, "energy": 0.3},
    "reliability": 0.92,
    "availability": True,
    "mechanism": {},
}

variants  = [PAY_API, PAY_DATABASE, PAY_GUI]
var_names = [v["name"] for v in variants]
var_vecs  = [encode_capability(v, state_vars) for v in variants]
ship_vec  = encode_capability(SHIP_CAP, state_vars)

# ---------------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------------
print("=" * 70)
print("  Experiment 3 — Alternative Implementations of the Same Capability")
print("  Operation: 'complete a payment' (same precond/effect, diff mechanism)")
print("=" * 70)

print("\n  Variant properties:")
print(f"  {'Variant':<22} {'Type':<12} {'Resources':<32} {'Reliability':>12} {'Cost[time]':>11}")
print(f"  {'-'*22} {'-'*12} {'-'*32} {'-'*12} {'-'*11}")
for v, vec in zip(variants, var_vecs):
    res_slice = vec[IDX_RESOURCE[0]:IDX_RESOURCE[1]]
    active_res = [GLOBAL_RESOURCE_VOCAB[i] for i,r in enumerate(res_slice) if r > 0.5]
    res_str = ",".join(active_res)[:30]
    print(f"  {v['name']:<22} {v['type']:<12} {res_str:<32} "
          f"{vec[IDX_RELY[0]]:>12.4f} {vec[IDX_COST[0]]:>11.4f}")

print()
print("  Precondition and Effect vectors (should be IDENTICAL across variants):")
print(f"  state_vars: {state_vars}")
for v, vec in zip(variants, var_vecs):
    pre = vec[IDX_PRECOND[0]:IDX_PRECOND[1]]
    eff = vec[IDX_EFFECT[0]:IDX_EFFECT[1]]
    print(f"  {v['name']:<22}  precond={np.round(pre,1).tolist()}  effect={np.round(eff,1).tolist()}")

print()
print("  Pairwise Similarity (should be HIGH but NOT 1.0):")
print(f"  {'Pair':<45} {'Similarity':>12}")
print(f"  {'-'*45} {'-'*12}")
for i in range(len(variants)):
    for j in range(i+1, len(variants)):
        sim = similarity(var_vecs[i], var_vecs[j])
        note = " <- NOT 1.0 (type/cost/resource differ)" if sim < 1.0 else " <- EXACT MATCH"
        print(f"  {var_names[i]+' <-> '+var_names[j]:<45} {sim:>12.4f}{note}")

print()
print("  Compatibility with ShipOrder (should be SIMILAR across variants):")
print(f"  {'Variant':<22} {'comp->ShipOrder':>16} {'sim(v,Ship)':>12}")
print(f"  {'-'*22} {'-'*16} {'-'*12}")
for v, vec in zip(variants, var_vecs):
    comp_val = compatibility(vec, ship_vec)
    sim_val  = similarity(vec, ship_vec)
    print(f"  {v['name']:<22} {comp_val:>16.4f} {sim_val:>12.4f}")

print()
print("  Key insight:")
print("    All three share identical precondition/effect vectors.")
print("    Cosine similarity is HIGH because the state-transition segments")
print("    (largest contribution) match perfectly.  The non-unity gap comes")
print("    from type one-hot, resources, and cost/reliability differences.")
print("    Compatibility with ShipOrder is IDENTICAL for all variants since")
print("    compatibility() depends only on the effect/precondition segments.")
print("=" * 70)
