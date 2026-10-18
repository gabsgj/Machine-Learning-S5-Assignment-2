"""
Experiment 5: Operational Attributes and Multi-Objective Trade-Offs (Section 7 Experiment 5).
Investigates the influence of cost, reliability, availability, risk, and resource requirements.
Evaluates multi-objective Pareto optimality in vector space.
"""

import os
import sys
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from capability_embedding import (
    CapabilityEmbeddingSystem,
    compute_operational_pareto_frontier,
    compose_sequence
)
from datasets.ecommerce import get_ecommerce_capabilities, get_ecommerce_initial_state, get_ecommerce_goal
from capability_embedding.visualization.plots import plot_operational_pareto_frontier


def run_experiment_5(figures_dir: str = "figures") -> Dict[str, Any]:
    print("=" * 60)
    print("Running Experiment 5: Operational Attributes & Pareto Frontier Analysis")
    print("=" * 60)

    caps = get_ecommerce_capabilities()
    system = CapabilityEmbeddingSystem()

    state = get_ecommerce_initial_state()
    goal = get_ecommerce_goal()
    system.schema.auto_register_from_domain(
        states=[state],
        capabilities=list(caps.values()),
        goals=[goal]
    )

    # Candidate set of atomic and composite capabilities
    c_comp_api = compose_sequence([caps["CreateOrder_API"], caps["MakePayment"]], name="Comp_OrderPay_API")
    c_comp_db = compose_sequence([caps["CreateOrder_DB"], caps["MakePayment"]], name="Comp_OrderPay_DB")
    c_comp_gui = compose_sequence([caps["CreateOrder_GUI"], caps["MakePayment"]], name="Comp_OrderPay_GUI")

    candidates = [
        caps["CreateOrder_API"],
        caps["CreateOrder_DB"],
        caps["CreateOrder_GUI"],
        caps["MakePayment"],
        caps["CancelCart"],
        caps["SendNotification"],
        caps["CheckInventory"],
        c_comp_api,
        c_comp_db,
        c_comp_gui
    ]

    embeddings = [system.encode_capability(c) for c in candidates]

    # Compute Pareto frontier on operational criteria
    frontier, pareto_mask = compute_operational_pareto_frontier(embeddings)

    names = [c.name for c in candidates]
    latencies = [c.quality.execution_time_ms for c in candidates]
    costs = [c.quality.monetary_cost for c in candidates]
    reliabilities = [c.quality.reliability for c in candidates]
    risks = [c.quality.risk for c in candidates]

    print(f"\n{'Capability':<25} | {'Latency(ms)':<12} | {'Cost($)':<10} | {'Reliability':<12} | {'Pareto Optimal?'}")
    print("-" * 75)
    for i, c in enumerate(candidates):
        p_status = "YES (Pareto Frontier)" if pareto_mask[i] else "No (Dominated)"
        print(f"{c.name:<25} | {latencies[i]:>11.1f} | {costs[i]:>9.4f} | {reliabilities[i]:>11.4f} | {p_status}")

    # Plot
    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "exp5_operational_pareto_frontier.png")
    plot_operational_pareto_frontier(latencies, costs, reliabilities, names, pareto_mask, fig_path)
    print(f"\n[Plot Saved] Operational Pareto trade-off frontier -> {fig_path}")

    return {
        "candidate_names": names,
        "pareto_mask": pareto_mask.tolist(),
        "frontier_names": [c.name for c in frontier],
        "figure_path": fig_path
    }


if __name__ == "__main__":
    run_experiment_5()
