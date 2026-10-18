import os
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.capability import Capability, load_capabilities_from_json
from src.encoder import CapabilityVocabulary, CapabilityEncoder
from src.similarity import similarity, functional_similarity, subvector_similarity
from src.utils import ensure_dir, save_csv

def run_experiment_5(capabilities: List[Capability], encoder: CapabilityEncoder) -> Dict[str, Any]:
    """
    Run Experiment 5: Operational Attributes.
    Compares MakePaymentPremium (Service A) vs MakePaymentDiscount (Service B).
    """
    cap_map = {c.name: c for c in capabilities}

    c_std = cap_map["MakePayment"]
    c_prem = cap_map["MakePaymentPremium"]
    c_disc = cap_map["MakePaymentDiscount"]

    v_std = encoder.encode_capability(c_std)
    v_prem = encoder.encode_capability(c_prem)
    v_disc = encoder.encode_capability(c_disc)

    # Operational Trade-off Summary Table
    tradeoff_rows = [
        {
            "Capability": c_prem.name,
            "ServiceTier": "Premium (Service A)",
            "Time_ms": c_prem.cost.time,
            "MonetaryCost_$": c_prem.cost.money,
            "RiskScore": c_prem.cost.risk,
            "Reliability": c_prem.reliability,
            "Availability": c_prem.availability
        },
        {
            "Capability": c_std.name,
            "ServiceTier": "Standard",
            "Time_ms": c_std.cost.time,
            "MonetaryCost_$": c_std.cost.money,
            "RiskScore": c_std.cost.risk,
            "Reliability": c_std.reliability,
            "Availability": c_std.availability
        },
        {
            "Capability": c_disc.name,
            "ServiceTier": "Discount (Service B)",
            "Time_ms": c_disc.cost.time,
            "MonetaryCost_$": c_disc.cost.money,
            "RiskScore": c_disc.cost.risk,
            "Reliability": c_disc.reliability,
            "Availability": c_disc.availability
        }
    ]
    df_tradeoffs = pd.DataFrame(tradeoff_rows)

    # Pairwise Similarity Metrics
    full_sim_prem_disc = similarity(v_prem, v_disc)
    func_sim_prem_disc = functional_similarity(v_prem, v_disc, encoder)
    oper_sim_prem_disc = subvector_similarity(v_prem, v_disc, encoder, "operational")

    full_sim_std_prem = similarity(v_std, v_prem)
    func_sim_std_prem = functional_similarity(v_std, v_prem, encoder)

    sim_results = [
        {
            "Pair": "MakePaymentPremium vs MakePaymentDiscount",
            "FunctionalSimilarity": func_sim_prem_disc,
            "OperationalSimilarity": oper_sim_prem_disc,
            "FullVectorSimilarity": full_sim_prem_disc
        },
        {
            "Pair": "MakePayment (Std) vs MakePaymentPremium",
            "FunctionalSimilarity": func_sim_std_prem,
            "OperationalSimilarity": subvector_similarity(v_std, v_prem, encoder, "operational"),
            "FullVectorSimilarity": full_sim_std_prem
        }
    ]
    df_sims = pd.DataFrame(sim_results)

    save_csv(df_tradeoffs, "results/tables/experiment_5_operational_attributes.csv")
    save_csv(df_sims, "results/tables/experiment_5_operational_similarity.csv")

    # Plot Visualizations
    ensure_dir("results/plots")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Ax1: Cost vs Reliability Radar/Bar
    tiers = df_tradeoffs["ServiceTier"].values
    times = df_tradeoffs["Time_ms"].values
    rel = df_tradeoffs["Reliability"].values * 100.0

    ax1_bar = ax1.bar(tiers, times, color='#34495e', alpha=0.8, label='Execution Time (ms)')
    ax1.set_ylabel("Execution Time (ms)", color='#34495e', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#34495e')

    ax1_twin = ax1.twinx()
    ax1_twin.plot(tiers, rel, color='#27ae60', marker='o', linewidth=2.5, markersize=8, label='Reliability (%)')
    ax1_twin.set_ylabel("Reliability (%)", color='#27ae60', fontweight='bold')
    ax1_twin.set_ylim(85, 101)
    ax1_twin.tick_params(axis='y', labelcolor='#27ae60')
    ax1.set_title("Operational Attributes: Time vs Reliability Trade-off", fontsize=11, fontweight='bold')

    # Ax2: Subspace Similarity Comparison
    labels = ["Functional Sim", "Operational Sim", "Full Vector Sim"]
    vals = [func_sim_prem_disc, oper_sim_prem_disc, full_sim_prem_disc]
    colors = ['#2ecc71', '#e67e22', '#3498db']

    ax2.bar(labels, vals, color=colors, edgecolor='black', alpha=0.85, width=0.5)
    ax2.set_ylabel("Similarity Score", fontsize=11, fontweight='bold')
    ax2.set_title("Premium vs Discount Sub-space Similarity", fontsize=11, fontweight='bold')
    ax2.set_ylim(0, 1.15)
    ax2.grid(axis='y', linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig("results/plots/plot_operational_tradeoff.png", dpi=300)
    plt.close()

    return {
        "df_tradeoffs": df_tradeoffs,
        "df_sims": df_sims
    }

if __name__ == "__main__":
    caps = load_capabilities_from_json("data/capabilities.json")
    vocab = CapabilityVocabulary(caps)
    enc = CapabilityEncoder(vocab)
    res = run_experiment_5(caps, enc)
    print("Experiment 5 completed successfully.")
    print(res["df_tradeoffs"])
    print(res["df_sims"])
