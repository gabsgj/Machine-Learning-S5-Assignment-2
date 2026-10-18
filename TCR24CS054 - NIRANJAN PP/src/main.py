import json
from pathlib import Path

from .model import State, Goal, Capability
from .embedding import (
    encode_state,
    encode_goal,
    encode_capability,
    cosine_similarity,
)
from .compatibility import are_compatible
from .composition import compose_capabilities


def load_application():
    """Load the experimental application from the JSON dataset."""

    project_root = Path(__file__).resolve().parent.parent
    data_file = project_root / "data" / "applications.json"

    with open(data_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    initial_state = State(
        values=data["initial_state"]
    )

    goal = Goal(
        conditions=data["goal"]
    )

    capabilities = []

    for item in data["capabilities"]:
        capability = Capability(
            name=item["name"],
            preconditions=item.get("preconditions", {}),
            effects=item.get("effects", {}),
            inputs=set(item.get("inputs", [])),
            outputs=set(item.get("outputs", [])),
            constraints=set(item.get("constraints", [])),
            resources=set(item.get("resources", [])),
            cost=float(item.get("cost", 0.0)),
            reliability=float(item.get("reliability", 1.0)),
            availability=float(item.get("availability", 1.0)),
        )

        capabilities.append(capability)

    return initial_state, goal, capabilities


def find_capability(capabilities, name):
    """Find a capability by name."""

    for capability in capabilities:
        if capability.name == name:
            return capability

    raise ValueError(
        f"Capability '{name}' was not found."
    )


def main():

    # =========================================================
    # 1. LOAD APPLICATION
    # =========================================================

    state, goal, capabilities = load_application()

    print("=" * 60)
    print("VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
    print("=" * 60)

    print()
    print("Application loaded successfully.")

    # =========================================================
    # 2. ENCODE INITIAL STATE
    # =========================================================

    print()
    print("-" * 60)
    print("INITIAL STATE VECTOR")
    print("-" * 60)

    state_vector = encode_state(state)

    print(state_vector)

    # =========================================================
    # 3. ENCODE GOAL
    # =========================================================

    print()
    print("-" * 60)
    print("GOAL VECTOR")
    print("-" * 60)

    goal_vector = encode_goal(goal)

    print(goal_vector)

    # =========================================================
    # 4. ENCODE CAPABILITIES
    # =========================================================

    print()
    print("-" * 60)
    print("CAPABILITY VECTORS")
    print("-" * 60)

    capability_vectors = {}

    for capability in capabilities:

        vector = encode_capability(capability)

        capability_vectors[capability.name] = vector

        print()
        print(f"{capability.name}:")
        print(vector)

    # =========================================================
    # 5. FIND CAPABILITIES
    # =========================================================

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

    cancel_cart = find_capability(
        capabilities,
        "CancelCart"
    )

    send_email = find_capability(
        capabilities,
        "SendEmailConfirmation"
    )

    # =========================================================
    # 6. SIMILARITY EXPERIMENT
    # =========================================================

    print()
    print("-" * 60)
    print("SIMILARITY EXPERIMENT")
    print("-" * 60)

    similarity_create_payment = cosine_similarity(
        capability_vectors["CreateOrder"],
        capability_vectors["MakePayment"]
    )

    similarity_payment_notification = cosine_similarity(
        capability_vectors["MakePayment"],
        capability_vectors["SendNotification"]
    )

    print(
        f"CreateOrder <-> MakePayment: "
        f"{similarity_create_payment:.4f}"
    )

    print(
        f"MakePayment <-> SendNotification: "
        f"{similarity_payment_notification:.4f}"
    )

    # =========================================================
    # 7. COMPATIBILITY EXPERIMENT
    # =========================================================

    print()
    print("-" * 60)
    print("COMPATIBILITY EXPERIMENT")
    print("-" * 60)

    compatibility_pairs = [
        (create_order, make_payment),
        (make_payment, send_notification),
        (create_order, cancel_cart),
    ]

    for first, second in compatibility_pairs:

        compatible = are_compatible(
            first,
            second
        )

        result = (
            "COMPATIBLE"
            if compatible
            else "INCOMPATIBLE"
        )

        print(
            f"{first.name} -> {second.name}: "
            f"{result}"
        )

    # =========================================================
    # 8. ALTERNATIVE IMPLEMENTATION EXPERIMENT
    # =========================================================

    print()
    print("-" * 60)
    print("ALTERNATIVE IMPLEMENTATION EXPERIMENT")
    print("-" * 60)

    alternative_similarity = cosine_similarity(
        capability_vectors["SendNotification"],
        capability_vectors["SendEmailConfirmation"]
    )

    print(
        "SendNotification <-> "
        f"SendEmailConfirmation: "
        f"{alternative_similarity:.4f}"
    )

    print()
    print(
        "SendNotification and SendEmailConfirmation "
        "have the same functional role of sending a "
        "notification after successful payment."
    )

    # =========================================================
    # 9. CAPABILITY COMPOSITION EXPERIMENT
    # =========================================================

    print()
    print("-" * 60)
    print("CAPABILITY COMPOSITION EXPERIMENT")
    print("-" * 60)

    purchase_sequence = [
        create_order,
        make_payment,
        send_notification,
    ]

    composite = compose_capabilities(
        purchase_sequence
    )

    composite_vector = encode_capability(
        composite
    )

    print()
    print(
        f"Composite capability: "
        f"{composite.name}"
    )

    print(
        f"Total cost: "
        f"{composite.cost:.2f}"
    )

    print(
        f"Cumulative reliability: "
        f"{composite.reliability:.4f}"
    )

    print(
        f"Availability: "
        f"{composite.availability:.2f}"
    )

    print()
    print("Composite resources:")

    for resource in sorted(composite.resources):
        print(f"  - {resource}")

    print()
    print("Composite effects:")

    for key, value in composite.effects.items():
        print(f"  {key}: {value}")

    print()
    print("Composite vector:")
    print(composite_vector)

    # =========================================================
    # 10. COMPOSITE GOAL ACHIEVEMENT
    # =========================================================

    print()
    print("-" * 60)
    print("COMPOSITE GOAL ACHIEVEMENT")
    print("-" * 60)

    goal_satisfied = True

    for key, required_value in goal.conditions.items():

        actual_value = composite.effects.get(key)

        if actual_value != required_value:
            goal_satisfied = False

        print(
            f"{key}: "
            f"required={required_value}, "
            f"produced={actual_value}"
        )

    print()

    if goal_satisfied:
        print(
            "Goal achieved by composite capability: YES"
        )
    else:
        print(
            "Goal achieved by composite capability: NO"
        )

    # =========================================================
    # 11. SUMMARY
    # =========================================================

    print()
    print("=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)

    print()
    print(
        "The application successfully encoded states, "
        "goals and capabilities as fixed-length vectors."
    )

    print(
        "Capability similarity was calculated using "
        "cosine similarity."
    )

    print(
        "Compatibility was determined by checking whether "
        "the effects of one capability satisfy the "
        "preconditions of the next capability."
    )

    print(
        "A compatible sequence of capabilities was "
        "successfully composed into a composite capability."
    )

    print(
        "The composite capability was checked directly "
        "against the goal conditions."
    )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
