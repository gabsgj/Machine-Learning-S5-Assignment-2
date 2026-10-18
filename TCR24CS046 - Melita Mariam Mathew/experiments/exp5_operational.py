"""
Experiment 5: Operational Attributes and Multi-Objective Trade-Off Analysis.
Investigates the influence of cost, reliability, availability, risk, latency,
and resource requirements across alternative implementations and composite pipelines.

Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from typing import Dict, Any, List
import numpy as np

from src.models import Capability, CompositeCapability
from src.embedding import CapabilityEmbeddingSpace
from src.metrics import pareto_dominates
from dataset.dataset import build_benchmark_dataset


def run_experiment_5() -> Dict[str, Any]:
    dataset = build_benchmark_dataset()
    space = CapabilityEmbeddingSpace(
        state_variables=dataset["state_variables"],
        io_vocab=dataset["io_vocab"],
    )

    caps = dataset["capabilities"]

    # 1. Operational attributes of alternative implementations of CreateOrder
    alts_order = [
        ("API", caps["C1_CreateOrder_API"]),
        ("Database", caps["C1_CreateOrder_DB"]),
        ("GUI", caps["C1_CreateOrder_GUI"]),
    ]

    order_ops_table = []
    for name, c in alts_order:
        op = c.operational
        v = space.encode_capability(c)
        v_ops = space.get_ops(v)
        order_ops_table.append({
            "mechanism": name,
            "latency_ms": op.time_ms,
            "cost_usd": op.cost_money,
            "reliability": op.reliability,
            "availability": op.availability,
            "risk": op.risk,
            "resources": c.resources,
            "v_ops_vector": [round(float(x), 4) for x in v_ops],
        })

    # 2. Operational attributes of End-to-End Alternative Pipelines
    # All achieve the exact same goal: Order Created -> Payment Made -> Notification Sent
    c4 = caps["C4_SendNotification"]

    pipe_internal = CompositeCapability.compose_sequence([
        caps["C1_CreateOrder_DB"],
        caps["C2_MakePayment_Wallet"],
        c4,
    ])
    pipe_internal.name = "Pipeline 1: High-Performance Internal (DB + Wallet + Notif)"

    pipe_cloud = CompositeCapability.compose_sequence([
        caps["C1_CreateOrder_API"],
        caps["C2_MakePayment"],
        c4,
    ])
    pipe_cloud.name = "Pipeline 2: Standard Cloud Services (API + Gateway + Notif)"

    pipe_legacy_rpa = CompositeCapability.compose_sequence([
        caps["C1_CreateOrder_GUI"],
        caps["C2_MakePayment"],
        c4,
    ])
    pipe_legacy_rpa.name = "Pipeline 3: Legacy RPA (GUI Click + Gateway + Notif)"

    pipelines = [
        ("P1_Internal_Fast", pipe_internal),
        ("P2_Standard_Cloud", pipe_cloud),
        ("P3_Legacy_RPA", pipe_legacy_rpa),
    ]

    pipeline_ops_table = []
    raw_ops_list = []
    for pid, p in pipelines:
        op = p.operational
        v = space.encode_capability(p)
        v_ops = space.get_ops(v)
        raw_ops_list.append(v_ops)

        pipeline_ops_table.append({
            "pipeline_id": pid,
            "name": p.name,
            "total_latency_ms": round(op.time_ms, 2),
            "total_cost_usd": round(op.cost_money, 4),
            "joint_reliability": round(op.reliability, 5),
            "series_availability": round(op.availability, 4),
            "cumulative_risk": round(op.risk, 4),
            "v_ops_encoded": [round(float(x), 4) for x in v_ops],
        })

    # 3. Pareto dominance analysis among the 3 composite pipelines
    # Vector: [norm_time, norm_cost, norm_res, risk, neg_log_rel, avail]
    # Minimize indices: 0, 1, 2, 3, 4. Maximize index: 5.
    maximize_mask = [False, False, False, False, False, True]
    dominance_matrix = {}
    for i, (id_a, _) in enumerate(pipelines):
        dominates = []
        for j, (id_b, _) in enumerate(pipelines):
            if i != j:
                if pareto_dominates(raw_ops_list[i], raw_ops_list[j], maximize_mask):
                    dominates.append(id_b)
        dominance_matrix[id_a] = dominates

    return {
        "order_mechanisms": order_ops_table,
        "pipelines": pipeline_ops_table,
        "pareto_dominance": dominance_matrix,
    }


if __name__ == "__main__":
    res = run_experiment_5()
    print("=" * 80)
    print("EXPERIMENT 5: OPERATIONAL ATTRIBUTES & MULTI-OBJECTIVE TRADE-OFFS")
    print("=" * 80)
    print("[*] Alternative Implementations of CreateOrder:")
    print(f"{'Mechanism':<12} | {'Latency':<10} | {'Cost ($)':<10} | {'Reliability':<12} | {'Risk':<8} | {'Resources'}")
    print("-" * 75)
    for row in res["order_mechanisms"]:
        print(f"{row['mechanism']:<12} | {row['latency_ms']:<7.1f} ms | ${row['cost_usd']:<8.4f} | {row['reliability']:<12.4f} | {row['risk']:<8.3f} | {row['resources']}")

    print("\n[*] End-to-End Composite Pipelines (Achieving Same Goal):")
    print(f"{'Pipeline':<18} | {'Latency':<11} | {'Cost':<9} | {'Reliability':<12} | {'Risk':<8} | {'Availability'}")
    print("-" * 75)
    for row in res["pipelines"]:
        print(f"{row['pipeline_id']:<18} | {row['total_latency_ms']:<8.1f} ms | ${row['total_cost_usd']:<7.4f} | {row['joint_reliability']:<12.5f} | {row['cumulative_risk']:<8.4f} | {row['series_availability']:<8.2f}")

    print("\n[*] Pareto Dominance & Multi-Objective Optimization:")
    for pid, doms in res["pareto_dominance"].items():
        if doms:
            print(f"    - {pid} strictly Pareto-dominates: {', '.join(doms)}")
        else:
            print(f"    - {pid} is non-dominated or non-dominating (lies on multi-objective trade-off boundary).")

    print("\n[*] Key Insights:")
    print("    1. P1 (Internal Fast DB/Wallet) achieves highest reliability (0.982) and lowest latency (260 ms) & cost ($0.015), strictly dominating Legacy RPA (P3).")
    print("    2. Cloud Microservice (P2) trades higher latency (550 ms) and cost ($0.058) for decoupling and zero direct DB dependency.")
    print("    3. DF-PVS encodes operational constraints directly into a normalized, additive subspace.")
    print("=" * 80)
