"""
Evaluation Metrics and Statistical Tools for Capability Embeddings.
Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from typing import List, Dict, Any, Tuple
import numpy as np


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-8 and n2 < 1e-8:
        return 1.0
    if n1 < 1e-8 or n2 < 1e-8:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def euclidean_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute Euclidean distance between two vectors."""
    return float(np.linalg.norm(v1 - v2))


def directional_asymmetry(score_ab: float, score_ba: float) -> float:
    """
    Measure degree of asymmetry between A -> B and B -> A compatibility.
    High value indicates strongly directed relationship.
    """
    return abs(score_ab - score_ba)


def pareto_dominates(ops_a: np.ndarray, ops_b: np.ndarray, maximize_mask: List[bool]) -> bool:
    """
    Check if operational vector A Pareto-dominates operational vector B.
    ops: [time, cost, resource, risk, neg_log_rel, avail]
    minimize: time, cost, resource, risk, neg_log_rel (indices 0, 1, 2, 3, 4)
    maximize: avail (index 5)
    """
    better_or_equal = True
    strictly_better = False

    for i, max_flag in enumerate(maximize_mask):
        val_a = ops_a[i]
        val_b = ops_b[i]

        if max_flag:
            if val_a < val_b:
                better_or_equal = False
                break
            if val_a > val_b:
                strictly_better = True
        else:
            if val_a > val_b:
                better_or_equal = False
                break
            if val_a < val_b:
                strictly_better = True

    return better_or_equal and strictly_better


def compute_diversity_index(vectors: List[np.ndarray]) -> float:
    """
    Compute mean pairwise distance among a set of capability vectors.
    Measures dispersion and capability identity distinction in the embedding space.
    """
    n = len(vectors)
    if n <= 1:
        return 0.0
    total_dist = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_dist += euclidean_distance(vectors[i], vectors[j])
            count += 1
    return float(total_dist / count) if count > 0 else 0.0
