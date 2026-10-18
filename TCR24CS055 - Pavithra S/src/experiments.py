import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .composition import compatibility, compose, compose_vector
from .encoder import StructuredEmbedding
from .models import Goal, State, capability_from_dict


def load_dataset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    capabilities = [capability_from_dict(x) for x in data["capabilities"]]
    states = [State(x) for x in data["states"]]
    goals = [Goal([
        __import__("src.models", fromlist=["condition_from_dict"]).condition_from_dict(c)
        for c in g["conditions"]
    ]) for g in data["goals"]]

    return data, capabilities, states, goals


def cosine(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def run_all(dataset_path: str, results_dir: str):
    results = Path(results_dir)
    results.mkdir(parents=True, exist_ok=True)

    data, capabilities, states, goals = load_dataset(dataset_path)
    encoder = StructuredEmbedding(capabilities, states, goals)

    # ----------------------------
    # Encode capabilities
    # ----------------------------
    vectors = {c.name: encoder.encode_capability(c) for c in capabilities}

    vector_df = pd.DataFrame.from_dict(vectors, orient="index", columns=encoder.feature_names())
    vector_df.insert(0, "capability", vector_df.index)
    vector_df.to_csv(results / "capability_vectors.csv", index=False)

    # ----------------------------
    # Experiment 1: compatibility
    # ----------------------------
    pairs = [
        ("CreateOrder", "MakePayment"),
        ("CreateOrder", "CancelCart"),
        ("CreateOrder", "SendNotification"),
        ("MakePayment", "SendNotification"),
        ("UpdateProfile", "MakePayment"),
    ]

    comp_rows = []
    lookup = {c.name: c for c in capabilities}

    for a, b in pairs:
        row = compatibility(lookup[a], lookup[b])
        row["vector_similarity"] = cosine(vectors[a], vectors[b])
        comp_rows.append(row)

    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(results / "compatibility_results.csv", index=False)

    # ----------------------------
    # Experiment 2: composition
    # ----------------------------
    chain_names = ["CreateOrder", "MakePayment", "SendNotification"]
    chain = [lookup[x] for x in chain_names]

    for i in range(len(chain) - 1):
        check = compatibility(chain[i], chain[i + 1])
        if not check["compatible"]:
            raise RuntimeError(
                f"Invalid composition: {chain[i].name} -> {chain[i+1].name}: {check}"
            )

    composite = compose(chain, name="CompletePurchase")
    composite_vector = encoder.encode_capability(composite)
    mean_vector = compose_vector([vectors[x] for x in chain_names])

    composition_rows = [{
        "composite": composite.name,
        "components": " -> ".join(chain_names),
        "cost": composite.cost,
        "reliability": composite.reliability,
        "availability": composite.availability,
        "risk": composite.risk,
        "cosine(composite,mean_atomic)": cosine(composite_vector, mean_vector),
        "cosine(composite,CreateOrder)": cosine(composite_vector, vectors["CreateOrder"]),
        "cosine(composite,MakePayment)": cosine(composite_vector, vectors["MakePayment"]),
        "cosine(composite,SendNotification)": cosine(composite_vector, vectors["SendNotification"]),
    }]
    pd.DataFrame(composition_rows).to_csv(results / "composition_results.csv", index=False)

    # ----------------------------
    # Experiment 3: alternative implementations
    # ----------------------------
    alt = ["CreateOrder", "CreateOrder_Database", "CreateOrder_GUI"]
    alt_rows = []
    for i in range(len(alt)):
        for j in range(i + 1, len(alt)):
            alt_rows.append({
                "capability_1": alt[i],
                "capability_2": alt[j],
                "similarity": cosine(vectors[alt[i]], vectors[alt[j]]),
            })
    pd.DataFrame(alt_rows).to_csv(results / "alternative_implementation_results.csv", index=False)

    # ----------------------------
    # Experiment 4: irrelevant capabilities
    # ----------------------------
    relevant = ["CreateOrder", "MakePayment", "SendNotification"]
    irrelevant = ["UpdateProfile", "SearchProduct"]

    irr_rows = []
    for r in relevant:
        for ir in irrelevant:
            irr_rows.append({
                "relevant_capability": r,
                "irrelevant_capability": ir,
                "similarity": cosine(vectors[r], vectors[ir]),
            })
    pd.DataFrame(irr_rows).to_csv(results / "irrelevant_results.csv", index=False)

    # ----------------------------
    # Experiment 5: operational attributes
    # ----------------------------
    op_names = ["MakePayment", "MakePayment_Backup"]
    op_rows = []
    for name in op_names:
        c = lookup[name]
        op_rows.append({
            "capability": name,
            "cost": c.cost,
            "reliability": c.reliability,
            "availability": c.availability,
            "risk": c.risk,
        })
    pd.DataFrame(op_rows).to_csv(results / "operational_results.csv", index=False)

    # ----------------------------
    # Full similarity matrix
    # ----------------------------
    names = list(vectors.keys())
    matrix = cosine_similarity(np.vstack([vectors[n] for n in names]))
    sim_df = pd.DataFrame(matrix, index=names, columns=names)
    sim_df.to_csv(results / "similarity_matrix.csv")

    plt.figure(figsize=(11, 8))
    plt.imshow(matrix, aspect="auto")
    plt.colorbar(label="Cosine similarity")
    plt.xticks(range(len(names)), names, rotation=70, ha="right")
    plt.yticks(range(len(names)), names)
    plt.title("Capability Embedding Similarity")
    plt.tight_layout()
    plt.savefig(results / "similarity_heatmap.png", dpi=180)
    plt.close()

    # ----------------------------
    # Summary scores
    # ----------------------------
    # These are descriptive experimental indicators, not a universal score.
    known_positive = {("CreateOrder", "MakePayment"): 1}
    known_negative = {("CreateOrder", "CancelCart"): 0}

    rows = []
    for pair, expected in {**known_positive, **known_negative}.items():
        actual = int(
            compatibility(lookup[pair[0]], lookup[pair[1]])["compatible"]
        )
        rows.append({
            "test": f"{pair[0]} -> {pair[1]}",
            "expected": expected,
            "actual": actual,
            "correct": int(expected == actual),
        })

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(results / "experiment_summary.csv", index=False)

    plt.figure(figsize=(7, 4))
    labels = summary_df["test"].tolist()
    values = summary_df["correct"].tolist()
    plt.bar(labels, values)
    plt.ylim(0, 1.2)
    plt.ylabel("Correct compatibility classification")
    plt.title("Required Compatibility Experiment")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(results / "experiment_scores.png", dpi=180)
    plt.close()

    # ----------------------------
    # Console report
    # ----------------------------
    print("\n=== CAPABILITY EMBEDDING ASSIGNMENT ===")
    print(f"Vector dimension: {len(next(iter(vectors.values())))}")
    print("\nFeature block sizes:")
    for k, v in encoder.feature_block_sizes().items():
        print(f"  {k:18s}: {v}")

    print("\nExperiment 1: Compatibility")
    print(comp_df[[
        "from", "to", "compatible", "vector_similarity"
    ]].to_string(index=False))

    print("\nExperiment 2: Composition")
    print(pd.DataFrame(composition_rows).to_string(index=False))

    print("\nExperiment 3: Alternative implementations")
    print(pd.DataFrame(alt_rows).to_string(index=False))

    print("\nExperiment 4: Irrelevant capabilities")
    print(pd.DataFrame(irr_rows).to_string(index=False))

    print("\nExperiment 5: Operational attributes")
    print(pd.DataFrame(op_rows).to_string(index=False))

    print(f"\nResults saved to: {results.resolve()}")


if __name__ == "__main__":
    run_all("data/application.json", "results")
