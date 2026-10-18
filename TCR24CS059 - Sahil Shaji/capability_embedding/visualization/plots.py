"""
Publication-Quality Visualization Utilities for Experimental Results.
Generates heatmaps, trajectories, alternative comparisons, and Pareto frontiers.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def plot_compatibility_matrix(
    labels: List[str],
    comp_matrix: np.ndarray,
    sim_matrix: np.ndarray,
    save_path: str
) -> None:
    """
    Plots side-by-side heatmaps comparing Composability vs Functional Similarity.
    Demonstrates that composability and similarity are decoupled (Experiment 1).
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 1. Composability Matrix
    im0 = axes[0].imshow(comp_matrix, cmap="coolwarm", vmin=-1.0, vmax=1.0)
    axes[0].set_title("Directional Composability Score $Comp(C_i \\to C_j)$", fontsize=12, fontweight="bold")
    axes[0].set_xticks(range(len(labels)))
    axes[0].set_yticks(range(len(labels)))
    axes[0].set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    axes[0].set_yticklabels(labels, fontsize=9)
    axes[0].set_xlabel("Target Capability $C_j$", fontsize=10)
    axes[0].set_ylabel("Source Capability $C_i$", fontsize=10)

    # Annotate numbers
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = comp_matrix[i, j]
            axes[0].text(j, i, f"{val:.2f}", ha="center", va="center",
                         color="white" if abs(val) > 0.5 else "black", fontsize=8)

    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

    # 2. Similarity Matrix
    im1 = axes[1].imshow(sim_matrix, cmap="viridis", vmin=0.0, vmax=1.0)
    axes[1].set_title("Functional Similarity $Sim_{func}(C_i, C_j)$", fontsize=12, fontweight="bold")
    axes[1].set_xticks(range(len(labels)))
    axes[1].set_yticks(range(len(labels)))
    axes[1].set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    axes[1].set_yticklabels(labels, fontsize=9)
    axes[1].set_xlabel("Capability $C_j$", fontsize=10)
    axes[1].set_ylabel("Capability $C_i$", fontsize=10)

    for i in range(len(labels)):
        for j in range(len(labels)):
            val = sim_matrix[i, j]
            axes[1].text(j, i, f"{val:.2f}", ha="center", va="center",
                         color="white" if val < 0.6 else "black", fontsize=8)

    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_composition_trajectory(
    pca_coords: np.ndarray,
    labels: List[str],
    save_path: str
) -> None:
    """
    Plots vector space composition trajectory from initial state through composed capabilities to goal.
    (Experiment 2: Capability Composition).
    """
    plt.figure(figsize=(9, 7))

    # Scatter points
    plt.scatter(pca_coords[:, 0], pca_coords[:, 1], c=range(len(labels)), cmap="plasma", s=180, edgecolors="black", zorder=4)

    # Draw directed arrows connecting successive states in composition
    for i in range(len(pca_coords) - 1):
        plt.annotate(
            "",
            xy=(pca_coords[i + 1, 0], pca_coords[i + 1, 1]),
            xytext=(pca_coords[i, 0], pca_coords[i, 1]),
            arrowprops=dict(arrowstyle="->", color="#4338ca", lw=2.2, mutation_scale=15),
            zorder=3
        )

    # Annotate labels
    for i, label in enumerate(labels):
        offset = (8, 8) if i % 2 == 0 else (-15, -18)
        plt.annotate(
            label,
            (pca_coords[i, 0], pca_coords[i, 1]),
            textcoords="offset points",
            xytext=offset,
            fontweight="bold" if "Composite" in label or "Goal" in label else "normal",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="#f8fafc", ec="#94a3b8", alpha=0.9)
        )

    plt.title("Vector Space Composition Trajectory: $C_1 \\to C_2 \\to C_3$ Sequence", fontsize=13, fontweight="bold")
    plt.xlabel("Principal Component 1 (State Transformation Projection)", fontsize=11)
    plt.ylabel("Principal Component 2 (Precondition / Context Projection)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_alternative_implementations(
    labels: List[str],
    func_sims: List[float],
    impl_sims: List[float],
    latencies: List[float],
    costs: List[float],
    save_path: str
) -> None:
    """
    Plots multi-facet comparison of alternative implementations (Experiment 3).
    Shows identical functional effect alongside distinguishable mechanism and operational vectors.
    """
    x = np.arange(len(labels))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(10, 6))

    rects1 = ax1.bar(x - width/2, func_sims, width, label="Functional Similarity to API", color="#3b82f6")
    rects2 = ax1.bar(x + width/2, impl_sims, width, label="Implementation Subspace Similarity", color="#f97316")

    ax1.set_ylabel("Cosine Similarity Score [0.0, 1.0]", fontsize=11)
    ax1.set_title("Alternative Implementations: Functional Equivalence vs. Implementation Distinguishability",
                  fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=10)
    ax1.set_ylim(0, 1.25)
    ax1.legend(loc="upper right")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    # Value labels
    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f"{h:.2f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f"{h:.2f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_goal_relevance_ranking(
    labels: List[str],
    relevance_scores: List[float],
    save_path: str
) -> None:
    """
    Plots bar chart ranking capabilities by their goal relevance score (Experiment 4).
    """
    colors = ["#10b981" if s > 0.1 else ("#ef4444" if s < -0.05 else "#94a3b8") for s in relevance_scores]

    plt.figure(figsize=(10, 6))
    bars = plt.barh(labels, relevance_scores, color=colors, edgecolor="black", height=0.6)
    plt.axvline(0, color="black", linestyle="-", linewidth=1.2)

    plt.title("Goal Relevance Filtering and Ranking: $Rel_{goal}(C, G, S_I)$", fontsize=13, fontweight="bold")
    plt.xlabel("Directional Alignment Score with Goal Delta", fontsize=11)
    plt.xlim(-0.5, 1.1)
    plt.grid(axis="x", linestyle="--", alpha=0.5)

    for bar in bars:
        w = bar.get_width()
        x_pos = w + (0.03 if w >= 0 else -0.08)
        plt.text(x_pos, bar.get_y() + bar.get_height()/2, f"{w:.2f}",
                 va="center", ha="left" if w >= 0 else "right", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_operational_pareto_frontier(
    latencies: List[float],
    costs: List[float],
    reliabilities: List[float],
    labels: List[str],
    pareto_mask: np.ndarray,
    save_path: str
) -> None:
    """
    Plots operational attribute trade-offs (Latency vs. Cost) with reliability bubbles (Experiment 5).
    Highlights Pareto-optimal capabilities.
    """
    plt.figure(figsize=(10, 7))

    bubble_sizes = [float(r * 400.0) for r in reliabilities]

    # Non-Pareto points
    non_pareto = ~pareto_mask
    if np.any(non_pareto):
        plt.scatter(
            [latencies[i] for i in range(len(latencies)) if non_pareto[i]],
            [costs[i] for i in range(len(costs)) if non_pareto[i]],
            s=[bubble_sizes[i] for i in range(len(bubble_sizes)) if non_pareto[i]],
            c="#cbd5e1", edgecolors="#64748b", alpha=0.7, label="Dominated Capabilities", zorder=3
        )

    # Pareto points
    if np.any(pareto_mask):
        p_lat = [latencies[i] for i in range(len(latencies)) if pareto_mask[i]]
        p_cost = [costs[i] for i in range(len(costs)) if pareto_mask[i]]
        p_sz = [bubble_sizes[i] for i in range(len(bubble_sizes)) if pareto_mask[i]]

        plt.scatter(
            p_lat, p_cost, s=p_sz,
            c="#3b82f6", edgecolors="#1d4ed8", linewidths=2, alpha=0.9, label="Pareto-Optimal Frontier", zorder=4
        )

        # Connect Pareto frontier line
        sorted_pairs = sorted(zip(p_lat, p_cost), key=lambda x: x[0])
        plt.plot([p[0] for p in sorted_pairs], [p[1] for p in sorted_pairs],
                 color="#2563eb", linestyle="--", lw=2, zorder=2)

    # Annotate labels
    for i, label in enumerate(labels):
        plt.annotate(
            f"{label}\n(Rel={reliabilities[i]:.2f})",
            (latencies[i], costs[i]),
            textcoords="offset points",
            xytext=(10, 5),
            fontsize=8,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#94a3b8", alpha=0.8)
        )

    plt.title("Operational Multi-Objective Space: Latency vs. Monetary Cost", fontsize=13, fontweight="bold")
    plt.xlabel("Execution Latency (ms) [lower is better]", fontsize=11)
    plt.ylabel("Monetary Cost ($) [lower is better]", fontsize=11)
    plt.legend(loc="upper right")
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
