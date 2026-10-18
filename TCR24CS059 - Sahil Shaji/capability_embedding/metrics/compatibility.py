"""
Compatibility and Composability Metrics (Section 6.1 Requirements 3, 4, 5 & Experiment 1).
Measures precondition-effect satisfaction, input-output dataflow, and overall composability.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np

from ..embedding.vector_space import MultiFacetedEmbedding


def precondition_effect_compatibility(c1: MultiFacetedEmbedding, c2: MultiFacetedEmbedding) -> float:
    """
    Evaluates whether c1 enables c2: E(c1) => P(c2).
    Returns a score in [-1.0, 1.0]:
      +1.0 : c1 satisfies all preconditions of c2 that it affects.
       0.0 : c1 is neutral / independent of c2's preconditions.
      -1.0 : c1 directly contradicts / invalidates c2's preconditions.
    """
    m_e1 = c1.eff_mask
    e_val1 = c1.eff_values
    m_p2 = c2.req_mask
    p_val2 = c2.req_values

    # Variables that c1 affects AND c2 requires
    overlap = m_e1 * m_p2
    num_overlapping = np.sum(overlap)

    if num_overlapping < 1e-6:
        # No direct interaction: neutral
        return 0.0

    # For overlapping variables, check if values agree or conflict
    satisfactions = 0.0
    conflicts = 0.0

    for k in range(len(overlap)):
        if overlap[k] > 0.5:
            # Check sign agreement
            if np.sign(e_val1[k]) == np.sign(p_val2[k]) and abs(e_val1[k] - p_val2[k]) < 0.5:
                satisfactions += 1.0
            else:
                conflicts += 1.0

    if conflicts > 0:
        # Contradiction strongly penalizes composability
        return float(-conflicts / num_overlapping)
    else:
        return float(satisfactions / max(np.sum(m_p2), 1.0))


def input_output_compatibility(c1: MultiFacetedEmbedding, c2: MultiFacetedEmbedding) -> float:
    """
    Evaluates dataflow compatibility: outputs of c1 matching required inputs of c2.
    Score in [0.0, 1.0].
    """
    out1 = c1.io_outputs
    in2 = c2.io_inputs

    norm_out = np.linalg.norm(out1)
    norm_in = np.linalg.norm(in2)

    if norm_out < 1e-12 or norm_in < 1e-12:
        return 0.5  # Neutral default if no inputs/outputs specified

    sim = np.dot(out1, in2) / (norm_out * norm_in)
    return float(np.clip(sim, 0.0, 1.0))


def composability(
    c1: MultiFacetedEmbedding,
    c2: MultiFacetedEmbedding,
    pe_weight: float = 0.7,
    io_weight: float = 0.3
) -> float:
    """
    Unified composability score: Composability(c1, c2) in [-1.0, 1.0].
    Positively rewards precondition satisfaction and dataflow matching,
    while severely penalizing precondition contradictions.
    """
    pe_score = precondition_effect_compatibility(c1, c2)
    if pe_score < 0:
        # Precondition conflict makes composition strictly invalid
        return pe_score

    io_score = input_output_compatibility(c1, c2)
    return float(pe_weight * pe_score + io_weight * io_score)
