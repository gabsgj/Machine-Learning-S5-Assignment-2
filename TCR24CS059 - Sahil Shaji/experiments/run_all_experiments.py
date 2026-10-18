"""
Master Experiment Runner.
Executes all 5 required experiments from Section 7 and benchmarks computational efficiency.
Generates all publication-quality figures and logs results.
"""

import os
import sys
import json
import time
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from experiments.exp1_compatibility import run_experiment_1
from experiments.exp2_composition import run_experiment_2
from experiments.exp3_alternatives import run_experiment_3
from experiments.exp4_irrelevance import run_experiment_4
from experiments.exp5_operational import run_experiment_5
from capability_embedding import CapabilityEmbeddingSystem, benchmark_system_performance
from datasets.ecommerce import get_ecommerce_capabilities, get_ecommerce_initial_state, get_ecommerce_goal


def run_all(figures_dir: str = "figures", results_file: str = "experiments/experiment_results.json") -> Dict[str, Any]:
    print("\n" + "=" * 70)
    print("STARTING FULL EXPERIMENTAL SUITE (ASSIGNMENT 2 REQUIREMENTS)")
    print("=" * 70 + "\n")

    os.makedirs(figures_dir, exist_ok=True)
    os.makedirs(os.path.dirname(results_file), exist_ok=True)

    results = {}

    # Experiment 1
    t0 = time.time()
    results["exp1_compatibility"] = run_experiment_1(figures_dir)
    print(f"-> Experiment 1 completed in {time.time() - t0:.2f}s\n")

    # Experiment 2
    t0 = time.time()
    results["exp2_composition"] = run_experiment_2(figures_dir)
    print(f"-> Experiment 2 completed in {time.time() - t0:.2f}s\n")

    # Experiment 3
    t0 = time.time()
    results["exp3_alternatives"] = run_experiment_3(figures_dir)
    print(f"-> Experiment 3 completed in {time.time() - t0:.2f}s\n")

    # Experiment 4
    t0 = time.time()
    results["exp4_irrelevance"] = run_experiment_4(figures_dir)
    print(f"-> Experiment 4 completed in {time.time() - t0:.2f}s\n")

    # Experiment 5
    t0 = time.time()
    results["exp5_operational"] = run_experiment_5(figures_dir)
    print(f"-> Experiment 5 completed in {time.time() - t0:.2f}s\n")

    # Section 8 Efficiency Benchmark
    print("=" * 60)
    print("Running Efficiency and Computational Profile Benchmark")
    print("=" * 60)
    caps = get_ecommerce_capabilities()
    sys = CapabilityEmbeddingSystem()
    state = get_ecommerce_initial_state()
    goal = get_ecommerce_goal()
    sys.schema.auto_register_from_domain(states=[state], capabilities=list(caps.values()), goals=[goal])

    bench = benchmark_system_performance(sys, [caps["CreateOrder_API"], caps["MakePayment"]], num_runs=2000)
    results["benchmarks"] = bench
    print(f"Encoding Latency: {bench['avg_encode_latency_us']} us ({bench['encode_throughput_ops_sec']} ops/sec)")
    print(f"Composition Latency: {bench['avg_compose_latency_us']} us ({bench['compose_throughput_ops_sec']} ops/sec)")
    print(f"Vector Dimensions: {bench['total_vector_dim']} dims ({bench['raw_vector_bytes']} bytes per vector)")

    # Save structured results
    with open(results_file, "w", encoding="utf-8") as f:
        # Strip non-serializable fields if any
        json.dump(results, f, indent=2)

    print(f"\n[Completed] All experimental results saved to -> {results_file}")
    print("=" * 70 + "\n")
    return results


if __name__ == "__main__":
    run_all()
