"""
State Applicability Metrics (Section 6.1 Requirement 2).
Quantifies whether a capability can be executed on a given state: S |= P_i.
"""

from typing import Tuple
import numpy as np

from ..embedding.vector_space import MultiFacetedEmbedding


def state_applicability(state_emb: MultiFacetedEmbedding, cap_emb: MultiFacetedEmbedding) -> float:
    """
    Computes applicability of cap_emb to state_emb in vector space.
    Returns:
      1.0 : State fully satisfies all preconditions of the capability.
      < 1.0 : Fraction of satisfied preconditions, penalized by violations.
    """
    # State values are stored in eff_values with eff_mask = 1
    s_val = state_emb.eff_values
    s_mask = state_emb.eff_mask

    m_p = cap_emb.req_mask
    p_val = cap_emb.req_values

    total_reqs = np.sum(m_p)
    if total_reqs < 1e-6:
        # Capability has no preconditions: universally applicable
        return 1.0

    satisfied = 0.0
    for k in range(len(m_p)):
        if m_p[k] > 0.5:
            # Check if state specifies variable k and matches requirement
            if s_mask[k] > 0.5:
                if np.sign(s_val[k]) == np.sign(p_val[k]) and abs(s_val[k] - p_val[k]) < 0.5:
                    satisfied += 1.0
                else:
                    satisfied -= 0.5  # Contradiction penalty

    score = satisfied / total_reqs
    return float(np.clip(score, 0.0, 1.0))
