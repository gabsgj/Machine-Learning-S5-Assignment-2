from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np

from src.models import (
    Capability,
    CapabilityType,
    Constraint,
    Goal,
    IOField,
    OperationalCost,
    Predicate,
    Resource,
    State,
)
from src.encoder import (
    EFFECT_SLICE,
    INPUT_SLICE,
    MECH_SLICE,
    OPS_SLICE,
    OUTPUT_SLICE,
    PRE_SLICE,
    encode_capability,
    encode_goal,
)
from src.metrics import (
    cosine_similarity,
    goal_relevance,
    similarity,
    validate_compatibility,
    vector_compatibility,
)
from src.composer import compose

DATA_PATH = ROOT / "data" / "experimental_dataset.json"
RESULTS_DIR = ROOT / "experiments" / "results"
PLOTS_DIR = RESULTS_DIR / "plots"


def load_dataset(path: Path | str = DATA_PATH) -> tuple[dict[str, Capability], dict[str, State], dict[str, Goal]]:
    """Load JSON dataset into formal model instances."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    capabilities: dict[str, Capability] = {}
    for c_data in data["capabilities"]:
        cap = Capability(
            id=c_data["id"],
            name=c_data["name"],
            T=CapabilityType(c_data["T"]),
            I=[IOField(**item) for item in c_data.get("I", [])],
            O=[IOField(**item) for item in c_data.get("O", [])],
            P=[Predicate(**item) for item in c_data.get("P", [])],
            E=[Predicate(**item) for item in c_data.get("E", [])],
            K=[Constraint(**item) for item in c_data.get("K", [])],
            R=[Resource(**item) for item in c_data.get("R", [])],
            Q=OperationalCost(**c_data.get("Q", {})),
            Rel=float(c_data.get("Rel", 1.0)),
            A=float(c_data.get("A", 1.0)),
            M=c_data.get("M", {}),
            components=c_data.get("components", []),
        )
        capabilities[cap.id] = cap

    states: dict[str, State] = {}
    for s_data in data["states"]:
        st = State(id=s_data["id"], values=s_data["values"])
        states[st.id] = st

    goals: dict[str, Goal] = {}
    for g_data in data["goals"]:
        g = Goal(
            id=g_data["id"],
            conditions=[Predicate(**item) for item in g_data.get("conditions", [])],
        )
        goals[g.id] = g

    return capabilities, states, goals


def run_experiment_1(capabilities: dict[str, Capability]) -> dict[str, Any]:
    """Experiment 1: Capability Compatibility."""
    pairs_to_test = [
        ("C1", "C2", "CreateOrder -> MakePayment (expected compatible)"),
        ("C1", "C3", "CreateOrder -> CancelCart (expected incompatible: contradiction)"),
        ("C2", "C1", "MakePayment -> CreateOrder (directionality test)"),
        ("C1", "C4", "CreateOrder -> SendNotification (expected incompatible: unmet precondition)"),
        ("C2", "C4", "MakePayment -> SendNotification (expected compatible)"),
        ("C1", "C8", "CreateOrder -> ArchiveOrder (expected incompatible: missing payment effect)"),
    ]

    records = []
    for src_id, dst_id, description in pairs_to_test:
        producer = capabilities[src_id]
        consumer = capabilities[dst_id]

        score = vector_compatibility(producer, consumer)
        val = validate_compatibility(producer, consumer)

        records.append({
            "pair": f"{producer.name} -> {consumer.name}",
            "src_id": src_id,
            "dst_id": dst_id,
            "description": description,
            "align_ep": score.effect_precondition,
            "align_oi": score.output_input,
            "vector_score": score.vector_score,
            "availability_factor": score.availability_factor,
            "execution_score": score.execution_score,
            "formally_compatible": val.compatible,
            "reasons": val.reasons,
        })

    return {"records": records}


def run_experiment_2(capabilities: dict[str, Capability]) -> dict[str, Any]:
    """Experiment 2: Capability Composition."""
    chain = [capabilities["C1"], capabilities["C2"], capabilities["C4"]]
    composite = compose(chain)
    v_comp = encode_capability(composite)

    v1 = encode_capability(chain[0])
    v2 = encode_capability(chain[1])
    v4 = encode_capability(chain[2])

    sim_comp_c1 = similarity(composite, chain[0])
    sim_comp_c2 = similarity(composite, chain[1])
    sim_comp_c4 = similarity(composite, chain[2])

    external_inputs = [i.name for i in composite.I]
    external_pre = [p.name for p in composite.P]
    final_effects = [e.name for e in composite.E]
    terminal_outputs = [o.name for o in composite.O]

    expected_time = sum(c.Q.execution_time_ms for c in chain)
    expected_rel = float(np.prod([c.Rel for c in chain]))
    expected_avail = float(np.prod([c.A for c in chain]))

    return {
        "composite_id": composite.id,
        "composite_name": composite.name,
        "components": composite.components,
        "external_inputs": external_inputs,
        "external_preconditions": external_pre,
        "terminal_outputs": terminal_outputs,
        "final_effects": final_effects,
        "similarities": {
            "comp_vs_C1": round(sim_comp_c1, 4),
            "comp_vs_C2": round(sim_comp_c2, 4),
            "comp_vs_C4": round(sim_comp_c4, 4),
        },
        "operational": {
            "execution_time_ms": composite.Q.execution_time_ms,
            "expected_time_ms": expected_time,
            "monetary_cost": composite.Q.monetary_cost,
            "reliability": composite.Rel,
            "expected_reliability": round(expected_rel, 6),
            "availability": composite.A,
            "expected_availability": round(expected_avail, 6),
        },
    }


def run_experiment_3(capabilities: dict[str, Capability]) -> dict[str, Any]:
    """Experiment 3: Alternative Implementations."""
    c_api = capabilities["C10"]  # API_CreateOrder
    c_db = capabilities["C11"]   # DB_CreateOrder
    c_gui = capabilities["C12"]  # GUI_CreateOrder

    v_api = encode_capability(c_api)
    v_db = encode_capability(c_db)
    v_gui = encode_capability(c_gui)

    pairs = [
        ("API vs DB", c_api, c_db, v_api, v_db),
        ("API vs GUI", c_api, c_gui, v_api, v_gui),
        ("DB vs GUI", c_db, c_gui, v_db, v_gui),
    ]

    results = []
    for label, ca, cb, va, vb in pairs:
        full_sim = similarity(ca, cb)
        eff_sim = cosine_similarity(va[EFFECT_SLICE], vb[EFFECT_SLICE])
        pre_sim = cosine_similarity(va[PRE_SLICE], vb[PRE_SLICE])
        io_in_sim = cosine_similarity(va[INPUT_SLICE], vb[INPUT_SLICE])
        io_out_sim = cosine_similarity(va[OUTPUT_SLICE], vb[OUTPUT_SLICE])
        mech_sim = cosine_similarity(va[MECH_SLICE], vb[MECH_SLICE])
        ops_sim = cosine_similarity(va[OPS_SLICE], vb[OPS_SLICE])

        results.append({
            "pair": label,
            "full_similarity": round(full_sim, 4),
            "effect_similarity": round(eff_sim, 4),
            "precondition_similarity": round(pre_sim, 4),
            "input_similarity": round(io_in_sim, 4),
            "output_similarity": round(io_out_sim, 4),
            "mechanism_similarity": round(mech_sim, 4),
            "operational_similarity": round(ops_sim, 4),
        })

    return {"alternatives": results}


def run_experiment_4(capabilities: dict[str, Capability], goals: dict[str, Goal]) -> dict[str, Any]:
    """Experiment 4: Irrelevant Capabilities and Goal Relevance."""
    target_goal = goals["Goal_Master"]
    candidates = [
        ("C1", capabilities["C1"], "Useful: establishes Order.exists=true"),
        ("C2", capabilities["C2"], "Useful: establishes Payment.status=SUCCESS"),
        ("C4", capabilities["C4"], "Useful: establishes Notification.sent=true"),
        ("C7", capabilities["C7"], "Irrelevant: establishes Order.status=COMPLETED"),
        ("C8", capabilities["C8"], "Irrelevant: establishes Order.archived=true"),
        ("C9", capabilities["C9"], "Contradictory/Irrelevant: sets Payment.status=REFUNDED"),
        ("C5", capabilities["C5"], "Irrelevant: establishes Inventory.available=true"),
        ("C3", capabilities["C3"], "Contradictory: establishes Cart.status=CANCELLED"),
    ]

    rankings = []
    for cid, cap, role in candidates:
        rel = goal_relevance(cap, target_goal)
        rankings.append({
            "id": cid,
            "name": cap.name,
            "role": role,
            "relevance_score": round(rel, 4),
        })

    # Sort descending by relevance score
    rankings.sort(key=lambda x: x["relevance_score"], reverse=True)
    return {
        "goal_id": target_goal.id,
        "rankings": rankings,
    }


def run_experiment_5(capabilities: dict[str, Capability]) -> dict[str, Any]:
    """
    Experiment 5: Operational Attributes.
    
    Includes both:
    1. Representation-level analysis: Direct examination of the PSD-160 operational
       slice [152:160], calculating pairwise cosine similarity and Euclidean distance.
    2. Application-level utility analysis: An external decision tool demonstrating
       how an application can prioritize capabilities based on business preferences.
    """
    options = [
        capabilities["C11"],  # DB_CreateOrder (fast, cheap, high rel)
        capabilities["C10"],  # API_CreateOrder (moderate time/cost)
        capabilities["C12"],  # GUI_CreateOrder (slow, zero money, lower rel)
        capabilities["C13"],  # UnavailableOrderService (A = 0.0)
    ]

    # 1. Representation-level operational vector analysis
    vectors = {c.id: encode_capability(c)[OPS_SLICE] for c in options}
    pairwise_rep = []
    comparison_pairs = [
        ("C11 (DB)", "C10 (API)", "C11", "C10"),
        ("C11 (DB)", "C12 (GUI)", "C11", "C12"),
        ("C10 (API)", "C12 (GUI)", "C10", "C12"),
        ("C11 (DB)", "C13 (Unavail)", "C11", "C13"),
        ("C10 (API)", "C13 (Unavail)", "C10", "C13"),
        ("C12 (GUI)", "C13 (Unavail)", "C12", "C13"),
    ]

    for label_a, label_b, id_a, id_b in comparison_pairs:
        va, vb = vectors[id_a], vectors[id_b]
        cos_sim = cosine_similarity(va, vb)
        euc_dist = float(np.linalg.norm(va - vb))
        pairwise_rep.append({
            "pair": f"{label_a} vs {label_b}",
            "id_a": id_a,
            "id_b": id_b,
            "cosine_similarity": round(cos_sim, 4),
            "euclidean_distance": round(euc_dist, 4),
        })

    operational_vectors = {}
    for c in options:
        v_ops = vectors[c.id]
        operational_vectors[c.id] = {
            "name": c.name,
            "norm_time": round(float(v_ops[0]), 4),
            "norm_money": round(float(v_ops[1]), 4),
            "norm_resource": round(float(v_ops[2]), 4),
            "risk": round(float(v_ops[3]), 4),
            "energy": round(float(v_ops[4]), 4),
            "unreliability": round(float(v_ops[5]), 4),
            "unavailability": round(float(v_ops[6]), 4),
            "composite_cost": round(float(v_ops[7]), 4),
        }

    # 2. Application-level utility analysis (external decision policy)
    weights_scenarios = [
        ("Speed-focused", 0.7, 0.1, 0.2),       # w_time, w_cost, w_rel
        ("Reliability-focused", 0.1, 0.1, 0.8),
        ("Cost-focused", 0.1, 0.8, 0.1),
    ]

    scenario_results = {}
    for s_name, w_time, w_cost, w_rel in weights_scenarios:
        scores = []
        for cap in options:
            norm_t = min(1.0, cap.Q.execution_time_ms / 1000.0)
            norm_m = min(1.0, cap.Q.monetary_cost / 0.10)
            utility = w_rel * cap.Rel - w_time * norm_t - w_cost * norm_m
            effective_utility = cap.A * utility

            scores.append({
                "id": cap.id,
                "name": cap.name,
                "raw_utility": round(utility, 4),
                "effective_utility": round(effective_utility, 4),
                "time_ms": cap.Q.execution_time_ms,
                "cost_money": cap.Q.monetary_cost,
                "reliability": cap.Rel,
                "availability": cap.A,
            })
        scores.sort(key=lambda x: x["effective_utility"], reverse=True)
        scenario_results[s_name] = scores

    return {
        "representation_level": {
            "operational_vectors": operational_vectors,
            "pairwise_comparisons": pairwise_rep,
        },
        "utility_analysis": {
            "scenarios": scenario_results,
        },
        "scenarios": scenario_results,
    }


def save_csv_results(exp1_res, exp2_res, exp3_res, exp4_res, exp5_res):
    """Write human-readable CSV summaries of experiment results."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Compatibility CSV
    with open(RESULTS_DIR / "compatibility.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "pair", "src_id", "dst_id", "align_ep", "align_oi", "vector_score", "execution_score", "formally_compatible"
        ])
        writer.writeheader()
        for r in exp1_res["records"]:
            writer.writerow({
                "pair": r["pair"],
                "src_id": r["src_id"],
                "dst_id": r["dst_id"],
                "align_ep": r["align_ep"],
                "align_oi": r["align_oi"],
                "vector_score": r["vector_score"],
                "execution_score": r["execution_score"],
                "formally_compatible": r["formally_compatible"],
            })

    # 2. Composition CSV
    with open(RESULTS_DIR / "composition.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["composite_id", exp2_res["composite_id"]])
        writer.writerow(["composite_name", exp2_res["composite_name"]])
        writer.writerow(["components", " -> ".join(exp2_res["components"])])
        writer.writerow(["external_inputs", ", ".join(exp2_res["external_inputs"])])
        writer.writerow(["external_preconditions", ", ".join(exp2_res["external_preconditions"])])
        writer.writerow(["terminal_outputs", ", ".join(exp2_res["terminal_outputs"])])
        writer.writerow(["final_effects", ", ".join(exp2_res["final_effects"])])
        for k, v in exp2_res["similarities"].items():
            writer.writerow([k, v])
        for k, v in exp2_res["operational"].items():
            writer.writerow([k, v])

    # 3. Alternatives CSV
    with open(RESULTS_DIR / "alternative_implementations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "pair", "full_similarity", "effect_similarity", "precondition_similarity",
            "input_similarity", "output_similarity", "mechanism_similarity", "operational_similarity"
        ])
        writer.writeheader()
        for r in exp3_res["alternatives"]:
            writer.writerow(r)

    # 4. Goal Relevance CSV
    with open(RESULTS_DIR / "goal_relevance.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "role", "relevance_score"])
        writer.writeheader()
        for r in exp4_res["rankings"]:
            writer.writerow(r)

    # 5. Operational Attributes CSV
    with open(RESULTS_DIR / "operational_attributes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["# SECTION 1: PSD-160 OPERATIONAL VECTOR COMPARISONS (REPRESENTATION LEVEL)"])
        writer.writerow(["pair", "cosine_similarity", "euclidean_distance"])
        for p in exp5_res["representation_level"]["pairwise_comparisons"]:
            writer.writerow([p["pair"], p["cosine_similarity"], p["euclidean_distance"]])
        writer.writerow([])
        writer.writerow(["# SECTION 2: UTILITY-BASED SELECTION (APPLICATION-LEVEL DECISION POLICY)"])
        writer.writerow(["scenario", "rank", "id", "name", "effective_utility", "time_ms", "cost_money", "reliability", "availability"])
        scenarios_data = exp5_res["utility_analysis"]["scenarios"]
        for s_name, rows in scenarios_data.items():
            for rank, r in enumerate(rows, start=1):
                writer.writerow([
                    s_name, rank, r["id"], r["name"], r["effective_utility"],
                    r["time_ms"], r["cost_money"], r["reliability"], r["availability"]
                ])


def generate_plots(exp1_res, exp3_res, exp4_res, exp5_res):
    """Generate and save publication-quality visualization figures."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Plot 1: Compatibility Scores
    pairs = [r["pair"].replace(" -> ", "\n-> ") for r in exp1_res["records"]]
    scores = [r["execution_score"] for r in exp1_res["records"]]
    colors = ["#2ecc71" if r["formally_compatible"] else "#e74c3c" for r in exp1_res["records"]]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(pairs, scores, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    plt.axhline(0.70, color="#2980b9", linestyle="--", linewidth=1.5, label="Compatibility Threshold (0.70)")
    plt.axhline(0.00, color="gray", linestyle="-", linewidth=0.8)
    plt.title("Experiment 1: Execution Compatibility Scores Across Capability Pairs", fontsize=12, fontweight="bold")
    plt.ylabel("Execution Compatibility Score", fontsize=10)
    plt.ylim(-1.1, 1.15)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "compatibility_scores.png", dpi=300)
    plt.close()

    # Plot 2: Alternative Implementations Block Similarities
    labels = [r["pair"] for r in exp3_res["alternatives"]]
    eff_sim = [r["effect_similarity"] for r in exp3_res["alternatives"]]
    pre_sim = [r["precondition_similarity"] for r in exp3_res["alternatives"]]
    mech_sim = [r["mechanism_similarity"] for r in exp3_res["alternatives"]]
    ops_sim = [r["operational_similarity"] for r in exp3_res["alternatives"]]
    full_sim = [r["full_similarity"] for r in exp3_res["alternatives"]]

    x = np.arange(len(labels))
    width = 0.15

    plt.figure(figsize=(9, 5))
    plt.bar(x - 2 * width, eff_sim, width, label="Effects", color="#27ae60")
    plt.bar(x - width, pre_sim, width, label="Preconditions", color="#2ecc71")
    plt.bar(x, ops_sim, width, label="Operational", color="#f39c12")
    plt.bar(x + width, mech_sim, width, label="Mechanism", color="#e74c3c")
    plt.bar(x + 2 * width, full_sim, width, label="Full Vector", color="#3498db")

    plt.xlabel("Alternative Implementation Pairs", fontsize=10)
    plt.ylabel("Cosine Similarity", fontsize=10)
    plt.title("Experiment 3: Functional vs Mechanism Similarity Across Implementations", fontsize=12, fontweight="bold")
    plt.xticks(x, labels)
    plt.ylim(-0.1, 1.15)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "alternative_implementations.png", dpi=300)
    plt.close()

    # Plot 3: Goal Relevance Ranking
    names = [r["name"] for r in exp4_res["rankings"]][::-1]
    rel_scores = [r["relevance_score"] for r in exp4_res["rankings"]][::-1]
    colors_g = ["#27ae60" if s > 0 else "#95a5a6" for s in rel_scores]

    plt.figure(figsize=(8, 5))
    plt.barh(names, rel_scores, color=colors_g, edgecolor="black", linewidth=0.8)
    plt.xlabel("Goal Relevance Score", fontsize=10)
    plt.title("Experiment 4: Capability Relevance Ranking for Goal_Master", fontsize=12, fontweight="bold")
    plt.xlim(0, 0.45)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "goal_relevance.png", dpi=300)
    plt.close()

    # Plot 4: Operational Tradeoffs
    scenarios_data = exp5_res["utility_analysis"]["scenarios"]
    scenarios = list(scenarios_data.keys())
    cap_ids = ["C11 (DB)", "C10 (API)", "C12 (GUI)", "C13 (Unavail)"]

    matrix = []
    for s_name in scenarios:
        row_dict = {r["id"]: r["effective_utility"] for r in scenarios_data[s_name]}
        matrix.append([
            row_dict.get("C11", 0.0),
            row_dict.get("C10", 0.0),
            row_dict.get("C12", 0.0),
            row_dict.get("C13", 0.0),
        ])

    matrix = np.array(matrix)
    x = np.arange(len(scenarios))
    w = 0.18

    plt.figure(figsize=(9, 5))
    for i, cid in enumerate(cap_ids):
        plt.bar(x + (i - 1.5) * w, matrix[:, i], w, label=cid)

    plt.xticks(x, scenarios)
    plt.ylabel("Effective Utility Score", fontsize=10)
    plt.title("Experiment 5: Operational Selection Utility across Priority Profiles", fontsize=12, fontweight="bold")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "operational_tradeoffs.png", dpi=300)
    plt.close()


def main():
    print("==================================================")
    print("ASSIGNMENT 2 EXPERIMENTS: PSD-160 EVALUATION")
    print("==================================================")

    capabilities, states, goals = load_dataset()
    print(f"Loaded {len(capabilities)} capabilities, {len(states)} states, {len(goals)} goals.\n")

    # Experiment 1
    print("--- Running Experiment 1: Capability Compatibility ---")
    exp1_res = run_experiment_1(capabilities)
    for r in exp1_res["records"]:
        compat_str = "COMPATIBLE" if r["formally_compatible"] else "INCOMPATIBLE"
        print(f"[{compat_str:12}] {r['pair']:<38} | VecScore={r['vector_score']:+.4f} | ExecScore={r['execution_score']:+.4f}")
    print()

    # Experiment 2
    print("--- Running Experiment 2: Capability Composition ---")
    exp2_res = run_experiment_2(capabilities)
    print(f"Composite ID: {exp2_res['composite_id']}")
    print(f"Components:   {' -> '.join(exp2_res['components'])}")
    print(f"Ext. Inputs:  {exp2_res['external_inputs']}")
    print(f"Ext. Pre:     {exp2_res['external_preconditions']}")
    print(f"Final Effects:{exp2_res['final_effects']}")
    print(f"Similarities: {exp2_res['similarities']}")
    print(f"Operational:  Time={exp2_res['operational']['execution_time_ms']} ms | Rel={exp2_res['operational']['reliability']}")
    print()

    # Experiment 3
    print("--- Running Experiment 3: Alternative Implementations ---")
    exp3_res = run_experiment_3(capabilities)
    for r in exp3_res["alternatives"]:
        print(f"{r['pair']:<12} | FullSim={r['full_similarity']:.4f} | EffSim={r['effect_similarity']:.4f} | MechSim={r['mechanism_similarity']:.4f} | OpsSim={r['operational_similarity']:.4f}")
    print()

    # Experiment 4
    print("--- Running Experiment 4: Irrelevant Capabilities ---")
    exp4_res = run_experiment_4(capabilities, goals)
    print(f"Target Goal: {exp4_res['goal_id']}")
    for r in exp4_res["rankings"]:
        print(f"[{r['id']}] {r['name']:<20} | Relevance={r['relevance_score']:.4f} | {r['role']}")
    print()

    # Experiment 5
    print("--- Running Experiment 5: Operational Attributes ---")
    exp5_res = run_experiment_5(capabilities)
    print("Part A: PSD-160 Operational Vector Representations (Slice [152:160]):")
    for p in exp5_res["representation_level"]["pairwise_comparisons"]:
        print(f"  {p['pair']:<12} | CosineSim={p['cosine_similarity']:.4f} | EuclDist={p['euclidean_distance']:.4f}")
    print("\nPart B: Utility-Based Selection (Application Decision Policy on Operational Slices):")
    for s_name, rows in exp5_res["utility_analysis"]["scenarios"].items():
        print(f"Scenario: {s_name}")
        for rank, r in enumerate(rows, start=1):
            print(f"  #{rank} {r['id']:<4} {r['name']:<24} | Utility={r['effective_utility']:+.4f} | Time={r['time_ms']}ms | Rel={r['reliability']}")
    print()

    # Save JSON results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = {
        "compatibility": exp1_res,
        "composition": exp2_res,
        "alternative_implementations": exp3_res,
        "goal_relevance": exp4_res,
        "operational_attributes": exp5_res,
    }
    with open(RESULTS_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    # Save CSVs
    save_csv_results(exp1_res, exp2_res, exp3_res, exp4_res, exp5_res)
    print(f"Results saved to {RESULTS_DIR}/results.json and CSV files.")

    # Generate Plots
    generate_plots(exp1_res, exp3_res, exp4_res, exp5_res)
    print(f"Plots saved to {PLOTS_DIR}/")
    print("==================================================")


if __name__ == "__main__":
    main()
