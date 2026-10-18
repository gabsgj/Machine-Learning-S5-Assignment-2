"""Master Runner for All Experiments and Benchmark Evaluations.

Executes:
1. Dataset persistence to JSON (Deliverable 3)
2. Experiment 1: Capability Compatibility
3. Experiment 2: Capability Composition
4. Experiment 3: Alternative Implementations
5. Experiment 4: Irrelevant Capabilities
6. Experiment 5: Operational Attributes
7. Evaluation across all 9 Section 8 criteria
"""

from __future__ import annotations
import json
import os
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.ecommerce_dataset import save_ecommerce_dataset
from src.data.cloud_pipeline_dataset import save_cloud_pipeline_dataset
from experiments.exp1_compatibility import run_experiment_1
from experiments.exp2_composition import run_experiment_2
from experiments.exp3_alternatives import run_experiment_3
from experiments.exp4_relevance import run_experiment_4
from experiments.exp5_operational import run_experiment_5
from src.evaluation.evaluator import SystemEvaluator


def main():
    print("=" * 70)
    print("PCCST503 ASSIGNMENT 2: VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
    print("Comprehensive Experimental Suite and Evaluation")
    print("=" * 70)

    os.makedirs("datasets", exist_ok=True)
    os.makedirs("results/figures", exist_ok=True)

    # 1. Save Datasets
    print("\n[Phase 1] Persisting Formally Specified Benchmark Datasets...")
    p1 = save_ecommerce_dataset("datasets/ecommerce_domain.json")
    p2 = save_cloud_pipeline_dataset("datasets/cloud_pipeline_domain.json")
    print(f"  -> Saved {p1}")
    print(f"  -> Saved {p2}")

    # 2. Run Experiments 1-5
    print("\n[Phase 2] Executing Experiments 1 to 5...")
    exp1_res = run_experiment_1(save_plot=True)
    exp2_res = run_experiment_2(save_plot=True)
    exp3_res = run_experiment_3(save_plot=True)
    exp4_res = run_experiment_4(save_plot=True)
    exp5_res = run_experiment_5(save_plot=True)

    # 3. Run Section 8 Evaluation Suite
    print("\n" + "=" * 70)
    print("[Phase 3] Evaluating Against Section 8 Criteria (1 to 9)...")
    print("=" * 70)
    evaluator = SystemEvaluator()
    eval_results = evaluator.run_all_evaluations()

    print(f"{'Criterion':<40} | {'Status':<10} | {'Key Metric'}")
    print("-" * 75)
    for res in eval_results:
        status = "PASSED" if res["passed"] else "FAILED"
        # Find key metric display
        crit = res["criterion"]
        detail = ""
        if "separation_margin" in res:
            detail = f"margin={res['separation_margin']:+.2f}"
        elif "homomorphism_cosine" in res:
            detail = f"cosine={res['homomorphism_cosine']:.4f}"
        elif "state_delta_alignment" in res:
            detail = f"delta_align={res['state_delta_alignment']:.4f}"
        elif "zero_collision_guarantee" in res:
            detail = f"min_dist={res['min_pairwise_distance']:.2f}"
        elif "discrimination_ratio" in res:
            detail = f"discrim_ratio={res['discrimination_ratio']:.1f}x"
        elif "functional_invariance" in res:
            detail = f"func_sim={res['functional_invariance']:.4f}, op_dist={res['operational_subspace_distance']:.2f}"
        elif "cloud_pipeline_composition_sim" in res:
            detail = f"pipe_sim={res['cloud_pipeline_composition_sim']:.4f}"
        elif "encodings_per_second" in res:
            detail = f"{res['encodings_per_second']:,.0f} enc/s, {res['storage_bytes_per_vector']}B/vec"
        else:
            detail = str(res.get("valid_dataflow_score", ""))
        print(f"{crit:<40} | {status:<10} | {detail}")

    # Save summary
    summary = {
        "experiments": {
            "exp1": exp1_res,
            "exp2": exp2_res,
            "exp3": exp3_res,
            "exp4": exp4_res,
            "exp5": exp5_res
        },
        "evaluation_criteria": eval_results
    }
    with open("results/evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\n[Phase 4] Benchmark results persisted to results/evaluation_summary.json.")
    print("=" * 70)


if __name__ == "__main__":
    main()
