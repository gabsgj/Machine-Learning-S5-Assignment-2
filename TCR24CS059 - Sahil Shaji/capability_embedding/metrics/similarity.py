"""
Similarity metrics for capability and entity comparison (Deliverable 2 & Section 6.1).
Explicitly decouples functional similarity from composability.
"""

from typing import Union, Optional, Dict
import numpy as np

from ..embedding.vector_space import MultiFacetedEmbedding


def functional_similarity(x: MultiFacetedEmbedding, y: MultiFacetedEmbedding) -> float:
    """
    Computes functional similarity between two entities based on their state delta effects.
    Yields 1.0 for capabilities with identical state transitions, even if implemented differently.
    """
    v1 = x.delta_vector
    v2 = y.delta_vector
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-12 or norm2 < 1e-12:
        return 1.0 if (norm1 < 1e-12 and norm2 < 1e-12) else 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def mechanism_similarity(x: MultiFacetedEmbedding, y: MultiFacetedEmbedding) -> float:
    """
    Computes implementation mechanism similarity (API, Database, GUI, etc.).
    """
    v1 = x.implementation_vector
    v2 = y.implementation_vector
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-12 or norm2 < 1e-12:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def operational_similarity(x: MultiFacetedEmbedding, y: MultiFacetedEmbedding) -> float:
    """
    Computes similarity between operational quality profiles (cost, latency, reliability).
    Uses normalized inverse Euclidean distance.
    """
    v1 = x.operational_vector
    v2 = y.operational_vector
    dist = np.linalg.norm(v1 - v2)
    return float(1.0 / (1.0 + dist))


def similarity(
    x: MultiFacetedEmbedding,
    y: MultiFacetedEmbedding,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Deliverable 2 API: similarity(x, y).
    Compares two encoded entities across functional, mechanism, and operational facets.
    Default weights prioritize functional equivalence (0.6) while accounting for mechanism (0.2)
    and operational profile (0.2).
    """
    if weights is None:
        weights = {"functional": 0.6, "mechanism": 0.2, "operational": 0.2}

    s_func = functional_similarity(x, y)
    s_mech = mechanism_similarity(x, y)
    s_ops = operational_similarity(x, y)

    total_weight = sum(weights.values())
    combined = (
        weights.get("functional", 0.6) * s_func
        + weights.get("mechanism", 0.2) * s_mech
        + weights.get("operational", 0.2) * s_ops
    ) / total_weight

    return float(combined)
