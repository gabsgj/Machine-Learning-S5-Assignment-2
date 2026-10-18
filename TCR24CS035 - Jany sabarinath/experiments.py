import json
import pandas as pd
import numpy as np

from embedding import (
    encode_capability,
    similarity,
    compatibility,
    input_output_compatibility,
    compose
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_capabilities():

    with open(
        "data/capabilities.json",
        "r"
    ) as file:

        return json.load(file)


# ---------------------------------------------------------
# FIND CAPABILITY
# ---------------------------------------------------------

def find_capability(capabilities, name):

    for capability in capabilities:

        if capability["name"] == name:
            return capability

    return None


# ---------------------------------------------------------
# EXPERIMENT 1
# CAPABILITY COMPATIBILITY
# ---------------------------------------------------------

def experiment_1(capabilities):

    print("\n")
    print("=" * 60)
    print("EXPERIMENT 1: CAPABILITY COMPATIBILITY")
    print("=" * 60)

    create_order = find_capability(
        capabilities,
        "CreateOrder"
    )

    make_payment = find_capability(
        capabilities,
        "MakePayment"
    )

    cancel_cart = find_capability(
        capabilities,
        "CancelCart"
    )

    # CreateOrder -> MakePayment
    score1 = compatibility(
        create_order,
        make_payment
    )

    # CreateOrder -> CancelCart
    score2 = compatibility(
        create_order,
        cancel_cart
    )

    print(
        "CreateOrder -> MakePayment:",
        score1
    )

    print(
        "CreateOrder -> CancelCart:",
        score2
    )

    results = pd.DataFrame({

        "Capability 1": [
            "CreateOrder",
            "CreateOrder"
        ],

        "Capability 2": [
            "MakePayment",
            "CancelCart"
        ],

        "Compatibility Score": [
            score1,
            score2
        ],

        "Expected": [
            "Compatible",
            "Incompatible"
        ]
    })

    results.to_csv(
        "results/compatibility_results.csv",
        index=False
    )


# ---------------------------------------------------------
# EXPERIMENT 2
# CAPABILITY COMPOSITION
# ---------------------------------------------------------

def experiment_2(capabilities):

    print("\n")
    print("=" * 60)
    print("EXPERIMENT 2: CAPABILITY COMPOSITION")
    print("=" * 60)

    create_order = find_capability(
        capabilities,
        "CreateOrder"
    )

    make_payment = find_capability(
        capabilities,
        "MakePayment"
    )

    send_notification = find_capability(
        capabilities,
        "SendNotification"
    )

    # Check compatibility
    c1 = compatibility(
        create_order,
        make_payment
    )

    c2 = compatibility(
        make_payment,
        send_notification
    )

    print(
        "CreateOrder -> MakePayment:",
        c1
    )

    print(
        "MakePayment -> SendNotification:",
        c2
    )

    # Create composite capability
    composite = compose([
        create_order,
        make_payment,
        send_notification
    ])

    print("\nComposite Capability")

    print("Name:", composite["name"])

    print(
        "Inputs:",
        composite["inputs"]
    )

    print(
        "Outputs:",
        composite["outputs"]
    )

    print(
        "Effects:",
        composite["effects"]
    )

    print(
        "Cost:",
        composite["cost"]
    )

    print(
        "Reliability:",
        composite["reliability"]
    )

    # Encode capabilities
    v1 = encode_capability(
        create_order
    )

    v2 = encode_capability(
        make_payment
    )

    v3 = encode_capability(
        send_notification
    )

    vc = encode_capability(
        composite
    )

    print("\nVector dimensions:")
    print("CreateOrder:", len(v1))
    print("MakePayment:", len(v2))
    print("SendNotification:", len(v3))
    print("Composite:", len(vc))

    results = pd.DataFrame({

        "Capability": [
            "CreateOrder",
            "MakePayment",
            "SendNotification"
        ],

        "Similarity with Composite": [
            similarity(v1, vc),
            similarity(v2, vc),
            similarity(v3, vc)
        ]
    })

    results.to_csv(
        "results/composition_results.csv",
        index=False
    )


# ---------------------------------------------------------
# EXPERIMENT 3
# ALTERNATIVE IMPLEMENTATIONS
# ---------------------------------------------------------

def experiment_3(capabilities):

    print("\n")
    print("=" * 60)
    print("EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS")
    print("=" * 60)

    api = find_capability(
        capabilities,
        "CreateOrder"
    )

    database = find_capability(
        capabilities,
        "CreateOrderDatabase"
    )

    gui = find_capability(
        capabilities,
        "CreateOrderGUI"
    )

    v_api = encode_capability(api)
    v_database = encode_capability(database)
    v_gui = encode_capability(gui)

    print(
        "API vs Database:",
        similarity(v_api, v_database)
    )

    print(
        "API vs GUI:",
        similarity(v_api, v_gui)
    )

    print(
        "Database vs GUI:",
        similarity(v_database, v_gui)
    )


# ---------------------------------------------------------
# EXPERIMENT 4
# IRRELEVANT CAPABILITY
# ---------------------------------------------------------

def experiment_4(capabilities):

    print("\n")
    print("=" * 60)
    print("EXPERIMENT 4: IRRELEVANT CAPABILITY")
    print("=" * 60)

    create_order = find_capability(
        capabilities,
        "CreateOrder"
    )

    report = find_capability(
        capabilities,
        "GenerateMonthlyReport"
    )

    v1 = encode_capability(
        create_order
    )

    v2 = encode_capability(
        report
    )

    score = similarity(
        v1,
        v2
    )

    print(
        "CreateOrder vs GenerateMonthlyReport:",
        score
    )


# ---------------------------------------------------------
# EXPERIMENT 5
# OPERATIONAL ATTRIBUTES
# ---------------------------------------------------------

def experiment_5(capabilities):

    print("\n")
    print("=" * 60)
    print("EXPERIMENT 5: OPERATIONAL ATTRIBUTES")
    print("=" * 60)

    for capability in capabilities:

        print(
            capability["name"],
            "| Cost:",
            capability["cost"],
            "| Reliability:",
            capability["reliability"]
        )


# ---------------------------------------------------------
# RUN ALL EXPERIMENTS
# ---------------------------------------------------------

def run_all_experiments():

    capabilities = load_capabilities()

    experiment_1(capabilities)

    experiment_2(capabilities)

    experiment_3(capabilities)

    experiment_4(capabilities)

    experiment_5(capabilities)


if __name__ == "__main__":

    run_all_experiments()