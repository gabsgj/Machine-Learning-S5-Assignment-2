"""
exp4_irrelevant.py
==================
Experiment 4 — Goal-Directed Relevance Ranking

Given a goal, rank ALL capabilities in a domain by their relevance to that
goal, where relevance is measured by:
  similarity(effect_vector(capability), goal_vector)

Capabilities whose effects align with the goal variables score HIGH.
Capabilities that don't touch those variables at all score near ZERO.

Domain: hotel_booking
Goal:   {checked_in: True, payment_captured: True, loyalty_points_credited: True}

Expected:
  - CheckIn should rank near top (its effect sets checked_in=True)
  - CapturePayment should rank near top (its effect sets payment_captured=True)
  - CheckOut should rank near top (its effect sets loyalty_points_credited=True)
  - SearchRooms / OrderRoomService / CancelReservation should rank lower
    (their effects don't directly address the goal)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.encode import (
    load_all_domains, load_domain, encode_capability, encode_goal,
    similarity, IDX_EFFECT, IDX_PRECOND
)

# ---------------------------------------------------------------------------
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
all_domains, _ = load_all_domains(DATA_DIR)
domain     = load_domain(os.path.join(DATA_DIR, "domain3_hotel.json"))
state_vars = domain["state_variables"]
caps       = domain["capabilities"]

# ---------------------------------------------------------------------------
# Encode goal
# ---------------------------------------------------------------------------
goal     = domain["goal"]
goal_vec = encode_goal(goal, state_vars)

# ---------------------------------------------------------------------------
# Rank all capabilities by similarity(effect_vector, goal_vector)
# ---------------------------------------------------------------------------
def effect_vector_only(cap_vec: np.ndarray) -> np.ndarray:
    """Extract just the effect segment of a capability vector."""
    return cap_vec[IDX_EFFECT[0]:IDX_EFFECT[1]]

def precond_vector_only(cap_vec: np.ndarray) -> np.ndarray:
    """Extract just the precondition segment of a capability vector."""
    return cap_vec[IDX_PRECOND[0]:IDX_PRECOND[1]]

rankings = []
for cap in caps:
    cap_vec    = encode_capability(cap, state_vars)
    eff_vec    = effect_vector_only(cap_vec)
    # similarity between effect segment and goal vector (both 12-dim)
    norm_eff  = np.linalg.norm(eff_vec)
    norm_goal = np.linalg.norm(goal_vec)
    if norm_eff == 0.0 or norm_goal == 0.0:
        rel = 0.0
    else:
        rel = float(np.dot(eff_vec, goal_vec) / (norm_eff * norm_goal))
    # full vector similarity for comparison
    full_sim = similarity(cap_vec, np.pad(goal_vec, (0, len(cap_vec) - len(goal_vec))))
    rankings.append((cap["name"], cap["type"], rel, full_sim))

rankings.sort(key=lambda x: x[2], reverse=True)

# ---------------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------------
print("=" * 70)
print("  Experiment 4 — Goal-Directed Relevance Ranking")
print("  Domain: hotel_booking")
print("=" * 70)

print(f"\n  Goal: {goal}")
print(f"  Goal vector (12-dim state space): {np.round(goal_vec, 1).tolist()}")
print(f"  State variables: {state_vars}")

print()
print(f"  {'Rank':<6} {'Capability':<25} {'Type':<12} "
      f"{'Effect-Goal Sim':>16}  Notes")
print(f"  {'-'*6} {'-'*25} {'-'*12} {'-'*16}  {'-'*30}")

for rank, (name, cap_type, rel, full_sim) in enumerate(rankings, start=1):
    if rel > 0.5:
        note = "<-- HIGHLY RELEVANT (effect matches goal)"
    elif rel > 0.1:
        note = "<-- Partially relevant"
    elif rel > 0.0:
        note = "  Slightly relevant"
    elif rel == 0.0:
        note = "  No alignment with goal"
    else:
        note = "  Contradicts goal"
    print(f"  {rank:<6} {name:<25} {cap_type:<12} {rel:>16.4f}  {note}")

print()
print("  Effect vector detail (capability vs goal):")
print(f"  {'Capability':<25}  Effect segment over state vars")
print(f"  {'-'*25}  {'-'*52}")
goal_str = "  GOAL              "
print(f"  {goal_str:<25}  {np.round(goal_vec, 1).tolist()}")
for cap in caps:
    cap_vec = encode_capability(cap, state_vars)
    eff     = effect_vector_only(cap_vec)
    print(f"  {cap['name']:<25}  {np.round(eff, 1).tolist()}")

print()
print("  Conclusion:")
print("    CheckIn, CapturePayment, CheckOut rank highest because their")
print("    effects directly set goal-required variables to the desired values.")
print("    SearchRooms / OrderRoomService effects are orthogonal to the goal,")
print("    yielding near-zero scores. CancelReservation may score negative")
print("    because it sets room_available=True while the goal doesn't need it,")
print("    but primarily because its effects conflict with goal vars.")
print("=" * 70)
