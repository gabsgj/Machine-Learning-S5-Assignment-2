"""
Experiment 2: Multi-Step Capability Composition Analysis.
Constructs composite capability C1 -> C2 -> C3 and investigates how its vector
relates to atomic components across subspace alignment, algebraic closure,
reconstruction fidelity, and operational accumulation.

Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from typing import Dict, Any, List
import numpy as np

from src.models import Capability, CompositeCapability, State
from src.embedding import CapabilityEmbeddingSpace
from src.composition import CompositionEngine
from dataset.dataset import build_benchmark_dataset


def run_experiment_2() -> Dict[str, Any]:
    dataset = build_benchmark_dataset()
    space = CapabilityEmbeddingSpace(
        state_variables=dataset["state_variables"],
        io_vocab=dataset["io_vocab"],
    )
    engine = CompositionEngine(space)

    c1 = dataset["capabilities"]["C1_CreateOrder_API"]
    c2 = dataset["capabilities"]["C2_MakePayment"]
    c4 = dataset["capabilities"]["C4_SendNotification"]

    pipeline = [c1, c2, c4]  # CreateOrder -> MakePayment -> SendNotification

    # 1. Fidelity between symbolic composite and vector algebraic composite
    fidelity = engine.evaluate_composition_fidelity(pipeline)

    # 2. Vector representations
    v1 = space.encode_capability(c1)
    v2 = space.encode_capability(c2)
    v4 = space.encode_capability(c4)
    v_comp_sym = fidelity["symbolic_vector"]
    v_comp_alg = fidelity["algebraic_vector"]

    # 3. Vector norms and angles
    norm_v1 = float(np.linalg.norm(v1))
    norm_v2 = float(np.linalg.norm(v2))
    norm_v4 = float(np.linalg.norm(v4))
    norm_comp = float(np.linalg.norm(v_comp_sym))

    def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_comp_c1 = cos_sim(v_comp_sym, v1)
    sim_comp_c2 = cos_sim(v_comp_sym, v2)
    sim_comp_c4 = cos_sim(v_comp_sym, v4)

    # 4. State Delta Linear Accumulation (TransE analogy: Delta_comp ~ sum of Deltas)
    delta1 = space.get_delta(v1)
    delta2 = space.get_delta(v2)
    delta4 = space.get_delta(v4)
    delta_sum = delta1 + delta2 + delta4
    delta_comp = space.get_delta(v_comp_sym)
    delta_alignment = cos_sim(delta_sum, delta_comp)

    # 5. Operational attribute verification
    c_comp_obj: CompositeCapability = fidelity["symbolic_composite"]
    ops_actual = c_comp_obj.operational
    expected_latency = c1.operational.time_ms + c2.operational.time_ms + c4.operational.time_ms
    expected_cost = c1.operational.cost_money + c2.operational.cost_money + c4.operational.cost_money
    expected_rel = c1.operational.reliability * c2.operational.reliability * c4.operational.reliability

    # 6. Actual State Transition verification
    s0 = dataset["initial_state"].clone()
    s1 = c1.execute(s0)
    s2 = c2.execute(s1)
    s3 = c4.execute(s2)

    # Direct execution of composite capability on s0
    s_direct = c_comp_obj.execute(s0)
    state_match = (s3.variables == s_direct.variables)

    return {
        "pipeline_names": [c.name for c in pipeline],
        "fidelity": fidelity,
        "norms": {
            "||v1||": round(norm_v1, 4),
            "||v2||": round(norm_v2, 4),
            "||v4||": round(norm_v4, 4),
            "||v_comp||": round(norm_comp, 4),
        },
        "cosine_with_atomic": {
            "Sim(v_comp, v1)": round(sim_comp_c1, 4),
            "Sim(v_comp, v2)": round(sim_comp_c2, 4),
            "Sim(v_comp, v4)": round(sim_comp_c4, 4),
        },
        "state_delta": {
            "delta_alignment_cosine": round(delta_alignment, 4),
            "l2_delta_diff": round(float(np.linalg.norm(delta_sum - delta_comp)), 4),
        },
        "operational": {
            "total_latency_ms": round(ops_actual.time_ms, 2),
            "expected_latency_ms": round(expected_latency, 2),
            "total_cost_usd": round(ops_actual.cost_money, 4),
            "expected_cost_usd": round(expected_cost, 4),
            "composite_reliability": round(ops_actual.reliability, 5),
            "expected_reliability": round(expected_rel, 5),
        },
        "state_transition_exact_match": state_match,
    }


if __name__ == "__main__":
    res = run_experiment_2()
    print("=" * 80)
    print("EXPERIMENT 2: CAPABILITY COMPOSITION ANALYSIS")
    print("=" * 80)
    print("Pipeline: " + " -> ".join(res["pipeline_names"]))
    print(f"\n[*] Vector Composition Fidelity (Symbolic vs Vector Algebraic):")
    print(f"    Full Vector Cosine Similarity : {res['fidelity']['full_cosine_similarity']:.4f}")
    print(f"    L2 Reconstruction Error       : {res['fidelity']['l2_error']:.4f}")
    print(f"    Mean Squared Error (MSE)      : {res['fidelity']['mean_squared_error']:.6f}")
    print("    Subspace Similarities:")
    for sub, sim in res["fidelity"]["subspace_similarities"].items():
        print(f"      - {sub:<14}: {sim:.4f}")

    print(f"\n[*] Vector Geometry & Norms:")
    for k, v in res["norms"].items():
        print(f"    {k:<12}: {v}")

    print(f"\n[*] Directional Alignment with Atomic Components:")
    for k, v in res["cosine_with_atomic"].items():
        print(f"    {k:<18}: {v}")

    print(f"\n[*] State Delta TransE-like Linear Preserving Property:")
    print(f"    Delta Cosine Alignment : {res['state_delta']['delta_alignment_cosine']:.4f}")
    print(f"    Delta L2 Discrepancy   : {res['state_delta']['l2_delta_diff']:.4f}")

    print(f"\n[*] Operational Attribute Propagation:")
    print(f"    Latency (ms)   : Actual={res['operational']['total_latency_ms']} vs Expected={res['operational']['expected_latency_ms']}")
    print(f"    Cost ($)       : Actual={res['operational']['total_cost_usd']} vs Expected={res['operational']['expected_cost_usd']}")
    print(f"    Reliability    : Actual={res['operational']['composite_reliability']} vs Expected={res['operational']['expected_reliability']}")

    print(f"\n[*] Formal State Invariance:")
    print(f"    Step-by-step S3 == Direct Composite S_direct : {res['state_transition_exact_match']}")
    print("=" * 80)
