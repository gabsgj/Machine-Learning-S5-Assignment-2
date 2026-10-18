import os
import sys
import json
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.capability import Capability, load_capabilities_from_json
from src.encoder import CapabilityVocabulary, CapabilityEncoder, CapabilityPCAEncoder
from src.evaluation import measure_efficiency_metrics
from src.utils import ensure_dir, save_csv, save_json

from experiments.experiment_1_compatibility import run_experiment_1
from experiments.experiment_2_composition import run_experiment_2
from experiments.experiment_3_implementations import run_experiment_3
from experiments.experiment_4_irrelevant import run_experiment_4
from experiments.experiment_5_operational import run_experiment_5

def run_all_experiments():
    print("==================================================")
    print("STARTING CAPABILITY EMBEDDING EXPERIMENT SUITE")
    print("==================================================")

    # 1. Load Capabilities & Initialize Encoder
    dataset_path = "data/capabilities.json"
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Capabilities dataset not found at {dataset_path}")

    capabilities = load_capabilities_from_json(dataset_path)
    print(f"Loaded {len(capabilities)} capabilities from '{dataset_path}'.")

    vocab = CapabilityVocabulary(capabilities)
    encoder = CapabilityEncoder(vocab)
    print(f"Constructed Hybrid Structured Feature Vocabulary.")
    print(f"Structured Vector Dimension D = {encoder.dimension}")

    # 2. Fit PCA Dense Encoder (d=16 and 2D for plotting)
    structured_matrix = np.array([encoder.encode_capability(c) for c in capabilities])
    pca_encoder = CapabilityPCAEncoder(n_components=16, random_state=42)
    dense_embeddings_16d = pca_encoder.fit_transform(structured_matrix)
    cum_var = np.sum(pca_encoder.pca.explained_variance_ratio_)
    print(f"PCA projection to d=16 explained variance ratio: {cum_var:.4f}")

    # 2D PCA for Visualization
    pca_2d = CapabilityPCAEncoder(n_components=2, random_state=42)
    dense_2d = pca_2d.fit_transform(structured_matrix)

    ensure_dir("results/plots")
    plt.figure(figsize=(11, 7))
    types = [c.type for c in capabilities]
    unique_types = sorted(list(set(types)))
    cmap = plt.get_cmap('tab10')

    for idx, t_name in enumerate(unique_types):
        indices = [i for i, c in enumerate(capabilities) if c.type == t_name]
        plt.scatter(
            dense_2d[indices, 0], 
            dense_2d[indices, 1], 
            label=t_name, 
            s=90, 
            color=cmap(idx), 
            edgecolor='black', 
            alpha=0.85
        )

    for i, c in enumerate(capabilities):
        plt.annotate(
            c.name, 
            (dense_2d[i, 0], dense_2d[i, 1]), 
            xytext=(5, 5), 
            textcoords='offset points', 
            fontsize=8, 
            alpha=0.9
        )

    plt.xlabel("PCA Component 1", fontsize=11, fontweight='bold')
    plt.ylabel("PCA Component 2", fontsize=11, fontweight='bold')
    plt.title("2D PCA Visualization of Capability Embeddings", fontsize=13, fontweight='bold')
    plt.legend(title="Capability Type", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/plots/plot_pca_embeddings.png", dpi=300)
    plt.close()

    # 3. Execute Experiment 1: Capability Compatibility
    print("\n--- Running Experiment 1: Capability Compatibility ---")
    res1 = run_experiment_1(capabilities, encoder)
    print(f"Experiment 1 Metrics: Proposed F1={res1['metrics']['proposed_f1']:.4f}, Baseline F1={res1['metrics']['baseline_f1']:.4f}")

    # 4. Execute Experiment 2: Capability Composition
    print("\n--- Running Experiment 2: Capability Composition ---")
    res2 = run_experiment_2(capabilities, encoder)
    print(f"Created Composite '{res2['composite_capability'].name}'.")
    print(res2["df"])

    # 5. Execute Experiment 3: Alternative Implementations
    print("\n--- Running Experiment 3: Alternative Implementations ---")
    res3 = run_experiment_3(capabilities, encoder)
    print(res3["df"][["Implementation Pair", "FunctionalSubspaceSim", "MechanismSubspaceSim", "FullVectorSimilarity"]])

    # 6. Execute Experiment 4: Irrelevant Capabilities
    print("\n--- Running Experiment 4: Irrelevant Capabilities ---")
    res4 = run_experiment_4(capabilities, encoder)
    print(res4["df"][["Capability", "Category", "FormalGoalRelevance", "VectorSimilarityToGoal"]])

    # 7. Execute Experiment 5: Operational Attributes
    print("\n--- Running Experiment 5: Operational Attributes ---")
    res5 = run_experiment_5(capabilities, encoder)
    print(res5["df_sims"])

    # 8. Efficiency & Computational Benchmarks
    print("\n--- Measuring Computational & Efficiency Benchmarks ---")
    eff_metrics = measure_efficiency_metrics(capabilities, encoder)
    eff_metrics["pca_explained_variance_16d"] = float(cum_var)
    save_json(eff_metrics, "results/tables/efficiency_metrics.json")
    print(f"Efficiency Metrics: {eff_metrics}")

    # Save Executive Master Summary JSON
    master_summary = {
        "dataset_size": len(capabilities),
        "structured_vector_dimension": encoder.dimension,
        "dense_vector_dimension": 16,
        "pca_explained_variance_16d": cum_var,
        "exp1_proposed_f1": res1['metrics']['proposed_f1'],
        "exp1_baseline_f1": res1['metrics']['baseline_f1'],
        "exp2_composite_name": res2['composite_capability'].name,
        "exp3_api_vs_db_func_sim": float(res3["df"].iloc[0]["FunctionalSubspaceSim"]),
        "exp3_api_vs_db_mech_sim": float(res3["df"].iloc[0]["MechanismSubspaceSim"]),
        "efficiency": eff_metrics
    }
    save_json(master_summary, "results/tables/master_summary.json")

    print("\n==================================================")
    print("ALL EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print("Result tables saved in 'results/tables/'")
    print("Result plots saved in 'results/plots/'")
    print("==================================================")

if __name__ == "__main__":
    run_all_experiments()
