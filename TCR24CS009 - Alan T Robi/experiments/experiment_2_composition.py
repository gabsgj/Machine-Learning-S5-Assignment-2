import os
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.capability import Capability, load_capabilities_from_json
from src.encoder import CapabilityVocabulary, CapabilityEncoder
from src.composition import compose, vector_composition_addition
from src.similarity import similarity
from src.utils import ensure_dir, save_csv

def run_experiment_2(capabilities: List[Capability], encoder: CapabilityEncoder) -> Dict[str, Any]:
    """
    Run Experiment 2: Capability Composition.
    Constructs composite capability CompletePurchase from CreateOrder -> MakePayment -> SendNotification.
    """
    cap_map = {c.name: c for c in capabilities}

    c1 = cap_map["CreateOrder"]
    c2 = cap_map["MakePayment"]
    c3 = cap_map["SendNotification"]

    sequence = [c1, c2, c3]
    comp_cap = compose(sequence, composite_name="CompletePurchase")

    # Vector Encodings
    v1 = encoder.encode_capability(c1)
    v2 = encoder.encode_capability(c2)
    v3 = encoder.encode_capability(c3)
    v_comp = encoder.encode_capability(comp_cap)
    v_add = vector_composition_addition([v1, v2, v3])

    sim_comp_c1 = similarity(v_comp, v1)
    sim_comp_c2 = similarity(v_comp, v2)
    sim_comp_c3 = similarity(v_comp, v3)
    sim_comp_add = similarity(v_comp, v_add)

    results_data = [
        {"Comparison": "CompletePurchase vs CreateOrder", "CosineSimilarity": sim_comp_c1, "Type": "Atomic Step 1"},
        {"Comparison": "CompletePurchase vs MakePayment", "CosineSimilarity": sim_comp_c2, "Type": "Atomic Step 2"},
        {"Comparison": "CompletePurchase vs SendNotification", "CosineSimilarity": sim_comp_c3, "Type": "Atomic Step 3"},
        {"Comparison": "CompletePurchase vs Vector Addition (v1+v2+v3)", "CosineSimilarity": sim_comp_add, "Type": "Linear Approx"}
    ]

    df_results = pd.DataFrame(results_data)
    save_csv(df_results, "results/tables/experiment_2_composition.csv")

    # Preservation Analysis Data
    preservation_summary = {
        "CompositeName": comp_cap.name,
        "AtomicInputs": [i.name for c in sequence for i in c.inputs],
        "CompositeNetInputs": [i.name for i in comp_cap.inputs],
        "AtomicOutputs": [o.name for c in sequence for o in c.outputs],
        "CompositeOutputs": [o.name for o in comp_cap.outputs],
        "CompositeEffects": comp_cap.effects,
        "CumulativeTime_ms": comp_cap.cost.time,
        "MaxRisk": comp_cap.cost.risk,
        "CombinedReliability": comp_cap.reliability,
        "MinimumAvailability": comp_cap.availability
    }

    # Plot Visualizations
    ensure_dir("results/plots")
    plt.figure(figsize=(9, 4.5))
    categories = df_results["Comparison"].values
    sims = df_results["CosineSimilarity"].values
    colors = ['#3498db', '#9b59b6', '#e67e22', '#1abc9c']

    plt.bar(categories, sims, color=colors, edgecolor='black', alpha=0.85, width=0.5)
    plt.ylabel("Cosine Similarity", fontsize=11, fontweight='bold')
    plt.title("Experiment 2: Composite Capability Embedding Relationships", fontsize=12, fontweight='bold')
    plt.ylim(0, 1.1)
    plt.xticks(rotation=15, ha='right', fontsize=9)
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/plots/plot_composite_similarity.png", dpi=300)
    plt.close()

    return {
        "df": df_results,
        "composite_capability": comp_cap,
        "preservation": preservation_summary
    }

if __name__ == "__main__":
    caps = load_capabilities_from_json("data/capabilities.json")
    vocab = CapabilityVocabulary(caps)
    enc = CapabilityEncoder(vocab)
    res = run_experiment_2(caps, enc)
    print("Experiment 2 completed successfully.")
    print(res["df"])
