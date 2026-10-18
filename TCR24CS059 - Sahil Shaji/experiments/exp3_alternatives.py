"""
Experiment 3: Alternative Implementations (Section 7 Experiment 3).
Tests whether the embedding captures functional equivalence (identical state effects)
without conflating different execution mechanisms (API, Database, GUI).
"""

import os
import sys
from typing import Dict, Any
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from capability_embedding import (
    CapabilityEmbeddingSystem,
    functional_similarity,
    mechanism_similarity,
    similarity
)
from datasets.ecommerce import get_ecommerce_capabilities, get_ecommerce_initial_state, get_ecommerce_goal
from capability_embedding.visualization.plots import plot_alternative_implementations


def run_experiment_3(figures_dir: str = "figures") -> Dict[str, Any]:
    print("=" * 60)
    print("Running Experiment 3: Alternative Implementations Analysis")
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

    c_api = caps["CreateOrder_API"]
    c_db = caps["CreateOrder_DB"]
    c_gui = caps["CreateOrder_GUI"]

    z_api = system.encode_capability(c_api)
    z_db = system.encode_capability(c_db)
    z_gui = system.encode_capability(c_gui)

    # 1. Compare Functional Similarity
    sim_func_api_db = functional_similarity(z_api, z_db)
    sim_func_api_gui = functional_similarity(z_api, z_gui)
    sim_func_db_gui = functional_similarity(z_db, z_gui)

    # 2. Compare Implementation Subspace Similarity
    sim_impl_api_db = mechanism_similarity(z_api, z_db)
    sim_impl_api_gui = mechanism_similarity(z_api, z_gui)
    sim_impl_db_gui = mechanism_similarity(z_db, z_gui)

    # 3. Full Overall Similarity (weighted)
    sim_overall_api_db = similarity(z_api, z_db)
    sim_overall_api_gui = similarity(z_api, z_gui)

    print(f"\n[Functional Equivalence vs Mechanism Distinguishability]")
    print(f"API vs DB  -> Functional Sim: {sim_func_api_db:.4f} | Mechanism Sim: {sim_impl_api_db:.4f}")
    print(f"API vs GUI -> Functional Sim: {sim_func_api_gui:.4f} | Mechanism Sim: {sim_impl_api_gui:.4f}")
    print(f"DB  vs GUI -> Functional Sim: {sim_func_db_gui:.4f} | Mechanism Sim: {sim_impl_db_gui:.4f}")

    print(f"\n[Operational Profiles]")
    print(f"API Latency: {c_api.quality.execution_time_ms} ms | Cost: ${c_api.quality.monetary_cost} | Rel: {c_api.quality.reliability}")
    print(f"DB  Latency: {c_db.quality.execution_time_ms} ms | Cost: ${c_db.quality.monetary_cost} | Rel: {c_db.quality.reliability}")
    print(f"GUI Latency: {c_gui.quality.execution_time_ms} ms | Cost: ${c_gui.quality.monetary_cost} | Rel: {c_gui.quality.reliability}")

    # Plot
    labels = ["API Implementation", "Database Stored Proc", "GUI Web Client"]
    func_sims = [1.0, float(sim_func_api_db), float(sim_func_api_gui)]
    impl_sims = [1.0, float(sim_impl_api_db), float(sim_impl_api_gui)]
    latencies = [c_api.quality.execution_time_ms, c_db.quality.execution_time_ms, c_gui.quality.execution_time_ms]
    costs = [c_api.quality.monetary_cost, c_db.quality.monetary_cost, c_gui.quality.monetary_cost]

    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "exp3_alternative_implementations.png")
    plot_alternative_implementations(labels, func_sims, impl_sims, latencies, costs, fig_path)
    print(f"\n[Plot Saved] Alternative implementations comparison -> {fig_path}")

    return {
        "sim_func_api_db": float(sim_func_api_db),
        "sim_func_api_gui": float(sim_func_api_gui),
        "sim_impl_api_db": float(sim_impl_api_db),
        "sim_impl_api_gui": float(sim_impl_api_gui),
        "figure_path": fig_path
    }


if __name__ == "__main__":
    run_experiment_3()
