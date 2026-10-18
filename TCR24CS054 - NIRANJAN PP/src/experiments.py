from .main import load_application, find_capability
from .embedding import encode_capability, cosine_similarity
from .compatibility import are_compatible
from .composition import compose_capabilities


def run_experiments():
    """
    Run the formal experiments for the capability-composition study.
    """

    _, goal, capabilities = load_application()

    create_order = find_capability(
        capabilities, "CreateOrder"
    )

    make_payment = find_capability(
        capabilities, "MakePayment"
    )

    send_notification = find_capability(
        capabilities, "SendNotification"
    )

    cancel_cart = find_capability(
        capabilities, "CancelCart"
    )

    send_email = find_capability(
        capabilities, "SendEmailConfirmation"
    )

    update_profile = find_capability(
        capabilities, "UpdateUserProfile"
    )

    print("=" * 60)
    print("FORMAL EXPERIMENTS")
    print("=" * 60)

    # ---------------------------------------------------------
    # Experiment 1: Capability compatibility
    # ---------------------------------------------------------

    print()
    print("Experiment 1: Capability compatibility")

    result_1 = are_compatible(
        create_order,
        make_payment
    )

    result_2 = are_compatible(
        create_order,
        cancel_cart
    )

    print(
        f"CreateOrder -> MakePayment: {result_1}"
    )

    print(
        f"CreateOrder -> CancelCart: {result_2}"
    )

    # ---------------------------------------------------------
    # Experiment 2: Capability composition
    # ---------------------------------------------------------

    print()
    print("Experiment 2: Capability composition")

    sequence = [
        create_order,
        make_payment,
        send_notification,
    ]

    composite = compose_capabilities(sequence)

    print(
        f"Composite: {composite.name}"
    )

    print(
        f"Cost: {composite.cost:.4f}"
    )

    print(
        f"Reliability: "
        f"{composite.reliability:.4f}"
    )

    print(
        f"Availability: "
        f"{composite.availability:.4f}"
    )

    # ---------------------------------------------------------
    # Goal verification
    # ---------------------------------------------------------

    print()
    print("Composite goal verification")

    goal_achieved = True

    for key, required_value in goal.conditions.items():

        produced_value = composite.effects.get(key)

        if produced_value != required_value:
            goal_achieved = False

        print(
            f"{key}: "
            f"required={required_value}, "
            f"produced={produced_value}"
        )

    print(
        f"Goal achieved: {goal_achieved}"
    )

    # ---------------------------------------------------------
    # Experiment 3: Alternative implementations
    # ---------------------------------------------------------

    print()
    print("Experiment 3: Alternative implementations")

    notification_vector = encode_capability(
        send_notification
    )

    email_vector = encode_capability(
        send_email
    )

    similarity = cosine_similarity(
        notification_vector,
        email_vector
    )

    print(
        "SendNotification <-> "
        f"SendEmailConfirmation: "
        f"{similarity:.4f}"
    )

    # ---------------------------------------------------------
    # Experiment 4: Irrelevant capability
    # ---------------------------------------------------------

    print()
    print("Experiment 4: Irrelevant capability")

    print(
        "Testing whether UpdateUserProfile contributes "
        "to the purchase goal."
    )

    goal_keys = set(
        goal.conditions.keys()
    )

    profile_effect_keys = set(
        update_profile.effects.keys()
    )

    relevant_effects = goal_keys.intersection(
        profile_effect_keys
    )

    print(
        f"Goal conditions: "
        f"{sorted(goal_keys)}"
    )

    print(
        f"UpdateUserProfile effects: "
        f"{sorted(profile_effect_keys)}"
    )

    print(
        f"Effects relevant to goal: "
        f"{sorted(relevant_effects)}"
    )

    if len(relevant_effects) == 0:
        print(
            "UpdateUserProfile contributes to goal: False"
        )
    else:
        print(
            "UpdateUserProfile contributes to goal: True"
        )

    # ---------------------------------------------------------
    # Experiment 5: Operational attributes
    # ---------------------------------------------------------

    print()
    print("Experiment 5: Operational attributes")

    print()
    print("Individual capabilities:")

    selected_capabilities = [
        create_order,
        make_payment,
        send_notification,
    ]

    for capability in selected_capabilities:

        print(
            f"{capability.name}: "
            f"cost={capability.cost:.4f}, "
            f"reliability={capability.reliability:.4f}, "
            f"availability={capability.availability:.4f}"
        )

    print()
    print("Composite capability:")

    print(
        f"Cost: {composite.cost:.4f}"
    )

    print(
        f"Reliability: "
        f"{composite.reliability:.4f}"
    )

    print(
        f"Availability: "
        f"{composite.availability:.4f}"
    )

    print()
    print("=" * 60)


if __name__ == "__main__":
    run_experiments()
