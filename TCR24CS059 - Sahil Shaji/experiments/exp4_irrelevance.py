"""
Experiment 4: Irrelevant Capabilities (Section 7 Experiment 4).
Tests whether the vector representation distinguishes useful capabilities
from irrelevant and counter-productive capabilities relative to a specified goal.
"""

import os
import sys
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from capability_embedding import (
    CapabilityEmbeddingSystem,
    goal_relevance,
    compose_sequence
)
from datasets.ecommerce import get_ecommerce_capabilities, get_ecommerce_initial_state, get_ecommerce_goal
from capability_embedding.visualization.plots import plot_goal_relevance_ranking


def run_experiment_4(figures_dir: str = "figures") -> Dict[str, Any]:
    print("=" * 60)
    print("Running Experiment 4: Irrelevant Capabilities Analysis")
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

    z_goal = system.encode_goal(goal)
    z_s0 = system.encode_state(state)

    # Composite purchase capability
    c_comp = compose_sequence(
        [caps["CreateOrder_API"], caps["MakePayment"], caps["SendNotification"]],
        name="CompositePurchase"
    )

    test_caps = [
        c_comp,
        caps["CreateOrder_API"],
        caps["MakePayment"],
        caps["SendNotification"],
        caps["CheckInventory"],
        caps["BrowseCatalogRecommendations"],
        caps["UpdateUserAvatar"],
        caps["GenerateTaxAuditReport"],
        caps["ResetOrderState"],
    ]

    labels = []
    scores = []

    print(f"\n[Goal Specification G]: {goal.conditions}")
    print(f"{'Capability':<30} | {'Goal Relevance':<15} | {'Category'}")
    print("-" * 65)

    for c in test_caps:
        z_c = system.encode_capability(c)
        rel = goal_relevance(z_c, z_goal, z_s0)
        labels.append(c.name)
        scores.append(float(rel))

        if rel > 0.15:
            cat = "USEFUL (Direct Goal Contributor)"
        elif rel > -0.05:
            cat = "IRRELEVANT (Orthogonal)"
        else:
            cat = "DETRIMENTAL (Reverses Goal)"

        print(f"{c.name:<30} | {rel:>14.4f} | {cat}")

    # Plot
    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "exp4_goal_relevance_ranking.png")
    plot_goal_relevance_ranking(labels, scores, fig_path)
    print(f"\n[Plot Saved] Goal relevance ranking -> {fig_path}")

    return {
        "labels": labels,
        "scores": scores,
        "figure_path": fig_path
    }


if __name__ == "__main__":
    run_experiment_4()
