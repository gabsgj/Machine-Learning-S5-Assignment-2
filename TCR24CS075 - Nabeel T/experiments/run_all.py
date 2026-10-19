import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================
# PROJECT PATH
# =============================================================

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT)
)


# =============================================================
# IMPORT PROJECT MODULES
# =============================================================

from src.models import (
    Capability,
    State,
    Goal
)

from src.embedding import (
    CapabilityEmbedding,
    similarity,
    operational_similarity
)

from src.compatibility import (
    compatibility_score,
    is_compatible,
    check_precondition_effect_compatibility,
    check_output_input_compatibility
)

from src.composition import compose


# =============================================================
# FILE PATHS
# =============================================================

DATA_FILE = (
    ROOT
    / "data"
    / "dataset.json"
)

RESULTS_DIR = (
    ROOT
    / "results"
)

FIGURES_DIR = (
    RESULTS_DIR
    / "figures"
)


# =============================================================
# LOAD DATASET
# =============================================================

def load_dataset():

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =============================================================
# CONVERT JSON CAPABILITY TO OBJECT
# =============================================================

def capability_from_dict(data):

    return Capability(
        **data
    )


# =============================================================
# BUILD BASE CAPABILITIES
# =============================================================

def build_base_capabilities(data):

    capabilities = {}

    for item in data["capabilities"]:

        capability = capability_from_dict(
            item
        )

        capabilities[
            capability.name
        ] = capability

    return capabilities


# =============================================================
# SAVE GRAPH
# =============================================================

def save_plot(
    title,
    labels,
    values,
    ylabel,
    filename
):

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.figure(
        figsize=(8, 4.5)
    )

    bars = plt.bar(
        labels,
        values
    )

    plt.ylabel(
        ylabel
    )

    plt.ylim(
        0,
        1.05
    )

    plt.title(
        title
    )

    plt.xticks(
        rotation=20,
        ha="right"
    )

    # Display numerical value above bars
    for bar, value in zip(
        bars,
        values
    ):

        plt.text(
            bar.get_x()
            + bar.get_width() / 2,

            min(
                1.0,
                value
            ) + 0.02,

            f"{value:.3f}",

            ha="center",

            va="bottom",

            fontsize=9
        )

    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR / filename,
        dpi=160
    )

    plt.close()


# =============================================================
# MAIN
# =============================================================

def main():

    # ---------------------------------------------------------
    # Load dataset
    # ---------------------------------------------------------

    data = load_dataset()

    capabilities = (
        build_base_capabilities(
            data
        )
    )

    embedding = CapabilityEmbedding()

    create_order = (
        capabilities["CreateOrder"]
    )

    make_payment = (
        capabilities["MakePayment"]
    )

    send_notification = (
        capabilities["SendNotification"]
    )

    # =========================================================
    # EXPERIMENT 1
    # CAPABILITY COMPATIBILITY
    # =========================================================

    cancel_cart = Capability(

        name="CancelCart",

        capability_type="FUNCTION",

        preconditions={
            "Order.exists": False
        },

        effects={
            "Cart.cancelled": True
        },

        constraints=[
            "Order must not exist"
        ],

        resources=[
            "Database"
        ],

        cost_time=50,

        cost_resource=1,

        cost_money=0.0,

        risk=0.02,

        reliability=0.99,

        availability=0.99,

        execution={
            "function": "cancel_cart"
        }
    )

    compatibility_create_payment = (
        compatibility_score(
            create_order,
            make_payment
        )
    )

    compatibility_create_cancel = (
        compatibility_score(
            create_order,
            cancel_cart
        )
    )

    # =========================================================
    # EXPERIMENT 2
    # CAPABILITY COMPOSITION
    # =========================================================

    composite = compose(
        [
            create_order,
            make_payment,
            send_notification
        ]
    )

    similarity_composite_create = similarity(
        composite,
        create_order,
        embedding
    )

    similarity_composite_payment = similarity(
        composite,
        make_payment,
        embedding
    )

    similarity_composite_notification = similarity(
        composite,
        send_notification,
        embedding
    )

    # =========================================================
    # EXPERIMENT 3
    # ALTERNATIVE IMPLEMENTATIONS
    # =========================================================

    api_payment = Capability(

        name="MakePayment_API",

        capability_type="API",

        inputs=make_payment.inputs,

        outputs=make_payment.outputs,

        preconditions=make_payment.preconditions,

        effects=make_payment.effects,

        constraints=make_payment.constraints,

        resources=make_payment.resources,

        cost_time=200,

        cost_resource=3,

        cost_money=0.05,

        risk=0.10,

        reliability=0.98,

        availability=0.97,

        execution={
            "method": "POST",
            "endpoint": "/payments"
        }
    )

    database_payment = Capability(

        name="MakePayment_DATABASE",

        capability_type="DATABASE",

        inputs=make_payment.inputs,

        outputs=make_payment.outputs,

        preconditions=make_payment.preconditions,

        effects=make_payment.effects,

        constraints=make_payment.constraints,

        resources=[
            "Database"
        ],

        cost_time=50,

        cost_resource=2,

        cost_money=0.00,

        risk=0.05,

        reliability=0.995,

        availability=0.995,

        execution={
            "operation": "UPDATE",
            "table": "payments"
        }
    )

    gui_payment = Capability(

        name="MakePayment_GUI",

        capability_type="GUI",

        inputs=make_payment.inputs,

        outputs=make_payment.outputs,

        preconditions=make_payment.preconditions,

        effects=make_payment.effects,

        constraints=make_payment.constraints,

        resources=[
            "Authentication token",
            "Network"
        ],

        cost_time=350,

        cost_resource=4,

        cost_money=0.05,

        risk=0.15,

        reliability=0.95,

        availability=0.96,

        execution={
            "action": "CLICK",
            "component": "pay_button"
        }
    )

    similarity_api_database = similarity(
        api_payment,
        database_payment,
        embedding
    )

    similarity_api_gui = similarity(
        api_payment,
        gui_payment,
        embedding
    )

    similarity_database_gui = similarity(
        database_payment,
        gui_payment,
        embedding
    )

    # =========================================================
    # EXPERIMENT 4
    # IRRELEVANT CAPABILITIES
    # =========================================================

    play_music = Capability(

        name="PlayMusic",

        capability_type="SERVICE",

        inputs={
            "song_id": {
                "type": "STRING",
                "required": True
            }
        },

        outputs={
            "stream_id": {
                "type": "STRING"
            }
        },

        preconditions={
            "User.authenticated": True
        },

        effects={
            "Music.playing": True
        },

        constraints=[
            "song_available"
        ],

        resources=[
            "Network"
        ],

        cost_time=120,

        cost_resource=2,

        cost_money=0.0,

        risk=0.01,

        reliability=0.99,

        availability=0.99,

        execution={
            "service": "music_service"
        }
    )

    goal_conditions = set(
        data["application"]["goal"].keys()
    )

    goal_relevance = {}

    for capability in [
        create_order,
        make_payment,
        send_notification,
        play_music
    ]:

        contribution = (
            set(
                capability.effects.keys()
            )
            &
            goal_conditions
        )

        goal_relevance[
            capability.name
        ] = int(
            bool(contribution)
        )

    # =========================================================
    # EXPERIMENT 5
    # OPERATIONAL ATTRIBUTES
    # =========================================================

    fast_payment = Capability(

        name="FastPayment",

        capability_type="SERVICE",

        inputs=make_payment.inputs,

        outputs=make_payment.outputs,

        preconditions=make_payment.preconditions,

        effects=make_payment.effects,

        resources=[
            "Payment gateway",
            "Network"
        ],

        cost_time=100,

        cost_resource=2,

        cost_money=0.05,

        risk=0.10,

        reliability=0.99,

        availability=0.99,

        execution={
            "service": "fast_payment"
        }
    )

    slow_payment = Capability(

        name="SlowPayment",

        capability_type="SERVICE",

        inputs=make_payment.inputs,

        outputs=make_payment.outputs,

        preconditions=make_payment.preconditions,

        effects=make_payment.effects,

        resources=[
            "Payment gateway",
            "Network"
        ],

        cost_time=500,

        cost_resource=5,

        cost_money=0.01,

        risk=0.30,

        reliability=0.90,

        availability=0.95,

        execution={
            "service": "slow_payment"
        }
    )

    combined_operational_similarity = similarity(
        fast_payment,
        slow_payment,
        embedding
    )

    pure_operational_similarity = (
        operational_similarity(
            fast_payment,
            slow_payment
        )
    )

    # =========================================================
    # STATE AND GOAL ENCODING
    # =========================================================

    initial_state = State(
        data["application"]["initial_state"]
    )

    goal = Goal(
        data["application"]["goal"]
    )

    state_vector = embedding.encode_state(
        initial_state
    )

    goal_vector = embedding.encode_goal(
        goal
    )

    # =========================================================
    # SAVE RESULTS
    # =========================================================

    rows = [

        [
            "Experiment 1",
            "CreateOrder -> MakePayment",
            "compatibility",
            compatibility_create_payment
        ],

        [
            "Experiment 1",
            "CreateOrder -> CancelCart",
            "compatibility",
            compatibility_create_cancel
        ],

        [
            "Experiment 2",
            "Composite -> CreateOrder",
            "similarity",
            similarity_composite_create
        ],

        [
            "Experiment 2",
            "Composite -> MakePayment",
            "similarity",
            similarity_composite_payment
        ],

        [
            "Experiment 2",
            "Composite -> SendNotification",
            "similarity",
            similarity_composite_notification
        ],

        [
            "Experiment 3",
            "API -> DATABASE",
            "similarity",
            similarity_api_database
        ],

        [
            "Experiment 3",
            "API -> GUI",
            "similarity",
            similarity_api_gui
        ],

        [
            "Experiment 3",
            "DATABASE -> GUI",
            "similarity",
            similarity_database_gui
        ],

        [
            "Experiment 4",
            "CreateOrder",
            "goal_relevance",
            goal_relevance["CreateOrder"]
        ],

        [
            "Experiment 4",
            "MakePayment",
            "goal_relevance",
            goal_relevance["MakePayment"]
        ],

        [
            "Experiment 4",
            "SendNotification",
            "goal_relevance",
            goal_relevance["SendNotification"]
        ],

        [
            "Experiment 4",
            "PlayMusic",
            "goal_relevance",
            goal_relevance["PlayMusic"]
        ],

        [
            "Experiment 5",
            "FastPayment -> SlowPayment",
            "combined_similarity",
            combined_operational_similarity
        ],

        [
            "Experiment 5",
            "FastPayment -> SlowPayment",
            "operational_similarity",
            pure_operational_similarity
        ]
    ]

    results_dataframe = pd.DataFrame(

        rows,

        columns=[
            "experiment",
            "comparison",
            "metric",
            "value"
        ]
    )

    RESULTS_DIR.mkdir(
        exist_ok=True
    )

    results_dataframe.to_csv(
        RESULTS_DIR / "results.csv",
        index=False
    )

    # =========================================================
    # SAVE FIGURES
    # =========================================================

    save_plot(

        "Experiment 1",

        [
            "CreateOrder->MakePayment",
            "CreateOrder->CancelCart"
        ],

        [
            compatibility_create_payment,
            compatibility_create_cancel
        ],

        "Compatibility score",

        "experiment_1.png"
    )

    save_plot(

        "Experiment 2",

        [
            "CreateOrder",
            "MakePayment",
            "SendNotification"
        ],

        [
            similarity_composite_create,
            similarity_composite_payment,
            similarity_composite_notification
        ],

        "Similarity to composite",

        "experiment_2.png"
    )

    save_plot(

        "Experiment 3",

        [
            "API->DATABASE",
            "API->GUI",
            "DATABASE->GUI"
        ],

        [
            similarity_api_database,
            similarity_api_gui,
            similarity_database_gui
        ],

        "Similarity",

        "experiment_3.png"
    )

    save_plot(

        "Experiment 4",

        list(
            goal_relevance.keys()
        ),

        list(
            goal_relevance.values()
        ),

        "Goal relevance",

        "experiment_4.png"
    )

    save_plot(

        "Experiment 5",

        [
            "Combined",
            "Operational only"
        ],

        [
            combined_operational_similarity,
            pure_operational_similarity
        ],

        "Similarity",

        "experiment_5.png"
    )

    # =========================================================
    # TERMINAL OUTPUT
    # =========================================================

    print()
    print("=" * 60)
    print("ASSIGNMENT 2 - FINAL EXPERIMENT RESULTS")
    print("=" * 60)

    print()
    print("Embedding information")
    print("-" * 60)

    print(
        "Capability vector dimension:",
        embedding.DIM
    )

    print(
        "State vector dimension:",
        len(state_vector)
    )

    print(
        "Goal vector dimension:",
        len(goal_vector)
    )

    # ---------------------------------------------------------
    # Experiment 1
    # ---------------------------------------------------------

    print()
    print("EXPERIMENT 1 - CAPABILITY COMPATIBILITY")
    print("-" * 60)

    print(
        "CreateOrder -> MakePayment:"
    )

    print(
        "Compatibility score:",
        f"{compatibility_create_payment:.6f}"
    )

    print(
        "Compatible:",
        is_compatible(
            create_order,
            make_payment
        )
    )

    print()

    print(
        "CreateOrder -> CancelCart:"
    )

    print(
        "Compatibility score:",
        f"{compatibility_create_cancel:.6f}"
    )

    print(
        "Compatible:",
        is_compatible(
            create_order,
            cancel_cart
        )
    )

    # ---------------------------------------------------------
    # Experiment 2
    # ---------------------------------------------------------

    print()
    print("EXPERIMENT 2 - CAPABILITY COMPOSITION")
    print("-" * 60)

    print(
        "Composite:",
        composite.name
    )

    print(
        "Composite effects:",
        composite.effects
    )

    print(
        "Composite resources:",
        composite.resources
    )

    print(
        "Composite reliability:",
        f"{composite.reliability:.6f}"
    )

    print()

    print(
        "Composite vs CreateOrder:",
        f"{similarity_composite_create:.6f}"
    )

    print(
        "Composite vs MakePayment:",
        f"{similarity_composite_payment:.6f}"
    )

    print(
        "Composite vs SendNotification:",
        f"{similarity_composite_notification:.6f}"
    )

    # ---------------------------------------------------------
    # Experiment 3
    # ---------------------------------------------------------

    print()
    print("EXPERIMENT 3 - ALTERNATIVE IMPLEMENTATIONS")
    print("-" * 60)

    print(
        "API vs DATABASE:",
        f"{similarity_api_database:.6f}"
    )

    print(
        "API vs GUI:",
        f"{similarity_api_gui:.6f}"
    )

    print(
        "DATABASE vs GUI:",
        f"{similarity_database_gui:.6f}"
    )

    # ---------------------------------------------------------
    # Experiment 4
    # ---------------------------------------------------------

    print()
    print("EXPERIMENT 4 - IRRELEVANT CAPABILITIES")
    print("-" * 60)

    for name, relevant in goal_relevance.items():

        if relevant:

            print(
                f"{name}: Relevant"
            )

        else:

            print(
                f"{name}: Irrelevant"
            )

    # ---------------------------------------------------------
    # Experiment 5
    # ---------------------------------------------------------

    print()
    print("EXPERIMENT 5 - OPERATIONAL ATTRIBUTES")
    print("-" * 60)

    print(
        "FastPayment vs SlowPayment"
    )

    print(
        "Combined similarity:",
        f"{combined_operational_similarity:.6f}"
    )

    print(
        "Operational similarity:",
        f"{pure_operational_similarity:.6f}"
    )

    # ---------------------------------------------------------
    # Files
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("FILES GENERATED")
    print("=" * 60)

    print(
        "CSV:",
        RESULTS_DIR / "results.csv"
    )

    print(
        "Figures:",
        FIGURES_DIR
    )

    print()
    print("Experiment execution completed successfully.")


# =============================================================
# PROGRAM ENTRY
# =============================================================

if __name__ == "__main__":

    main()