"""
Goal Relevance and Target Alignment Metrics (Section 6.1 Requirement 7 & Experiment 4).
Quantifies how effectively a capability contributes to achieving a specified goal.
"""

from typing import Optional
import numpy as np

from ..embedding.vector_space import MultiFacetedEmbedding


def goal_distance(state_emb: MultiFacetedEmbedding, goal_emb: MultiFacetedEmbedding) -> float:
    """
    Computes Euclidean distance between state and goal on constrained goal variables.
    ||m_G * (s - g)||_2.
    """
    m_g = goal_emb.eff_mask
    g_val = goal_emb.eff_values
    s_val = state_emb.eff_values

    diff = m_g * (s_val - g_val)
    return float(np.linalg.norm(diff))


def goal_relevance(
    cap_emb: MultiFacetedEmbedding,
    goal_emb: MultiFacetedEmbedding,
    initial_state_emb: Optional[MultiFacetedEmbedding] = None
) -> float:
    """
    Computes the directional projection of a capability's effect delta onto the goal vector.
    Returns:
      > 0.0 : Contributes directly toward satisfying one or more goal conditions.
      = 0.0 : Irrelevant to the goal (modifies unrelated variables).
      < 0.0 : Detrimental (reverses or contradicts a goal condition).
    """
    c_delta = cap_emb.delta_vector
    norm_c = np.linalg.norm(c_delta)
    if norm_c < 1e-12:
        return 0.0

    m_g = goal_emb.eff_mask
    g_val = goal_emb.eff_values

    if initial_state_emb is not None:
        # Distance remaining from initial state to goal
        s_val = initial_state_emb.eff_values
        goal_delta = m_g * (g_val - s_val)
    else:
        # Unconstrained goal target
        goal_delta = m_g * g_val

    norm_g = np.linalg.norm(goal_delta)
    if norm_g < 1e-12:
        return 0.0

    # Directional cosine projection
    cosine_proj = float(np.dot(c_delta, goal_delta) / (norm_c * norm_g))
    return cosine_proj


def rank_capabilities_by_goal_relevance(
    capabilities: list,
    goal_emb: MultiFacetedEmbedding,
    initial_state_emb: Optional[MultiFacetedEmbedding] = None
) -> list:
    """
    Ranks a list of capability embeddings by their contribution to the goal.
    Returns sorted list of tuples: (capability_embedding, relevance_score).
    """
    scored = []
    for c in capabilities:
        score = goal_relevance(c, goal_emb, initial_state_emb)
        scored.append((c, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored
