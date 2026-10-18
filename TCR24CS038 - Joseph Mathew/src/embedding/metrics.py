"""Mathematical metrics for Similarity, Composability, and Goal Relevance.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
import numpy as np

from src.models.capability import Capability
from src.models.state import State, Goal
from src.embedding.schema import EmbeddingSchema
from src.embedding.encoder import CapabilityEncoder


def cosine_similarity(v1: np.ndarray, v2: np.ndarray, eps: float = 1e-8) -> float:
    """Standard cosine similarity between two vectors."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < eps or n2 < eps:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def functional_similarity(v1: np.ndarray, v2: np.ndarray, schema: EmbeddingSchema) -> float:
    """Computes functional resemblance between two capabilities.
    
    High when capabilities have similar effects and functional semantics (substitutable),
    regardless of whether they can be chained sequentially.
    """
    # Compare effect vectors and functional semantics
    eff_sim = cosine_similarity(v1[schema.slice_effects], v2[schema.slice_effects])
    fun_sim = cosine_similarity(v1[schema.slice_functional], v2[schema.slice_functional])
    inp_sim = cosine_similarity(v1[schema.slice_inputs], v2[schema.slice_inputs])
    out_sim = cosine_similarity(v1[schema.slice_outputs], v2[schema.slice_outputs])
    
    # Weighted functional similarity (semantic substitute score)
    return float(0.4 * eff_sim + 0.3 * fun_sim + 0.15 * inp_sim + 0.15 * out_sim)


def mechanism_similarity(v1: np.ndarray, v2: np.ndarray, schema: EmbeddingSchema) -> float:
    """Computes similarity of execution mechanism (API vs DB vs GUI)."""
    return cosine_similarity(v1[schema.slice_mechanism], v2[schema.slice_mechanism])


def composability_score(v1: np.ndarray, v2: np.ndarray, schema: EmbeddingSchema) -> Tuple[float, Dict[str, float]]:
    """Directed composability metric C(C1 -> C2).
    
    Evaluates whether C1 enables C2:
    1. Precondition-Effect Alignment: Does effect of C1 satisfy precondition of C2?
       Negative penalty if effect of C1 contradicts precondition of C2!
    2. Input-Output Flow: Does output of C1 supply input required by C2?
    """
    v_e1 = v1[schema.slice_effects]
    v_p2 = v2[schema.slice_preconditions]
    v_o1 = v1[schema.slice_outputs]
    v_i2 = v2[schema.slice_inputs]

    # Precondition count of C2
    p2_mask = np.abs(v_p2) > 1e-3
    p2_count = np.sum(p2_mask)

    if p2_count > 0:
        # Dot product between C1 effects and C2 preconditions for matching variables
        match_product = v_e1 * v_p2
        # Positive where signs agree (satisfaction), negative where signs disagree (conflict)
        satisfied = np.sum(np.maximum(0.0, match_product))
        conflicts = np.sum(np.maximum(0.0, -match_product))
        
        state_compat = (satisfied - 2.0 * conflicts) / float(p2_count)
    else:
        # C2 has no preconditions; state compatibility is neutral/high
        state_compat = 1.0

    # Input-Output Dataflow compatibility
    i2_mask = v_i2 > 1e-3
    i2_count = np.sum(i2_mask)
    if i2_count > 0:
        io_matches = np.sum(np.minimum(v_o1, v_i2))
        data_compat = io_matches / float(i2_count)
    else:
        data_compat = 1.0

    # Total composability score in [-1.0, 1.0]
    total_score = 0.6 * state_compat + 0.4 * data_compat
    total_score = float(np.clip(total_score, -1.0, 1.0))

    breakdown = {
        "state_compatibility": float(state_compat),
        "data_compatibility": float(data_compat),
        "composite_score": total_score
    }
    return total_score, breakdown


def goal_relevance_score(
    cap_vec: np.ndarray,
    goal_vec: np.ndarray,
    curr_state_vec: np.ndarray,
    schema: EmbeddingSchema
) -> float:
    """Computes relevance of capability to reaching goal G from current state S.
    
    Goal delta: Delta_G = phi(G) - phi(S) (dimensions where goal differs from current state).
    Relevance is the projection of capability effect onto Delta_G.
    """
    v_eff = cap_vec[schema.slice_effects]
    goal_delta = goal_vec - curr_state_vec
    
    # We only care about variables where goal specifies a condition
    active_goal = np.abs(goal_vec) > 1e-3
    if not np.any(active_goal):
        return 0.0

    g_masked = goal_delta * active_goal
    n_goal = np.linalg.norm(g_masked)
    n_eff = np.linalg.norm(v_eff * active_goal)
    
    if n_goal < 1e-8 or n_eff < 1e-8:
        return 0.0

    # Dot product between effect and goal delta
    alignment = np.dot(v_eff, g_masked) / (n_eff * n_goal)
    return float(np.clip(alignment, -1.0, 1.0))
