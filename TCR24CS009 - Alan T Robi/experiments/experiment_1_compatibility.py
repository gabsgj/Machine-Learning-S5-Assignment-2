import os
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.capability import Capability, load_capabilities_from_json
from src.encoder import CapabilityVocabulary, CapabilityEncoder
from src.compatibility import compatibility
from src.evaluation import evaluate_compatibility_classification
from src.utils import ensure_dir, save_csv

def run_experiment_1(capabilities: List[Capability], encoder: CapabilityEncoder) -> Dict[str, Any]:
    """
    Run Experiment 1: Capability Compatibility.
    Validates directional compatibility on central demonstration pairs and pairwise dataset.
    """
    cap_map = {c.name: c for c in capabilities}

    # Additional Pairwise Evaluation Dataset
    ground_truth_pairs = [
        ("CreateOrder", "MakePayment", True),
        ("CreateOrder", "CancelCart", False),
        ("MakePayment", "SendNotification", True),
        ("MakePayment", "GenerateInvoice", True),
        ("AddToCart", "CreateOrder", True),
        ("AuthenticateUser", "AddToCart", True),
        ("CheckInventory", "ReserveInventory", True),
        ("ReserveInventory", "CreateOrder", True),
        ("CreateOrder", "SendNotification", False), # Missing required payment_id/receipt_token
        ("CancelCart", "MakePayment", False), # Cart cleared, cannot make payment
        ("LogoutUser", "AddToCart", False), # Unauthenticated user cannot add to cart
        ("UpdateProfile", "MakePayment", False)
    ]

    demo_results = []
    for c1_n, c2_n, gt_label in ground_truth_pairs:
        if c1_n in cap_map and c2_n in cap_map:
            res = compatibility(cap_map[c1_n], cap_map[c2_n])
            demo_results.append({
                "Pair": f"{c1_n} -> {c2_n}",
                "C1": c1_n,
                "C2": c2_n,
                "EffectPreconditionMatch": res.effect_precondition_match,
                "OutputInputMatch": res.output_input_match,
                "CompatibilityScore": res.compatibility_score,
                "HasContradiction": res.has_contradiction,
                "Classification": "Compatible" if res.is_compatible else "Incompatible"
            })

    df_results = pd.DataFrame(demo_results)
    save_csv(df_results, "results/tables/experiment_1_compatibility.csv")

    eval_metrics = evaluate_compatibility_classification(capabilities, ground_truth_pairs, encoder)

    # Generate Visualization Plot
    ensure_dir("results/plots")
    plt.figure(figsize=(10, 5))
    pairs_plot = df_results["Pair"].values[:8]
    scores_plot = df_results["CompatibilityScore"].values[:8]
    colors = ['#2ecc71' if c == "Compatible" else '#e74c3c' for c in df_results["Classification"].values[:8]]

    bars = plt.barh(pairs_plot, scores_plot, color=colors, edgecolor='black', alpha=0.85)
    plt.xlabel("Directional Compatibility Score", fontsize=11, fontweight='bold')
    plt.title("Experiment 1: Directional Capability Compatibility Scores", fontsize=12, fontweight='bold')
    plt.axvline(x=0.5, color='gray', linestyle='--', label='Threshold (0.5)')
    plt.xlim(0, 1.05)
    plt.gca().invert_yaxis()
    plt.grid(axis='x', linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/plots/plot_compatibility_scores.png", dpi=300)
    plt.close()

    return {
        "df": df_results,
        "metrics": eval_metrics,
        "res_1_2": compatibility(cap_map["CreateOrder"], cap_map["MakePayment"]),
        "res_1_3": compatibility(cap_map["CreateOrder"], cap_map["CancelCart"])
    }

if __name__ == "__main__":
    caps = load_capabilities_from_json("data/capabilities.json")
    vocab = CapabilityVocabulary(caps)
    enc = CapabilityEncoder(vocab)
    res = run_experiment_1(caps, enc)
    print("Experiment 1 completed successfully.")
    print(res["df"].head())
