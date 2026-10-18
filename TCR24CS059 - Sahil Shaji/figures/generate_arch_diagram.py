"""
Script to generate the System Architecture Diagram for the Technical Report and README.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def generate_architecture_diagram(output_path: str = "figures/architecture_diagram.png"):
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    # Background canvas
    fig.patch.set_facecolor("#ffffff")

    # Title
    ax.text(7.0, 8.1, "Multi-Faceted Compositional Vector Embedding Architecture (MFCE)",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#1e293b")
    ax.text(7.0, 7.7, "Preserving Functional Transformations, Precondition Algebra, and Multi-Objective Quality",
            ha="center", va="center", fontsize=11, color="#64748b")

    # Block 1: Formal Entity Inputs
    box_inputs = patches.FancyBboxPatch((0.5, 3.8), 3.2, 3.2, boxstyle="round,pad=0.2",
                                        facecolor="#f1f5f9", edgecolor="#94a3b8", linewidth=1.5)
    ax.add_patch(box_inputs)
    ax.text(2.1, 6.7, "Formal Specification", ha="center", fontsize=12, fontweight="bold", color="#0f172a")

    ax.text(0.8, 6.1, "• State: S = {(x_i, v_i)}", fontsize=10, color="#334155")
    ax.text(0.8, 5.6, "• Goal: G = {g_1, ..., g_m}", fontsize=10, color="#334155")
    ax.text(0.8, 5.1, "• Capability: C_i = (T, I, O, P,", fontsize=10, color="#334155")
    ax.text(1.0, 4.7, "    E, K, R, Q, Rel, A, M)", fontsize=10, color="#334155")
    ax.text(0.8, 4.2, "• Composition: C_2 o C_1", fontsize=10, color="#334155")

    # Arrow 1: Inputs -> Encoder
    ax.annotate("", xy=(4.3, 5.4), xytext=(3.7, 5.4),
                arrowprops=dict(arrowstyle="->", color="#3b82f6", lw=2.5, mutation_scale=15))
    ax.text(4.0, 5.7, "encode()", ha="center", fontsize=9, fontweight="bold", color="#2563eb")

    # Block 2: Multi-Faceted Vector Space R^D
    box_embed = patches.FancyBboxPatch((4.5, 1.2), 5.2, 5.8, boxstyle="round,pad=0.2",
                                       facecolor="#f8fafc", edgecolor="#3b82f6", linewidth=2.0)
    ax.add_patch(box_embed)
    ax.text(7.1, 6.7, "Multi-Faceted Embedding Space R^D", ha="center", fontsize=12, fontweight="bold", color="#1d4ed8")

    # Subspaces inside R^D
    subspaces = [
        ("Precondition Subspace z_req", "[p_1..p_n || m_p1..m_pn]", "#dbeafe", "#1e40af", 5.8),
        ("Effect / Delta Subspace z_eff", "[e_1..e_n || m_e1..m_en] => delta_E", "#dcfce7", "#166534", 4.9),
        ("Input-Output Subspace z_io", "[z_in || z_out] (Dataflow Hash)", "#fef3c7", "#92400e", 4.0),
        ("Operational Subspace z_ops", "[T, C_$, -log(Rel), -log(Avail), Risk, R]", "#fee2e2", "#991b1b", 3.1),
        ("Implementation Subspace z_impl", "[Type One-Hot || Mech Hash]", "#f3e8ff", "#6b21a8", 2.2),
    ]

    for title, desc, fc, ec, y_pos in subspaces:
        box_sub = patches.FancyBboxPatch((4.8, y_pos - 0.35), 4.6, 0.7, boxstyle="round,pad=0.1",
                                         facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(box_sub)
        ax.text(5.0, y_pos + 0.1, title, fontsize=9.5, fontweight="bold", color=ec)
        ax.text(5.0, y_pos - 0.18, desc, fontsize=8.5, color="#334155")

    # Arrow 2: Vector Space -> Composition & Reasoning Engine
    ax.annotate("", xy=(10.3, 5.4), xytext=(9.7, 5.4),
                arrowprops=dict(arrowstyle="->", color="#3b82f6", lw=2.5, mutation_scale=15))
    ax.text(10.0, 5.7, "Algebraic Ops", ha="center", fontsize=9, fontweight="bold", color="#2563eb")

    # Block 3: Vector Reasoning & Composition Operations
    box_ops = patches.FancyBboxPatch((10.5, 3.8), 3.0, 3.2, boxstyle="round,pad=0.2",
                                     facecolor="#f1f5f9", edgecolor="#94a3b8", linewidth=1.5)
    ax.add_patch(box_ops)
    ax.text(12.0, 6.7, "Vector Operators", ha="center", fontsize=12, fontweight="bold", color="#0f172a")

    ax.text(10.7, 6.1, "• compose(z_1, z_2)", fontsize=9.5, fontweight="bold", color="#4338ca")
    ax.text(10.9, 5.7, "  - Effect masking", fontsize=8.5, color="#475569")
    ax.text(10.9, 5.4, "  - Weakest precond", fontsize=8.5, color="#475569")
    ax.text(10.9, 5.1, "  - Additive log-ops", fontsize=8.5, color="#475569")
    ax.text(10.7, 4.6, "• composability(z_1, z_2)", fontsize=9.5, fontweight="bold", color="#047857")
    ax.text(10.7, 4.1, "• similarity(z_1, z_2)", fontsize=9.5, fontweight="bold", color="#b45309")

    # Bottom Applications Box
    box_apps = patches.FancyBboxPatch((10.5, 1.2), 3.0, 2.2, boxstyle="round,pad=0.2",
                                      facecolor="#ecfdf5", edgecolor="#10b981", linewidth=1.5)
    ax.add_patch(box_apps)
    ax.text(12.0, 3.0, "Downstream Tasks", ha="center", fontsize=11, fontweight="bold", color="#065f46")
    ax.text(10.7, 2.5, "• Goal Relevance Filtering", fontsize=9, color="#047857")
    ax.text(10.7, 2.1, "• Pareto Multi-Objective", fontsize=9, color="#047857")
    ax.text(10.7, 1.7, "• Composite Service Synthesis", fontsize=9, color="#047857")

    # Arrow between Operators and Downstream
    ax.annotate("", xy=(12.0, 3.4), xytext=(12.0, 3.8),
                arrowprops=dict(arrowstyle="->", color="#10b981", lw=2, mutation_scale=12))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated architecture diagram at {output_path}")


if __name__ == "__main__":
    generate_architecture_diagram()
