import numpy as np

from .model import State, Goal, Capability


# Fixed feature space for the application.
#
# The logical features are divided into:
#   1. Preconditions
#   2. Effects
#   3. Resources
#   4. Operational attributes
#
# This keeps the different kinds of information explicit.

PRECONDITION_FEATURES = [
    "User.authenticated",
    "Cart.exists",
    "Cart.item_count_positive",
    "Order.exists",
    "Order.status_created",
    "Payment.status_success",
    "Notification.sent",
    "Inventory.available",
]

EFFECT_FEATURES = [
    "User.authenticated",
    "Cart.exists",
    "Cart.item_count_positive",
    "Order.exists",
    "Order.status_created",
    "Payment.status_success",
    "Notification.sent",
    "Inventory.available",
]

RESOURCE_FEATURES = [
    "resource.database",
    "resource.payment_gateway",
    "resource.notification_service",
]


def _condition_value(value):
    """Convert a condition value into a numerical value."""

    if isinstance(value, bool):
        return 1.0 if value else 0.0

    if isinstance(value, (int, float)):
        return float(value)

    return 1.0


def encode_state(state: State) -> np.ndarray:
    """
    Encode a state using the application feature space.
    """

    vector = np.zeros(
        len(PRECONDITION_FEATURES),
        dtype=float
    )

    for key, value in state.values.items():

        if key in PRECONDITION_FEATURES:

            index = PRECONDITION_FEATURES.index(key)

            vector[index] = _condition_value(value)

    return vector


def encode_goal(goal: Goal) -> np.ndarray:
    """
    Encode a goal using the same logical feature space
    as the application state.
    """

    vector = np.zeros(
        len(EFFECT_FEATURES),
        dtype=float
    )

    for key, value in goal.conditions.items():

        if key in EFFECT_FEATURES:

            index = EFFECT_FEATURES.index(key)

            vector[index] = _condition_value(value)

    return vector


def encode_capability(
    capability: Capability
) -> np.ndarray:
    """
    Encode a capability as:

    [preconditions |
     effects |
     resources |
     cost |
     reliability |
     availability]
    """

    vector = np.zeros(
        len(PRECONDITION_FEATURES)
        + len(EFFECT_FEATURES)
        + len(RESOURCE_FEATURES)
        + 3,
        dtype=float
    )

    # ---------------------------------------------------------
    # Preconditions
    # ---------------------------------------------------------

    precondition_offset = 0

    for key, value in capability.preconditions.items():

        if key in PRECONDITION_FEATURES:

            index = PRECONDITION_FEATURES.index(key)

            vector[
                precondition_offset + index
            ] = _condition_value(value)

    # ---------------------------------------------------------
    # Effects
    # ---------------------------------------------------------

    effect_offset = len(PRECONDITION_FEATURES)

    for key, value in capability.effects.items():

        if key in EFFECT_FEATURES:

            index = EFFECT_FEATURES.index(key)

            vector[
                effect_offset + index
            ] = _condition_value(value)

    # ---------------------------------------------------------
    # Resources
    # ---------------------------------------------------------

    resource_offset = (
        len(PRECONDITION_FEATURES)
        + len(EFFECT_FEATURES)
    )

    for resource in capability.resources:

        key = f"resource.{resource}"

        if key in RESOURCE_FEATURES:

            index = RESOURCE_FEATURES.index(key)

            vector[
                resource_offset + index
            ] = 1.0

    # ---------------------------------------------------------
    # Operational attributes
    # ---------------------------------------------------------

    operational_offset = resource_offset + len(
        RESOURCE_FEATURES
    )

    vector[operational_offset] = capability.cost

    vector[operational_offset + 1] = (
        capability.reliability
    )

    vector[operational_offset + 2] = (
        capability.availability
    )

    return vector


def cosine_similarity(
    vector_a: np.ndarray,
    vector_b: np.ndarray
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(
        np.dot(vector_a, vector_b)
        / (norm_a * norm_b)
    )
