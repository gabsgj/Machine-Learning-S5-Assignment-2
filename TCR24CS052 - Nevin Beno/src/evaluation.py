from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .compatibility import compatibility, goal_relevance
from .composition import compose_capabilities
from .embedding import StructuredEmbedder
from .models import Capability, Goal


def evaluate_compatibility(
    capabilities: Dict[str, Capability],
    embedder: StructuredEmbedder,
) -> pd.DataFrame:
    rows = []
    for a_name, a in capabilities.items():
        for b_name, b in capabilities.items():
            if a_name == b_name:
                continue
            rows.append({
                "from": a_name,
                "to": b_name,
                "compatibility": compatibility(a, b),
                "embedding_similarity": embedder.similarity(
                    embedder.encode_capability(a),
                    embedder.encode_capability(b),
                ),
            })
    return pd.DataFrame(rows)


def evaluate_composition(
    chain: List[Capability],
    embedder: StructuredEmbedder,
) -> pd.DataFrame:
    composite = compose_capabilities(chain, embedder)
    cv = embedder.encode_capability(composite)

    rows = []
    for c in chain:
        rows.append({
            "component": c.name,
            "similarity_to_composite": embedder.similarity(
                embedder.encode_capability(c), cv
            ),
        })
    return pd.DataFrame(rows)


def evaluate_goal_relevance(
    capabilities: Dict[str, Capability],
    goal: Goal,
    embedder: StructuredEmbedder,
) -> pd.DataFrame:
    gv = embedder.encode_goal(goal)
    rows = []
    for name, cap in capabilities.items():
        rows.append({
            "capability": name,
            "goal_relevance": goal_relevance(cap, goal),
            "goal_similarity": embedder.similarity(
                embedder.encode_capability(cap), gv
            ),
        })
    return pd.DataFrame(rows)


def evaluate_operational_effect(
    capabilities: Dict[str, Capability],
    embedder: StructuredEmbedder,
) -> pd.DataFrame:
    rows = []
    for name, cap in capabilities.items():
        cv = embedder.encode_capability(cap)
        rows.append({
            "capability": name,
            "reliability": cap.reliability,
            "availability": cap.availability,
            "vector_norm": float(np.linalg.norm(cv)),
            "operational_block_mean": float(np.mean(cv[64:72])),
        })
    return pd.DataFrame(rows)


def save_plots(
    compatibility_df: pd.DataFrame,
    goal_df: pd.DataFrame,
    operational_df: pd.DataFrame,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    pivot = compatibility_df.pivot(
        index="from", columns="to", values="compatibility"
    )
    plt.figure(figsize=(10, 6))
    plt.imshow(pivot.fillna(0).values, aspect="auto")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.colorbar(label="Compatibility")
    plt.title("Directed Capability Compatibility")
    plt.tight_layout()
    plt.savefig(out_dir / "compatibility_matrix.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    x = np.arange(len(goal_df))
    plt.bar(x - 0.18, goal_df["goal_relevance"], width=0.36, label="Formal relevance")
    plt.bar(x + 0.18, goal_df["goal_similarity"], width=0.36, label="Vector similarity")
    plt.xticks(x, goal_df["capability"], rotation=45, ha="right")
    plt.ylabel("Score")
    plt.title("Capability–Goal Relationship")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "goal_relevance.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.scatter(
        operational_df["reliability"],
        operational_df["operational_block_mean"],
        s=60,
    )
    for _, row in operational_df.iterrows():
        plt.annotate(row["capability"], (row["reliability"], row["operational_block_mean"]))
    plt.xlabel("Reliability")
    plt.ylabel("Operational embedding block mean")
    plt.title("Reliability and Operational Representation")
    plt.tight_layout()
    plt.savefig(out_dir / "operational_effect.png", dpi=160)
    plt.close()
