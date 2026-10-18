from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import numpy as np

from src.models.capability import Capability
from src.embedding.encoder import CapabilityEmbedding


@dataclass
class ParetoRankingResult:
    capability_id: str
    is_pareto_optimal: bool
    dominates: List[str]
    dominated_by: List[str]
    scores: Dict[str, float]


class OperationalEvaluator:
    """
    Analyzes quality attributes, costs, reliabilities, and availability
    in both scalar space and vector embedding space.
    """

    @staticmethod
    def extract_operational_metrics(cap: Capability) -> Dict[str, float]:
        return {
            "time_ms": cap.quality.time_ms,
            "monetary_cost": cap.quality.monetary_cost,
            "resource_cost": cap.quality.resource_cost,
            "risk": cap.quality.risk,
            "energy_cost": cap.quality.energy_cost,
            "reliability": cap.reliability,
            "availability": cap.availability,
            "neg_log_reliability": -float(np.log(max(cap.reliability, 1e-6)))
        }

    @staticmethod
    def compute_composite_utility(
        cap: Capability,
        w_time: float = 0.2,
        w_money: float = 0.3,
        w_rel: float = 0.4,
        w_avail: float = 0.1
    ) -> float:
        """
        Calculates normalized operational utility score in [0, 1].
        Higher is better.
        """
        # Costs: normalized inversely (lower cost = higher utility)
        u_time = 1.0 / (1.0 + cap.quality.time_ms / 500.0)
        u_money = 1.0 / (1.0 + cap.quality.monetary_cost / 0.10)
        u_rel = cap.reliability
        u_avail = cap.availability

        return float(w_time * u_time + w_money * u_money + w_rel * u_rel + w_avail * u_avail)

    @classmethod
    def find_pareto_frontier(
        cls,
        capabilities: List[Capability],
        metrics_to_minimize: List[str] = ("monetary_cost", "time_ms"),
        metrics_to_maximize: List[str] = ("reliability", "availability")
    ) -> List[ParetoRankingResult]:
        """
        Computes non-dominated Pareto frontier across multiple operational criteria.
        """
        all_metrics = [cls.extract_operational_metrics(c) for c in capabilities]
        n = len(capabilities)
        results = []

        for i in range(n):
            c_i = capabilities[i]
            m_i = all_metrics[i]
            dominates = []
            dominated_by = []

            for j in range(n):
                if i == j:
                    continue
                c_j = capabilities[j]
                m_j = all_metrics[j]

                # Check if i dominates j:
                # i is at least as good in all criteria, and strictly better in at least one
                i_as_good = True
                i_strictly_better = False

                for min_k in metrics_to_minimize:
                    if m_i[min_k] > m_j[min_k]:
                        i_as_good = False
                        break
                    elif m_i[min_k] < m_j[min_k]:
                        i_strictly_better = True

                if i_as_good:
                    for max_k in metrics_to_maximize:
                        if m_i[max_k] < m_j[max_k]:
                            i_as_good = False
                            break
                        elif m_i[max_k] > m_j[max_k]:
                            i_strictly_better = True

                if i_as_good and i_strictly_better:
                    dominates.append(c_j.id)

                # Check if j dominates i
                j_as_good = True
                j_strictly_better = False

                for min_k in metrics_to_minimize:
                    if m_j[min_k] > m_i[min_k]:
                        j_as_good = False
                        break
                    elif m_j[min_k] < m_i[min_k]:
                        j_strictly_better = True

                if j_as_good:
                    for max_k in metrics_to_maximize:
                        if m_j[max_k] < m_i[max_k]:
                            j_as_good = False
                            break
                        elif m_j[max_k] > m_i[max_k]:
                            j_strictly_better = True

                if j_as_good and j_strictly_better:
                    dominated_by.append(c_j.id)

            is_pareto = (len(dominated_by) == 0)
            results.append(ParetoRankingResult(
                capability_id=c_i.id,
                is_pareto_optimal=is_pareto,
                dominates=dominates,
                dominated_by=dominated_by,
                scores=m_i
            ))

        return results
