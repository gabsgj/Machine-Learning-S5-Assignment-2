"""
Formal Metrics for Capability Evaluation:
- Precondition-Effect Compatibility (Gamma_PE)
- Input-Output Compatibility (Gamma_IO)
- Total Directional Composability (Comp)
- Functional Similarity vs. Implementation Similarity
- Goal Relevance
- Operational Utility and Multi-Objective Scoring
"""

from __future__ import annotations
import numpy as np
from typing import Tuple, Dict, Any, Optional

from .encoder import EncodedCapability, EncodedState, EncodedGoal


def cosine_similarity(v1: np.ndarray, v2: np.ndarray, eps: float = 1e-9) -> float:
    """Computes cosine similarity between two 1D vectors."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < eps or norm2 < eps:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def precondition_effect_compatibility(
    ec1: EncodedCapability,
    ec2: EncodedCapability,
    eps: float = 1e-9,
) -> float:
    """
    Evaluates precondition-effect compatibility for transition C1 -> C2.
    Gamma_PE in [-1.0, 1.0]:
    +1.0 : All specified preconditions of C2 are satisfied by C1's effects (or unviolated).
     0.0 : Neutral / no overlap between C1 effects and C2 preconditions.
    -1.0 : Direct contradiction (C1 produces an effect that violates a precondition of C2).
    """
    p2_mask = ec2.m_pre
    p2_vals = ec2.v_pre
    e1_mask = ec1.m_eff
    e1_vals = ec1.v_eff

    # Common variables: touched by C1's effect and required by C2's precondition
    overlap_mask = p2_mask * e1_mask
    overlap_count = np.sum(overlap_mask)

    if overlap_count == 0:
        # No direct interaction between C1 effects and C2 preconditions
        # If C2 has no preconditions at all, it is trivially compatible (+1.0)
        # If C2 has preconditions, they must come from state, so neutral (0.0)
        return 1.0 if np.sum(p2_mask) == 0 else 0.0

    # For overlapping variables:
    # Target alignment: e1_vals * p2_vals
    alignments = (e1_vals * p2_vals) * overlap_mask
    matches = np.sum(alignments > 0)
    conflicts = np.sum(alignments < 0)

    score = (matches - conflicts) / (overlap_count + eps)
    return float(np.clip(score, -1.0, 1.0))


def input_output_compatibility(
    ec1: EncodedCapability,
    ec2: EncodedCapability,
    eps: float = 1e-9,
) -> float:
    """
    Evaluates input-output dataflow compatibility for C1 -> C2.
    Gamma_IO in [0.0, 1.0]:
    Measures the fraction of C2's required inputs that are supplied by C1's outputs.
    """
    total_inputs_required = np.sum(ec2.v_in)
    if total_inputs_required < eps:
        # C2 requires no inputs -> trivially satisfied
        return 1.0

    # Satisfied inputs: min(ec1.v_out, ec2.v_in)
    satisfied = np.sum(np.minimum(ec1.v_out, ec2.v_in))
    return float(np.clip(satisfied / (total_inputs_required + eps), 0.0, 1.0))


def compatibility_score(
    ec1: EncodedCapability,
    ec2: EncodedCapability,
    w_pe: float = 0.6,
    w_io: float = 0.4,
) -> float:
    """
    Combined directional composability score Comp(C1, C2) in [-1.0, 1.0].
    Directional: Comp(C1, C2) != Comp(C2, C1).
    """
    pe = precondition_effect_compatibility(ec1, ec2)
    io = input_output_compatibility(ec1, ec2)
    if pe < 0:
        # Severe conflict in state effects overrides dataflow
        return float(pe)
    return float(w_pe * pe + w_io * io)


def functional_similarity(ec1: EncodedCapability, ec2: EncodedCapability) -> float:
    """
    Computes functional similarity between two capabilities based on their
    preconditions, effects, and I/O contracts.
    Symmetric: Sim(C1, C2) == Sim(C2, C1).
    """
    return cosine_similarity(ec1.functional_vector, ec2.functional_vector)


def implementation_similarity(ec1: EncodedCapability, ec2: EncodedCapability) -> float:
    """
    Computes implementation similarity (mechanism and capability type).
    API vs DATABASE vs GUI will have lower implementation similarity even if
    functional similarity is high.
    """
    return cosine_similarity(ec1.implementation_vector, ec2.implementation_vector)


def overall_similarity(
    ec1: EncodedCapability,
    ec2: EncodedCapability,
    w_func: float = 0.7,
    w_impl: float = 0.2,
    w_ops: float = 0.1,
) -> float:
    """
    Computes composite similarity balancing functional, implementation, and operational features.
    """
    s_func = functional_similarity(ec1, ec2)
    s_impl = implementation_similarity(ec1, ec2)
    s_ops = cosine_similarity(ec1.operational_vector, ec2.operational_vector)
    return float(w_func * s_func + w_impl * s_impl + w_ops * s_ops)


def state_applicability_score(es: EncodedState, ec: EncodedCapability) -> float:
    """
    Measures whether capability ec is applicable to state es.
    Returns 1.0 if all preconditions match, < 1.0 if unsatisfied or violated.
    """
    p_mask = ec.m_pre
    p_vals = ec.v_pre
    s_mask = es.mask_vector
    s_vals = es.state_vector

    total_pre = np.sum(p_mask)
    if total_pre == 0:
        return 1.0

    # Unset required variables
    missing = p_mask * (1.0 - s_mask)
    if np.sum(missing) > 0:
        return -0.5

    # Check value match
    diff = (s_vals - p_vals) * p_mask
    violations = np.sum(np.abs(diff) > 1e-4)
    if violations > 0:
        return -1.0
    return 1.0


def goal_relevance(
    ec: EncodedCapability,
    eg: EncodedGoal,
    eps: float = 1e-9,
) -> float:
    """
    Evaluates how directly a capability's effects satisfy the goal specification.
    Returns relevance score in [-1.0, 1.0].
    Positive: contributes positively to goal conditions.
    Zero: irrelevant (does not affect any goal condition).
    Negative: counterproductive (modifies a goal variable to an undesirable value).
    """
    g_mask = eg.mask_vector
    g_vals = eg.goal_vector
    e_mask = ec.m_eff
    e_vals = ec.v_eff

    # Common variables between goal and effects
    overlap_mask = g_mask * e_mask
    overlap_count = np.sum(overlap_mask)

    if overlap_count == 0:
        return 0.0

    # Compute alignment of values
    alignments = (e_vals * g_vals) * overlap_mask
    pos_matches = np.sum(alignments > 0)
    neg_conflicts = np.sum(alignments < 0)

    score = (pos_matches - neg_conflicts) / (np.sum(g_mask) + eps)
    return float(np.clip(score, -1.0, 1.0))


def operational_utility(
    ec: EncodedCapability,
    w_rel: float = 0.4,
    w_avail: float = 0.2,
    w_time: float = 0.2,
    w_cost: float = 0.2,
    max_time_ms: float = 1000.0,
    max_cost: float = 10.0,
) -> float:
    """
    Calculates scalar multi-attribute operational utility in [0, 1].
    Higher is better (more reliable, higher availability, lower latency, lower cost).
    """
    ops = ec.raw_capability.operational_profile
    rel = ops.reliability
    avail = ops.availability
    norm_time = 1.0 - min(1.0, ops.execution_time_ms / max_time_ms)
    norm_cost = 1.0 - min(1.0, ops.monetary_cost / max_cost)

    utility = (w_rel * rel + w_avail * avail + w_time * norm_time + w_cost * norm_cost)
    return float(np.clip(utility, 0.0, 1.0))
