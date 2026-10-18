import os
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.capability import Capability, load_capabilities_from_json
from src.state import Goal
from src.encoder import CapabilityVocabulary, CapabilityEncoder
from src.evaluation import evaluate_goal_relevance
from src.similarity import similarity
from src.utils import ensure_dir, save_csv

def run_experiment_4(capabilities: List[Capability], encoder: CapabilityEncoder) -> Dict[str, Any]:
    """
    Run Experiment 4: Irrelevant Capabilities.
    Compares goal relevance of checkout capabilities vs unrelated capabilities.
    """
    cap_map = {c.name: c for c in capabilities}

    # Define Checkout Goal G
    goal = Goal(conditions=[
        "Order.exists=true",
        "Payment.status=SUCCESS",
        "Notification.sent=true"
    ])

    v_goal = encoder.encode_goal(goal)

    test_caps = [
        ("CreateOrder", "Relevant"),
        ("MakePayment", "Relevant"),
        ("SendNotification", "Relevant"),
        ("GenerateInvoice", "Relevant / Auxiliary"),
        ("AddToCart", "Pre-checkout Relevant"),
        ("UpdateProfile", "Irrelevant"),
        ("CreateWishlist", "Irrelevant"),
        ("GenerateUserReport", "Irrelevant")
    ]

    results = []
    for cap_name, category in test_caps:
        if cap_name not in cap_map:
            continue
        c = cap_map[cap_name]
        v_c = encoder.encode_capability(c)

        rel_score = evaluate_goal_relevance(c, goal)
        vec_sim_to_goal = similarity(v_c, v_goal)

        results.append({
            "Capability": c.name,
            "Type": c.type,
            "Category": category,
            "FormalGoalRelevance": rel_score,
            "VectorSimilarityToGoal": vec_sim_to_goal,
            "RelevanceClassification": "Relevant" if rel_score > 0 else "Irrelevant"
        })

    df_results = pd.DataFrame(results)
    save_csv(df_results, "results/tables/experiment_4_irrelevant.csv")

    # Plot Visualization
    ensure_dir("results/plots")
    plt.figure(figsize=(10, 5))
    names = df_results["Capability"].values
    relevance_scores = df_results["FormalGoalRelevance"].values
    vec_sims = df_results["VectorSimilarityToGoal"].values

    x = np.arange(len(names))
    width = 0.35

    plt.bar(x - width/2, relevance_scores, width, label='Formal Goal Relevance (Effect Match)', color='#2ecc71', edgecolor='black', alpha=0.85)
    plt.bar(x + width/2, vec_sims, width, label='Vector Cosine Sim to Goal Vector', color='#3498db', edgecolor='black', alpha=0.85)

    plt.ylabel("Score", fontsize=11, fontweight='bold')
    plt.title("Experiment 4: Goal Relevance Analysis (Relevant vs Irrelevant Capabilities)", fontsize=12, fontweight='bold')
    plt.xticks(x, names, rotation=20, ha='right', fontsize=9)
    plt.ylim(0, 1.1)
    plt.legend(loc='upper right', frameon=True)
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/plots/plot_goal_relevance.png", dpi=300)
    plt.close()

    return {
        "df": df_results,
        "goal": goal
    }

if __name__ == "__main__":
    caps = load_capabilities_from_json("data/capabilities.json")
    vocab = CapabilityVocabulary(caps)
    enc = CapabilityEncoder(vocab)
    res = run_experiment_4(caps, enc)
    print("Experiment 4 completed successfully.")
    print(res["df"])
