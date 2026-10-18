#!/usr/bin/env python3
"""
Master runner for all 5 required experiments for Assignment 2:
1. Capability Compatibility (C1 -> C2 vs C1 -> C3)
2. Capability Composition (C1 -> C2 -> C4 vs C124)
3. Alternative Implementations (API vs DB vs GUI)
4. Irrelevant Capabilities (Goal relevance and distractor discrimination)
5. Operational Attributes (Multi-criteria evaluation & Pareto frontier)
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from experiments.exp1_compatibility import run_experiment_1
from experiments.exp2_composition import run_experiment_2
from experiments.exp3_alternative_impl import run_experiment_3
from experiments.exp4_irrelevant_capabilities import run_experiment_4
from experiments.exp5_operational_attributes import run_experiment_5


def run_all():
    print("#" * 80)
    print("  ASSIGNMENT 2: VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
    print("  FULL EXPERIMENTAL SUITE EXECUTION")
    print("#" * 80)

    start_total = time.time()

    print("\n>>> Launching Experiment 1/5...")
    t0 = time.time()
    res1 = run_experiment_1(save_plot=True)
    t1 = time.time() - t0
    print(f"[Done Experiment 1 in {t1:.2f}s]\n")

    print("\n>>> Launching Experiment 2/5...")
    t0 = time.time()
    res2 = run_experiment_2(save_plot=True)
    t2 = time.time() - t0
    print(f"[Done Experiment 2 in {t2:.2f}s]\n")

    print("\n>>> Launching Experiment 3/5...")
    t0 = time.time()
    res3 = run_experiment_3(save_plot=True)
    t3 = time.time() - t0
    print(f"[Done Experiment 3 in {t3:.2f}s]\n")

    print("\n>>> Launching Experiment 4/5...")
    t0 = time.time()
    res4 = run_experiment_4(save_plot=True)
    t4 = time.time() - t0
    print(f"[Done Experiment 4 in {t4:.2f}s]\n")

    print("\n>>> Launching Experiment 5/5...")
    t0 = time.time()
    res5 = run_experiment_5(save_plot=True)
    t5 = time.time() - t0
    print(f"[Done Experiment 5 in {t5:.2f}s]\n")

    total_time = time.time() - start_total
    print("#" * 80)
    print(f"  ALL 5 EXPERIMENTS COMPLETED SUCCESSFULLY IN {total_time:.2f} SECONDS")
    print("  Artifacts generated:")
    print("  - figures/exp1_compatibility_matrix.png")
    print("  - figures/exp2_composition_trajectory.png")
    print("  - figures/exp3_mechanism_clustering.png")
    print("  - figures/exp4_goal_relevance_ranking.png")
    print("  - figures/exp5_pareto_operational.png")
    print("#" * 80)


if __name__ == "__main__":
    run_all()
