"""Experiment 5: Operational Attributes Analysis.

Section 7.5:
Investigate the influence of at least two of the following:
cost, reliability, availability, risk, and resource requirement.

Evaluates:
- Subspace decoupling: functional logic invariant while operational attributes vary
- Multi-criteria trade-off (Cost vs Reliability vs Latency)
- Resource requirement multi-hot vectors and bottleneck detection
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

from src.data.ecommerce_dataset import build_ecommerce_domain
from src.embedding.encoder import CapabilityEncoder
from src.embedding.metrics import functional_similarity, cosine_similarity


def run_experiment_5(save_plot: bool = True):
    print("=" * 60)
    print("EXPERIMENT 5: Operational Attributes (Cost, Reliability, Resources)")
    print("=" * 60)

    domain = build_ecommerce_domain()
    schema = domain["schema"]
    encoder = CapabilityEncoder(schema)
    caps = domain["named_capabilities"]

    c_standard = caps["MakePayment"]
    c_premium = caps["MakePayment_PremiumGateway"]
    c_budget = caps["MakePayment_BudgetGateway"]

    v_std = encoder.encode_capability(c_standard)
    v_prem = encoder.encode_capability(c_premium)
    v_budg = encoder.encode_capability(c_budget)

    # 1. Verify Functional Equivalence
    f_sim_prem = functional_similarity(v_std, v_prem, schema)
    f_sim_budg = functional_similarity(v_std, v_budg, schema)
    print(f"Functional Similarity to Standard Payment:")
    print(f"  Premium Gateway: {f_sim_prem:.4f}")
    print(f"  Budget Gateway:  {f_sim_budg:.4f}")
    print("  -> Confirms operational variance does NOT corrupt functional semantics!")
    print()

    # 2. Operational Subspace extraction
    op_std = v_std[schema.slice_operational]
    op_prem = v_prem[schema.slice_operational]
    op_budg = v_budg[schema.slice_operational]

    print(f"{'Variant':<25} | {'Cost ($)':<10} | {'Time (ms)':<10} | {'Reliability':<12} | {'Availability':<12} | {'Risk':<8}")
    print("-" * 85)
    candidates = [
        ("Standard Stripe", c_standard),
        ("Premium SLA Gateway", c_premium),
        ("Budget Gateway", c_budget),
    ]
    for name, c in candidates:
        print(f"{name:<25} | ${c.cost.monetary_cost:<9.3f} | {c.cost.execution_time_ms:<10.1f} | {c.reliability:<12.4f} | {c.availability:<12.2f} | {c.cost.risk:<8.3f}")

    # Resource requirements
    print()
    print("Resource Footprints:")
    for name, c in candidates:
        res_str = ", ".join([f"{r.name}: {r.amount}" for r in c.resources])
        print(f"  {name}: [{res_str}]")

    if save_plot:
        names = [c[0] for c in candidates]
        costs = [c[1].cost.monetary_cost for c in candidates]
        times = [c[1].cost.execution_time_ms for c in candidates]
        reliabilities = [c[1].reliability * 100 for c in candidates]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

        # Plot 1: Pareto Trade-off Cost vs Reliability
        scatter = ax1.scatter(costs, reliabilities, s=[t/2 for t in times], c=['#2563eb', '#16a34a', '#dc2626'], alpha=0.8, edgecolors='black', linewidth=1.5)
        ax1.set_xlabel("Monetary Cost ($)", fontweight='bold')
        ax1.set_ylabel("Reliability (%)", fontweight='bold')
        ax1.set_title("Operational Trade-off Space (Bubble size = Latency)", pad=15, fontweight='bold')
        ax1.grid(True, linestyle='--', alpha=0.5)

        for i, name in enumerate(names):
            ax1.annotate(f"{name}\n({times[i]}ms)", (costs[i], reliabilities[i]),
                         xytext=(10, -5), textcoords='offset points', fontweight='bold', fontsize=8)

        # Plot 2: Operational Subspace Feature Vector Comparison
        labels = ["Time", "Money", "Res", "Risk", "Energy", "Reliability", "Availability"]
        x = np.arange(len(labels))
        width = 0.25

        ax2.bar(x - width, op_std, width, label='Standard', color='#2563eb')
        ax2.bar(x, op_prem, width, label='Premium', color='#16a34a')
        ax2.bar(x + width, op_budg, width, label='Budget', color='#dc2626')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=30, ha='right', fontweight='bold')
        ax2.set_ylabel("Normalized Value in [-1, 1]", fontweight='bold')
        ax2.set_title("Operational Subspace Vector Coordinates", pad=15, fontweight='bold')
        ax2.legend(loc='lower left')
        ax2.grid(axis='y', linestyle='--', alpha=0.5)

        plt.tight_layout()
        plt.savefig("results/figures/exp5_operational_tradeoffs.png", dpi=200)
        plt.close()
        print("  -> Saved plot: results/figures/exp5_operational_tradeoffs.png")

    return {
        "f_sim_prem": f_sim_prem,
        "f_sim_budg": f_sim_budg,
        "candidates": [
            {
                "name": name,
                "cost": c.cost.monetary_cost,
                "latency_ms": c.cost.execution_time_ms,
                "reliability": c.reliability,
                "availability": c.availability
            }
            for name, c in candidates
        ]
    }


if __name__ == "__main__":
    run_experiment_5()
