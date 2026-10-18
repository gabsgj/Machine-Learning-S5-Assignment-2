import json
import time

from capabilities import create_capabilities
from embedding import (
    encode_state,
    encode_goal,
    encode_capability,
    similarity
)
from composition import (
    check_compatibility,
    compose
)
from evaluation import (
    print_vectors,
    compare_capabilities,
    plot_cost,
    plot_reliability,
    plot_similarity
)


def print_title(title):

    print("\n")
    print("=" * 60)
    print(title)
    print("=" * 60)


def main():

    capabilities = create_capabilities()

    create_order = capabilities[0]
    make_payment = capabilities[1]
    send_notification = capabilities[2]
    cancel_cart = capabilities[3]

    print_title("VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")

    # --------------------------------------------------
    # INITIAL STATE
    # --------------------------------------------------

    initial_state = {
        "Cart.exists": True,
        "Cart.item_count_positive": True,
        "Inventory.available": True,
        "Order.exists": False,
        "Order.status.CREATED": False,
        "Payment.status.SUCCESS": False,
        "Notification.sent": False,
        "User.authenticated": True,
        "Cart.cancelled": False,
        "Product.search_completed": False
    }

    print_title("INITIAL STATE")

    print(initial_state)

    state_vector = encode_state(initial_state)

    print("\nState Vector:")
    print(state_vector)

    # --------------------------------------------------
    # GOAL
    # --------------------------------------------------

    goal = {
        "Order.exists": True,
        "Order.status.CREATED": True,
        "Payment.status.SUCCESS": True,
        "Notification.sent": True
    }

    print_title("GOAL")

    print(goal)

    goal_vector = encode_goal(goal)

    print("\nGoal Vector:")
    print(goal_vector)

    # --------------------------------------------------
    # CAPABILITY VECTORS
    # --------------------------------------------------

    print_title("CAPABILITY VECTORS")

    print_vectors(capabilities)

    # --------------------------------------------------
    # EXPERIMENT 1
    # CAPABILITY COMPATIBILITY
    # --------------------------------------------------

    print_title("EXPERIMENT 1: CAPABILITY COMPATIBILITY")

    result1 = check_compatibility(
        create_order,
        make_payment
    )

    result2 = check_compatibility(
        create_order,
        cancel_cart
    )

    print(
        "CreateOrder -> MakePayment:",
        "Compatible" if result1 else "Incompatible"
    )

    print(
        "CreateOrder -> CancelCart:",
        "Compatible" if result2 else "Incompatible"
    )

    # --------------------------------------------------
    # EXPERIMENT 2
    # CAPABILITY COMPOSITION
    # --------------------------------------------------

    print_title("EXPERIMENT 2: CAPABILITY COMPOSITION")

    chain = [
        create_order,
        make_payment,
        send_notification
    ]

    composite = compose(chain)

    if composite is not None:

        print("Composite Capability Created")

        print(
            "Composition:",
            " -> ".join(composite["components"])
        )

        print(
            "Total Cost:",
            round(composite["cost"], 4)
        )

        print(
            "Combined Reliability:",
            round(composite["reliability"], 4)
        )

        print(
            "Availability:",
            composite["availability"]
        )

    else:

        print("Composition is invalid")

    # --------------------------------------------------
    # EXPERIMENT 3
    # ALTERNATIVE IMPLEMENTATIONS
    # --------------------------------------------------

    print_title("EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS")

    print("API implementation:")
    print("CreateOrder -> Type = API")

    print("\nDatabase implementation:")
    print("CreateOrder -> Type = DATABASE")

    print("\nGUI implementation:")
    print("CreateOrder -> Type = GUI")

    # --------------------------------------------------
    # EXPERIMENT 4
    # IRRELEVANT CAPABILITIES
    # --------------------------------------------------

    print_title("EXPERIMENT 4: IRRELEVANT CAPABILITIES")

    relevant = [
        create_order,
        make_payment,
        send_notification
    ]

    irrelevant = [
        capabilities[4],
        capabilities[5]
    ]

    print("Relevant capabilities:")

    for capability in relevant:
        print("-", capability.name)

    print("\nIrrelevant capabilities:")

    for capability in irrelevant:
        print("-", capability.name)

    # --------------------------------------------------
    # EXPERIMENT 5
    # OPERATIONAL ATTRIBUTES
    # --------------------------------------------------

    print_title("EXPERIMENT 5: OPERATIONAL ATTRIBUTES")

    for capability in capabilities:

        print(
            capability.name,
            "| Cost =",
            capability.cost,
            "| Reliability =",
            capability.reliability,
            "| Availability =",
            capability.availability
        )

    # --------------------------------------------------
    # SIMILARITY
    # --------------------------------------------------

    print_title("CAPABILITY SIMILARITY")

    score1 = compare_capabilities(
        create_order,
        make_payment
    )

    score2 = compare_capabilities(
        create_order,
        cancel_cart
    )

    score3 = compare_capabilities(
        make_payment,
        send_notification
    )

    print(
        "CreateOrder vs MakePayment:",
        round(score1, 4)
    )

    print(
        "CreateOrder vs CancelCart:",
        round(score2, 4)
    )

    print(
        "MakePayment vs SendNotification:",
        round(score3, 4)
    )

    # --------------------------------------------------
    # EFFICIENCY
    # --------------------------------------------------

    print_title("EFFICIENCY")

    start = time.perf_counter()

    for capability in capabilities:

        encode_capability(capability)

    end = time.perf_counter()

    print(
        "Encoding Time:",
        round(end - start, 6),
        "seconds"
    )

    print(
        "Number of Capabilities:",
        len(capabilities)
    )

    print(
        "Vector Dimension:",
        len(encode_capability(capabilities[0]))
    )

    # --------------------------------------------------
    # SAVE DATASET
    # --------------------------------------------------

    dataset = {

        "initial_state": initial_state,

        "goal": goal,

        "capabilities": [
            {
                "name": c.name,
                "type": c.capability_type,
                "inputs": c.inputs,
                "outputs": c.outputs,
                "preconditions": c.preconditions,
                "effects": c.effects,
                "cost": c.cost,
                "reliability": c.reliability,
                "availability": c.availability
            }

            for c in capabilities
        ],

        "composition": [
            "CreateOrder",
            "MakePayment",
            "SendNotification"
        ]
    }

    with open("dataset.json", "w") as file:

        json.dump(
            dataset,
            file,
            indent=4
        )

    print("\nDataset saved to dataset.json")

    # --------------------------------------------------
    # GRAPHS
    # --------------------------------------------------

    plot_cost(capabilities)

    plot_reliability(capabilities)

    plot_similarity(capabilities)

    print("\nGraphs saved in results/")

    print_title("PROGRAM COMPLETED")


if __name__ == "__main__":
    main()