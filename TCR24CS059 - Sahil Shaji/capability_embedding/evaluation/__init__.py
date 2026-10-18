"""
Evaluation sub-package: Pareto optimization, benchmarking, and consistency metrics.
"""

from .pareto import is_pareto_efficient, compute_operational_pareto_frontier
from .benchmarks import benchmark_system_performance

__all__ = [
    "is_pareto_efficient",
    "compute_operational_pareto_frontier",
    "benchmark_system_performance",
]
