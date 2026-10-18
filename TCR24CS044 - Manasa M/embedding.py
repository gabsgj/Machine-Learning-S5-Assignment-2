import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


CAPABILITY_TYPES = [
    "API",
    "DATABASE",
    "GUI",
    "EVENT",
    "FUNCTION",
    "FILE",
    "COMPUTATION",
    "MESSAGE",
    "SERVICE"
]


FEATURES = [
    "Cart.exists",
    "Cart.item_count_positive",
    "Inventory.available",
    "Order.exists",
    "Order.status.CREATED",
    "Payment.status.SUCCESS",
    "Notification.sent",
    "User.authenticated",
    "Cart.cancelled",
    "Product.search_completed"
]


def encode_state(state):

    vector = []

    for feature in FEATURES:

        value = state.get(feature, False)

        if isinstance(value, bool):
            vector.append(1.0 if value else 0.0)

        elif isinstance(value, str):
            vector.append(1.0 if value else 0.0)

        else:
            vector.append(float(value))

    return np.array(vector, dtype=float)


def encode_goal(goal):

    vector = []

    for feature in FEATURES:

        value = goal.get(feature, False)

        if isinstance(value, bool):
            vector.append(1.0 if value else 0.0)

        elif isinstance(value, str):
            vector.append(1.0 if value else 0.0)

        else:
            vector.append(float(value))

    return np.array(vector, dtype=float)


def encode_capability(capability):

    vector = []

    # Capability type
    for capability_type in CAPABILITY_TYPES:
        vector.append(
            1.0 if capability.capability_type == capability_type else 0.0
        )

    # Preconditions
    for feature in FEATURES:
        vector.append(
            1.0 if feature in capability.preconditions else 0.0
        )

    # Effects
    for feature in FEATURES:
        vector.append(
            1.0 if feature in capability.effects else 0.0
        )

    # Operational properties
    vector.append(capability.cost)
    vector.append(capability.reliability)
    vector.append(float(capability.availability))

    return np.array(vector, dtype=float)


def similarity(vector1, vector2):

    return float(
        cosine_similarity(
            [vector1],
            [vector2]
        )[0][0]
    )