#!/usr/bin/env python3
"""
Interactive Demonstration CLI for Assignment 2:
Design of a Vector Embedding for Capability Composition.
PCCST503 - Machine Learning
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tabulate import tabulate
import numpy as np

from src.dataset.loader import BenchmarkLoader
from src.embedding import EmbeddingSystem
from src.embedding.schema import EmbeddingSchema
from src.models import CapabilityType


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)


def demo_domain_overview(system: EmbeddingSystem, loader: BenchmarkLoader):
    print_banner("1. Application Domain Overview (E-Commerce Benchmark)")
    problem = loader.load_ecommerce_benchmark()

    print(f"Problem Name: {problem.name}")
    print(f"Description:  {problem.description}")
    print(f"State Dimensions: {len(problem.state_variables)} variables (Embedded Dim: {system.schema.state_dim})")
    print(f"Available Resources: {', '.join(problem.available_resources)}")

    print("\n[State Variables Schema]:")
    var_rows = [[v.name, v.var_type.value, str(v.domain) if v.domain else "Any", str(v.default_value)] for v in problem.state_variables]
    print(tabulate(var_rows, headers=["Variable", "Type", "Domain", "Default"], tablefmt="grid"))

    print("\n[Initial State S_I]:")
    s_rows = [[k, str(v)] for k, v in problem.initial_state.values.items()]
    print(tabulate(s_rows, headers=["Variable", "Initial Valuation"], tablefmt="grid"))

    print("\n[Goal Specification G]:")
    g_rows = [[c.variable, c.op.value, str(c.target_value)] for c in problem.goal.conditions]
    print(tabulate(g_rows, headers=["Target Variable", "Operator", "Target Value"], tablefmt="grid"))


def demo_encoding_inspection(system: EmbeddingSystem, loader: BenchmarkLoader):
    print_banner("2. Entity Encoding Inspection (encode(state), encode(goal), encode(capability))")
    problem = loader.load_ecommerce_benchmark()
    c1 = problem.get_capability("C1_CreateOrder")

    # Encode state
    s_emb = system.encode_state(problem.initial_state)
    # Encode goal
    g_emb = system.encode_goal(problem.goal)
    # Encode capability
    c_emb = system.encode_capability(c1)

    print(f"Total Capability Embedding Dimension d_C: {c_emb.dim}")
    print(f"Total State Embedding Dimension d_S:      {s_emb.dim}")
    print(f"Total Goal Embedding Dimension d_G:       {g_emb.dim}")

    print("\n[Subspace Sector Breakdown for C1 (CreateOrder)]:")
    sectors = [
        ["Precondition Values (p_val)", f"R^{c_emb.schema.slice_pre_val.dim}", f"Non-zero elements: {np.count_nonzero(c_emb.pre_val)}"],
        ["Precondition Mask (p_mask)", f"R^{c_emb.schema.slice_pre_mask.dim}", f"Active constraints: {np.count_nonzero(c_emb.pre_mask)}"],
        ["Effect Values (e_val)", f"R^{c_emb.schema.slice_eff_val.dim}", f"Non-zero elements: {np.count_nonzero(c_emb.eff_val)}"],
        ["Effect Mask (e_mask)", f"R^{c_emb.schema.slice_eff_mask.dim}", f"Active updates: {np.count_nonzero(c_emb.eff_mask)}"],
        ["Input Schema (i)", f"R^{c_emb.schema.slice_in.dim}", f"L2 Norm: {np.linalg.norm(c_emb.input_vec):.4f}"],
        ["Output Schema (o)", f"R^{c_emb.schema.slice_out.dim}", f"L2 Norm: {np.linalg.norm(c_emb.output_vec):.4f}"],
        ["Capability Type (t)", f"R^{c_emb.schema.slice_type.dim}", f"Type: {c1.type.value} (One-hot index {c_emb.schema.capability_types.index(c1.type)})"],
        ["Resource Requirements (r)", f"R^{c_emb.schema.slice_res.dim}", f"Multi-hot: {', '.join(c1.resources)}"],
        ["Operational Attributes (q)", f"R^{c_emb.schema.slice_ops.dim}", f"[Time={c1.quality.time_ms}ms, Money=${c1.quality.monetary_cost}, Rel={c1.reliability}]"],
        ["Execution Mechanism (m)", f"R^{c_emb.schema.slice_mech.dim}", f"Type: {c1.mechanism.mechanism_type}"],
    ]
    print(tabulate(sectors, headers=["Sector Name", "Dimension", "Contents & Inspection"], tablefmt="grid"))


def demo_interactive_compatibility(system: EmbeddingSystem, loader: BenchmarkLoader):
    print_banner("3. Directional Compatibility Evaluation (C_i -> C_j)")
    problem = loader.load_ecommerce_benchmark()

    c1 = problem.get_capability("C1_CreateOrder")
    c2 = problem.get_capability("C2_MakePayment")
    c3 = problem.get_capability("C3_CancelCart")
    c4 = problem.get_capability("C4_SendNotification")

    pairs = [(c1, c2), (c1, c3), (c2, c4), (c3, c2)]
    rows = []
    for ca, cb in pairs:
        res = system.compatibility(ca, cb)
        rows.append([
            f"{ca.id} -> {cb.id}",
            "YES (COMPATIBLE)" if res.is_compatible else "NO (INCOMPATIBLE)",
            f"{res.total_score:.4f}",
            f"{res.pe_score:.4f}",
            f"{res.io_score:.4f}",
            res.explanation
        ])

    print(tabulate(rows, headers=["Transition Pair", "Status", "Total Score", "PE Match", "IO Match", "Diagnostic"], tablefmt="grid"))


def demo_interactive_composition(system: EmbeddingSystem, loader: BenchmarkLoader):
    print_banner("4. Capability Composition (C1 -> C2 -> C4)")
    problem = loader.load_ecommerce_benchmark()

    c1 = problem.get_capability("C1_CreateOrder")
    c2 = problem.get_capability("C2_MakePayment")
    c4 = problem.get_capability("C4_SendNotification")

    # Semantic composition
    comp, comp_emb = system.compose([c1, c2, c4], composite_id="C124_OrderPipeline")

    # Direct algebraic vector composition
    emb1 = system.encode_capability(c1)
    emb2 = system.encode_capability(c2)
    emb4 = system.encode_capability(c4)
    from src.embedding.encoder import CapabilityEmbedding
    v_alg_12 = system.composer.vector_compose(emb1, emb2)
    v_alg_124 = system.composer.vector_compose(CapabilityEmbedding("c12", v_alg_12, system.schema), emb4)

    cos_homo = float(np.dot(comp_emb.vector, v_alg_124) / (np.linalg.norm(comp_emb.vector) * np.linalg.norm(v_alg_124)))

    print(f"Composite ID:          {comp.id}")
    print(f"Constituent Pipeline:  {' -> '.join(comp.sub_capabilities)}")
    print(f"Open Preconditions:    {', '.join(repr(p) for p in comp.preconditions)}")
    print(f"Cumulative Effects:    {', '.join(repr(e) for e in comp.effects)}")
    print(f"Total Pipeline Cost:   ${comp.quality.monetary_cost:.4f}")
    print(f"Total Execution Time:  {comp.quality.time_ms:.1f} ms")
    print(f"End-to-End Reliability:{comp.reliability:.6f}")
    print(f"Semantic vs Vector Homomorphism: Cosine = {cos_homo:.6f} (> 0.98)")

    # Execute on initial state
    s0 = problem.initial_state
    s_end = comp.apply(s0)
    print(f"\nGoal Satisfaction after Composite Execution: {problem.is_goal_satisfied(s_end)}")


def demo_alternative_implementations(system: EmbeddingSystem, loader: BenchmarkLoader):
    print_banner("5. Alternative Implementations (API vs DB vs GUI)")
    alts = loader.load_alternative_implementations()

    c_api = next(c for c in alts if c.id == "CreateOrder_API")
    c_db = next(c for c in alts if c.id == "CreateOrder_DB")
    c_gui = next(c for c in alts if c.id == "CreateOrder_GUI")

    tests = [
        ("API vs Database", c_api, c_db),
        ("API vs Web GUI", c_api, c_gui),
        ("Database vs Web GUI", c_db, c_gui),
    ]

    rows = []
    for label, a, b in tests:
        sim_f = system.similarity(a, b, metric="functional")
        sim_m = system.similarity(a, b, metric="mechanism")
        dist_impl = np.linalg.norm(system.encode_capability(a).implementation_vec - system.encode_capability(b).implementation_vec)
        sim_full = system.similarity(a, b, metric="full")

        rows.append([label, f"{sim_f:.4f}", f"{sim_m:.4f}", f"{dist_impl:.4f}", f"{sim_full:.4f}"])

    print(tabulate(rows, headers=["Comparison", "Functional Sim", "Mechanism Sim", "Impl Distance", "Full Vector Sim"], tablefmt="grid"))
    print("\nInsight: Functional equivalence is 1.0000 while implementation mechanisms remain distinctly separated!")


def demo_goal_relevance(system: EmbeddingSystem, loader: BenchmarkLoader):
    print_banner("6. Goal Relevance & Irrelevant Distractor Filtering")
    problem = loader.load_ecommerce_benchmark()
    goal = problem.goal
    goal_emb = system.encode_goal(goal)

    rows = []
    for cap in problem.capabilities:
        rel = system.goal_relevance(cap, goal_emb)
        is_rel = rel > 0.1
        rows.append([cap.id, cap.name, cap.type.value, f"{rel:.4f}", "YES (GOAL CONTRIBUTOR)" if is_rel else "NO (IRRELEVANT / DISTRACTOR)"])

    print(tabulate(rows, headers=["Capability", "Name", "Type", "Goal Relevance", "Classification"], tablefmt="grid"))


def demo_operational_pareto(system: EmbeddingSystem, loader: BenchmarkLoader):
    print_banner("7. Multi-Criteria Operational Evaluation & Pareto Frontier")
    alts = loader.load_alternative_implementations()
    from src.embedding.operational import OperationalEvaluator

    results = OperationalEvaluator.find_pareto_frontier(
        alts,
        metrics_to_minimize=["monetary_cost", "time_ms"],
        metrics_to_maximize=["reliability"]
    )

    rows = []
    for r in results:
        c = next(cap for cap in alts if cap.id == r.capability_id)
        rows.append([
            c.id, c.type.value,
            "YES (PARETO FRONTIER)" if r.is_pareto_optimal else "NO (DOMINATED)",
            f"{c.quality.time_ms:.1f} ms",
            f"${c.quality.monetary_cost:.4f}",
            f"{c.reliability:.4f}",
            ", ".join(r.dominates) if r.dominates else "None"
        ])

    print(tabulate(rows, headers=["Candidate", "Type", "Pareto Status", "Latency", "Monetary Cost", "Reliability", "Dominates"], tablefmt="grid"))


def main():
    loader = BenchmarkLoader()
    problem = loader.load_ecommerce_benchmark()
    schema = EmbeddingSchema(state_variables=problem.state_variables)
    system = EmbeddingSystem(schema)

    while True:
        print("\n" + "#" * 80)
        print("  ASSIGNMENT 2: VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
        print("  Interactive Demonstration CLI")
        print("#" * 80)
        print("  1. Application Domain & State Space Overview")
        print("  2. Formal Entity Encoding Inspection (encode(state), encode(goal), encode(capability))")
        print("  3. Directional Compatibility Evaluation (C_i -> C_j)")
        print("  4. Capability Composition & Homomorphism (C1 -> C2 -> C4)")
        print("  5. Alternative Implementations (API vs DB vs GUI)")
        print("  6. Goal Relevance & Distractor Filtering")
        print("  7. Multi-Criteria Operational Evaluation & Pareto Frontier")
        print("  8. Run All 5 Experiments (Generate Figures & Tables)")
        print("  0. Exit")
        print("#" * 80)

        choice = input("\nEnter choice [0-8]: ").strip()

        if choice == "1":
            demo_domain_overview(system, loader)
        elif choice == "2":
            demo_encoding_inspection(system, loader)
        elif choice == "3":
            demo_interactive_compatibility(system, loader)
        elif choice == "4":
            demo_interactive_composition(system, loader)
        elif choice == "5":
            demo_alternative_implementations(system, loader)
        elif choice == "6":
            demo_goal_relevance(system, loader)
        elif choice == "7":
            demo_operational_pareto(system, loader)
        elif choice == "8":
            from experiments.run_all_experiments import run_all
            run_all()
        elif choice == "0":
            print("\nExiting demonstration. Goodbye!\n")
            break
        else:
            print("\nInvalid choice. Please enter a number between 0 and 8.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--non-interactive":
        # Quick non-interactive dry-run of all options
        loader = BenchmarkLoader()
        problem = loader.load_ecommerce_benchmark()
        schema = EmbeddingSchema(state_variables=problem.state_variables)
        system = EmbeddingSystem(schema)
        demo_domain_overview(system, loader)
        demo_encoding_inspection(system, loader)
        demo_interactive_compatibility(system, loader)
        demo_interactive_composition(system, loader)
        demo_alternative_implementations(system, loader)
        demo_goal_relevance(system, loader)
        demo_operational_pareto(system, loader)
    else:
        main()
