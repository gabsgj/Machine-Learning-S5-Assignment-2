from src.main import load_application, find_capability
from src.embedding import encode_capability, cosine_similarity
from src.compatibility import are_compatible
from src.composition import compose_capabilities


def get_capabilities():
    _, goal, capabilities = load_application()

    return (
        goal,
        find_capability(capabilities, "CreateOrder"),
        find_capability(capabilities, "MakePayment"),
        find_capability(capabilities, "SendNotification"),
        find_capability(capabilities, "CancelCart"),
        find_capability(capabilities, "SendEmailConfirmation"),
        find_capability(capabilities, "UpdateUserProfile"),
    )


def test_capability_vectors_have_same_length():
    _, create_order, make_payment, send_notification, cancel_cart, send_email, update_profile = get_capabilities()

    vectors = [
        encode_capability(create_order),
        encode_capability(make_payment),
        encode_capability(send_notification),
        encode_capability(cancel_cart),
        encode_capability(send_email),
        encode_capability(update_profile),
    ]

    lengths = [len(vector) for vector in vectors]

    assert len(set(lengths)) == 1


def test_compatible_capability_pair():
    _, create_order, make_payment, _, _, _, _ = get_capabilities()

    assert are_compatible(
        create_order,
        make_payment
    ) is True


def test_incompatible_capability_pair():
    _, create_order, _, _, cancel_cart, _, _ = get_capabilities()

    assert are_compatible(
        create_order,
        cancel_cart
    ) is False


def test_alternative_implementations_are_similar():
    _, _, _, send_notification, _, send_email, _ = get_capabilities()

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

    assert similarity > 0.9


def test_capability_composition():
    _, create_order, make_payment, send_notification, _, _, _ = get_capabilities()

    composite = compose_capabilities([
        create_order,
        make_payment,
        send_notification,
    ])

    assert composite.cost == 6.0
    assert composite.availability == 1.0

    assert abs(
        composite.reliability - 0.912285
    ) < 0.000001


def test_composite_achieves_goal():
    goal, create_order, make_payment, send_notification, _, _, _ = get_capabilities()

    composite = compose_capabilities([
        create_order,
        make_payment,
        send_notification,
    ])

    for key, required_value in goal.conditions.items():
        assert composite.effects.get(key) == required_value


def test_irrelevant_capability_does_not_contribute_to_goal():
    goal, _, _, _, _, _, update_profile = get_capabilities()

    goal_keys = set(goal.conditions.keys())
    profile_effects = set(update_profile.effects.keys())

    relevant_effects = goal_keys.intersection(
        profile_effects
    )

    assert relevant_effects == set()
