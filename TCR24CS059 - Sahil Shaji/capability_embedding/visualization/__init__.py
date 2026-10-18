"""
Visualization sub-package: high-resolution figure plotting functions.
"""

from .plots import (
    plot_compatibility_matrix,
    plot_composition_trajectory,
    plot_alternative_implementations,
    plot_goal_relevance_ranking,
    plot_operational_pareto_frontier,
)

__all__ = [
    "plot_compatibility_matrix",
    "plot_composition_trajectory",
    "plot_alternative_implementations",
    "plot_goal_relevance_ranking",
    "plot_operational_pareto_frontier",
]
