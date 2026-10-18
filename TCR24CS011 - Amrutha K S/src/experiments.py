import csv
import os
import matplotlib.pyplot as plt

from .compatibility import (
    cosine_similarity,
    compatibility_score,
    is_composable
)

from .composition import (
    compose_capabilities,
    compose_vectors
)


def run_all(capabilities, encoder, results_dir="results"):

    os.makedirs(results_dir, exist_ok=True)

    # ---------------------------------------------------------
    # Load capabilities
    # ---------------------------------------------------------

    c1 = capabilities["C1"]   # CreateOrder
    c2 = capabilities["C2"]   # MakePayment
    c3 = capabilities["C3"]   # CancelCart
    c4 = capabilities["C4"]   # SendNotification
    c5 = capabilities["C5"]   # CreateOrderDatabase
    c6 = capabilities["C6"]   # CreateOrderGUI

    # =========================================================
    # EXPERIMENT 1
    # Capability Compatibility
    # =========================================================

    compatibility_rows = []

    pairs = [
        (c1, c2),   # CreateOrder -> MakePayment
        (c1, c3),   # CreateOrder -> CancelCart
        (c2, c4)    # MakePayment -> SendNotification
    ]

    for first, second in pairs:

        vector_first = encoder.encode_capability(first)
        vector_second = encoder.encode_capability(second)

        compatibility_rows.append({
            "first": first.name,
            "second": second.name,

            "cosine_similarity": cosine_similarity(
                vector_first,
                vector_second
            ),

            "compatibility_score": compatibility_score(
                first,
                second
            ),

            "composable": is_composable(
                first,
                second
            )
        })

    _write_csv(
        os.path.join(
            results_dir,
            "compatibility_results.csv"
        ),
        compatibility_rows
    )

    _bar(
        [
            r["first"] + " -> " + r["second"]
            for r in compatibility_rows
        ],

        [
            r["compatibility_score"]
            for r in compatibility_rows
        ],

        "Compatibility score",
        "Capability pair",

        os.path.join(
            results_dir,
            "compatibility_plot.png"
        )
    )

    # =========================================================
    # EXPERIMENT 2
    # Three-Capability Composition
    #
    # CreateOrder
    #      ->
    # MakePayment
    #      ->
    # SendNotification
    #
    # CompletePurchase =
    # SendNotification o MakePayment o CreateOrder
    # =========================================================

    composition_capabilities = [
        c1,
        c2,
        c4
    ]

    composite = compose_capabilities(
        composition_capabilities
    )

    composite_vector = compose_vectors(
        composition_capabilities,
        encoder
    )

    composition_rows = []

    for capability in composition_capabilities:

        capability_vector = encoder.encode_capability(
            capability
        )

        composition_rows.append({
            "composite": composite.name,
            "atomic_capability": capability.name,
            "similarity_to_composite": cosine_similarity(
                composite_vector,
                capability_vector
            )
        })

    _write_csv(
        os.path.join(
            results_dir,
            "composition_results.csv"
        ),
        composition_rows
    )

    _bar(
        [
            row["atomic_capability"]
            for row in composition_rows
        ],

        [
            row["similarity_to_composite"]
            for row in composition_rows
        ],

        "Similarity to composite",
        "Atomic capability",

        os.path.join(
            results_dir,
            "composition_plot.png"
        )
    )

    # =========================================================
    # EXPERIMENT 3
    # Alternative Implementations
    #
    # CreateOrder
    # CreateOrderDatabase
    # CreateOrderGUI
    # =========================================================

    similarity_rows = []

    alternative_pairs = [
        (c1, c5),
        (c1, c6),
        (c5, c6)
    ]

    for first, second in alternative_pairs:

        vector_first = encoder.encode_capability(
            first
        )

        vector_second = encoder.encode_capability(
            second
        )

        similarity_rows.append({
            "first": first.name,
            "second": second.name,

            "cosine_similarity": cosine_similarity(
                vector_first,
                vector_second
            )
        })

    _write_csv(
        os.path.join(
            results_dir,
            "similarity_results.csv"
        ),
        similarity_rows
    )

    _bar(
        [
            r["first"] + " vs " + r["second"]
            for r in similarity_rows
        ],

        [
            r["cosine_similarity"]
            for r in similarity_rows
        ],

        "Cosine similarity",
        "Capability pair",

        os.path.join(
            results_dir,
            "similarity_plot.png"
        )
    )

    # =========================================================
    # EXPERIMENT 4
    # Goal Relevance
    # =========================================================

    goal = {
        "Order.exists": True,
        "Payment.status": "SUCCESS",
        "Notification.sent": True
    }

    goal_rows = []

    for capability in capabilities.values():

        relevant_effects = sum(
            1
            for key in capability.effects
            if key in goal
        )

        relevance = (
            relevant_effects /
            len(goal)
        )

        goal_rows.append({
            "capability": capability.name,
            "goal_relevance": relevance
        })

    _write_csv(
        os.path.join(
            results_dir,
            "goal_relevance.csv"
        ),
        goal_rows
    )

    # =========================================================
    # EXPERIMENT 5
    # Operational Attributes
    #
    # Cost
    # Risk
    # Reliability
    # Availability
    # =========================================================

    operational_rows = []

    for capability in capabilities.values():

        total_cost = (
            capability.cost.time
            + capability.cost.resource
            + capability.cost.money
            + capability.cost.risk
            + capability.cost.energy
        )

        operational_rows.append({
            "capability": capability.name,

            "execution_time":
                capability.cost.time,

            "total_cost_index":
                total_cost,

            "risk":
                capability.cost.risk,

            "reliability":
                capability.reliability,

            "availability":
                capability.availability
        })

    _write_csv(
        os.path.join(
            results_dir,
            "operational_results.csv"
        ),
        operational_rows
    )

    return (
        compatibility_rows,
        composition_rows,
        similarity_rows,
        goal_rows,
        operational_rows
    )


# =============================================================
# Helper function: Write CSV
# =============================================================

def _write_csv(path, rows):

    if not rows:
        return

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(rows)


# =============================================================
# Helper function: Create bar graph
# =============================================================

def _bar(
        labels,
        values,
        title,
        xlabel,
        path):

    plt.figure(
        figsize=(9, 5)
    )

    plt.bar(
        labels,
        values
    )

    plt.ylabel(title)
    plt.xlabel(xlabel)
    plt.title(title)

    plt.xticks(
        rotation=20,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=160
    )

    plt.close()