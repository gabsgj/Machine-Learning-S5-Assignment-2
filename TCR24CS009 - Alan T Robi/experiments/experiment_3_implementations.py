import os
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.capability import Capability, load_capabilities_from_json
from src.encoder import CapabilityVocabulary, CapabilityEncoder
from src.similarity import similarity, functional_similarity, subvector_similarity
from src.utils import ensure_dir, save_csv

def run_experiment_3(capabilities: List[Capability], encoder: CapabilityEncoder) -> Dict[str, Any]:
    """
    Run Experiment 3: Alternative Implementations.
    Compares CreateOrder (API), CreateOrderDatabase (DATABASE), and CreateOrderGUI (GUI).
    """
    cap_map = {c.name: c for c in capabilities}

    c_api = cap_map["CreateOrder"]
    c_db = cap_map["CreateOrderDatabase"]
    c_gui = cap_map["CreateOrderGUI"]

    v_api = encoder.encode_capability(c_api)
    v_db = encoder.encode_capability(c_db)
    v_gui = encoder.encode_capability(c_gui)

    pairs = [
        ("CreateOrder (API)", "CreateOrderDatabase (DB)", c_api, c_db, v_api, v_db),
        ("CreateOrder (API)", "CreateOrderGUI (GUI)", c_api, c_gui, v_api, v_gui),
        ("CreateOrderDatabase (DB)", "CreateOrderGUI (GUI)", c_db, c_gui, v_db, v_gui)
    ]

    results = []
    for label1, label2, c1, c2, v1, v2 in pairs:
        full_sim = similarity(v1, v2)
        func_sim = functional_similarity(v1, v2, encoder)
        type_sim = subvector_similarity(v1, v2, encoder, "type")
        mech_sim = subvector_similarity(v1, v2, encoder, "mechanism")
        res_sim = subvector_similarity(v1, v2, encoder, "resources")

        results.append({
            "Implementation Pair": f"{c1.name} vs {c2.name}",
            "Type1": c1.type,
            "Type2": c2.type,
            "FullVectorSimilarity": full_sim,
            "FunctionalSubspaceSim": func_sim,
            "TypeSubspaceSim": type_sim,
            "MechanismSubspaceSim": mech_sim,
            "ResourceSubspaceSim": res_sim
        })

    df_results = pd.DataFrame(results)
    save_csv(df_results, "results/tables/experiment_3_implementations.csv")

    # Plot Visualization
    ensure_dir("results/plots")
    plt.figure(figsize=(9, 5))
    x = np.arange(len(pairs))
    width = 0.25

    full_scores = df_results["FullVectorSimilarity"].values
    func_scores = df_results["FunctionalSubspaceSim"].values
    mech_scores = df_results["MechanismSubspaceSim"].values

    plt.bar(x - width, func_scores, width, label='Functional Subspace Sim', color='#2ecc71', edgecolor='black', alpha=0.85)
    plt.bar(x, full_scores, width, label='Full Vector Sim', color='#3498db', edgecolor='black', alpha=0.85)
    plt.bar(x + width, mech_scores, width, label='Mechanism Subspace Sim', color='#e74c3c', edgecolor='black', alpha=0.85)

    plt.ylabel("Similarity Score", fontsize=11, fontweight='bold')
    plt.title("Experiment 3: Alternative Implementation Sub-space Analysis", fontsize=12, fontweight='bold')
    plt.xticks(x, [p[0].split(" vs ")[0] + "\nvs " + p[1].split(" vs ")[0] for p in pairs], fontsize=9)
    plt.ylim(0, 1.15)
    plt.legend(loc='upper right', frameon=True)
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/plots/plot_alternative_implementations.png", dpi=300)
    plt.close()

    return {
        "df": df_results
    }

if __name__ == "__main__":
    caps = load_capabilities_from_json("data/capabilities.json")
    vocab = CapabilityVocabulary(caps)
    enc = CapabilityEncoder(vocab)
    res = run_experiment_3(caps, enc)
    print("Experiment 3 completed successfully.")
    print(res["df"])
