"""
Operational Pareto Frontier and Multi-Objective Trade-off Analysis (Section 7 Experiment 5).
Investigates trade-offs across cost, latency, reliability, risk, and resource utilization.
"""

from typing import List, Tuple, Dict, Any
import numpy as np

from ..embedding.vector_space import MultiFacetedEmbedding


def is_pareto_efficient(costs: np.ndarray) -> np.ndarray:
    """
    Find the Pareto-efficient points along objective dimensions (all objectives assumed to be minimized).
    :param costs: (n_points, n_costs) array
    :return: (n_points, ) boolean array, indicating whether each point is Pareto efficient
    """
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, c in enumerate(costs):
        if is_efficient[i]:
            # Keep any point with a lower cost in at least one dimension or identical cost
            is_efficient[is_efficient] = np.any(costs[is_efficient] < c, axis=1) | np.all(costs[is_efficient] == c, axis=1)
            is_efficient[i] = True  # And keep self
    return is_efficient


def compute_operational_pareto_frontier(
    capabilities: List[MultiFacetedEmbedding]
) -> Tuple[List[MultiFacetedEmbedding], np.ndarray]:
    """
    Extracts Pareto-optimal capabilities across operational objectives:
      - Execution time (min)
      - Monetary cost (min)
      - Negative log reliability (min <=> max reliability)
      - Risk (min)
    Returns: (list_of_pareto_optimal_embeddings, pareto_mask)
    """
    if not capabilities:
        return [], np.array([], dtype=bool)

    # Cost matrix where all criteria are to be minimized
    # Objectives: [Latency, Money, -log(Rel), Risk]
    cost_matrix = []
    for c in capabilities:
        ops = c.operational_vector
        latency = ops[0]
        money = ops[1]
        neg_log_rel = ops[4]  # Lower is better (higher reliability)
        risk = ops[6]
        cost_matrix.append([latency, money, neg_log_rel, risk])

    cost_matrix = np.array(cost_matrix, dtype=np.float64)
    pareto_mask = is_pareto_efficient(cost_matrix)

    frontier = [capabilities[i] for i in range(len(capabilities)) if pareto_mask[i]]
    return frontier, pareto_mask
