"""
main.py
=======
Top-Level Entry Point for Assignment 2: Design of a Vector Embedding for Capability Composition.
Executes the formal embedding system, runs all 5 required experiments, computes evaluation metrics,
exports CSV data, and generates publication plots.
"""

import sys
import os
import time
import pandas as pd
import numpy as np

from dataset import build_ecommerce_application, export_dataset
from embedding import CapabilityEmbedder, StateEmbedder, GoalEmbedder, cosine_similarity
from compatibility import CompatibilityEngine
from composition import CompositionEngine
from experiments import ExperimentRunner
from evaluation import EvaluationSuite
from visualization import Visualizer


def print_banner():
    banner = """
================================================================================
     PCCST503 - MACHINE LEARNING ASSIGNMENT 2: CAPABILITY EMBEDDING
        Formal Vector Embedding Design for Capability Composition
================================================================================
  Domain: E-Commerce & Order Fulfillment
  Formal Model: A = (S, C, SI, G, R, K)
  Capability Vector Space: 108-Dimensional Partitioned Feature Representation
================================================================================
"""
    print(banner)


def main():
    print_banner()

    # 1. Initialization and Dataset Construction
    print("[1/5] Initializing Formal Application Model and Capabilities...")
    app, capabilities = build_ecommerce_application()
    print(f"      - Initial State (SI): {len(app.initial_state.variables)} variables initialized")
    print(f"      - Goal Specification (G): {len(app.goal.conditions)} target conditions")
    print(f"      - Capabilities Catalog (C): {len(capabilities)} formal capabilities registered")

    # Export dataset to data/
    json_path, csv_path = export_dataset(app, data_dir="data")
    print(f"      - Dataset exported: {json_path} & {csv_path}")

    # 2. Setup Embedding, Compatibility, and Composition Engines
    print("\n[2/5] Setting up Embedding, Compatibility, and Composition Engines...")
    embedder = CapabilityEmbedder()
    compat_engine = CompatibilityEngine(embedder=embedder, w_ep=0.50, w_io=0.30, w_state=0.20)
    comp_engine = CompositionEngine(embedder=embedder, compat_engine=compat_engine)
    eval_suite = EvaluationSuite(app=app, embedder=embedder, compat_engine=compat_engine, comp_engine=comp_engine)
    visualizer = Visualizer(app=app, embedder=embedder, compat_engine=compat_engine, comp_engine=comp_engine, output_dir="plots")

    print(f"      - Total Embedding Dimension: {embedder.total_dim} features")
    print(f"        * Type Subspace          : {embedder.d_type}D (One-Hot)")
    print(f"        * Input Subspace         : {embedder.d_in}D (Data Entities)")
    print(f"        * Output Subspace        : {embedder.d_out}D (Data Entities)")
    print(f"        * Precondition Subspace  : {embedder.d_pre}D (Signed Predicates)")
    print(f"        * Effect Subspace        : {embedder.d_eff}D (State Delta Delta-S)")
    print(f"        * Resource Subspace      : {embedder.d_res}D (Hardware & Services)")
    print(f"        * Constraint Subspace    : {embedder.d_con}D (Domain Policies)")
    print(f"        * Operational Subspace   : {embedder.d_ops}D (Cost, Time, Rel, Avail, Risk)")
    print(f"        * Mechanism Subspace     : {embedder.d_mech}D (Protocol & Action Category)")

    # 3. Run the 5 Required Experiments
    print("\n[3/5] Executing the 5 Required Experiments...")
    runner = ExperimentRunner(app=app, embedder=embedder, compat_engine=compat_engine, comp_engine=comp_engine)
    exp_results = runner.run_all_experiments()

    # 4. Evaluation Suite
    print("\n" + "=" * 70)
    print("  COMPREHENSIVE FORMAL EVALUATION SUMMARY (9 EVALUATION CRITERIA)")
    print("=" * 70)
    eval_metrics = eval_suite.evaluate_all()

    for criterion_key, data in eval_metrics.items():
        title = criterion_key.replace("_", " ").title()
        print(f"\n[+] Criterion: {title}")
        for k, v in data.items():
            print(f"    - {k:<42}: {v}")

    # 5. Export CSV Results
    print("\n[4/5] Exporting Experimental and Evaluation CSV Results...")
    os.makedirs("results", exist_ok=True)
    exp_csv_path = runner.export_results_csv(results_dir="results")
    print(f"      - Experiment Results saved to : {exp_csv_path}")

    summary_df = eval_suite.generate_summary_df(eval_metrics)
    summary_csv_path = os.path.join("results", "metrics_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"      - Metrics Summary saved to    : {summary_csv_path}")

    # 6. Generate Publication Visualizations
    print("\n[5/5] Generating Publication-Grade Visualizations...")
    plot_paths = visualizer.generate_all_plots()
    for p in plot_paths:
        print(f"      - Plot generated: {p}")

    print("\n" + "=" * 70)
    print("  ALL EXPERIMENTS AND EVALUATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
