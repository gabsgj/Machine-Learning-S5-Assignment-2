import numpy as np


# ---------------------------------------------------------
# 1. VOCABULARY
# ---------------------------------------------------------

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
    # State / condition features
    "Cart.exists=true",
    "Cart.exists=false",
    "Cart.item_count>0",
    "Inventory.available=true",

    "Order.exists=true",
    "Order.exists=false",
    "Order.status=CREATED",

    "Payment.status=SUCCESS",
    "Payment.status=NOT_STARTED",

    "Notification.sent=true",
    "Report.generated=true",

    "sales_data_available=true",

    # Input / output features
    "cart_id",
    "order_id",
    "payment_id",
    "notification_id",
    "sales_data",
    "report",

    # Resources
    "Database",
    "Authentication token",
    "Payment gateway",
    "Network",
    "External service",
    "User interface",
    "CPU"
]


# ---------------------------------------------------------
# 2. HELPER FUNCTION
# ---------------------------------------------------------

def vector_from_items(items, vocabulary):
    """
    Converts a list of items into a binary vector.

    If an item exists in the vocabulary -> 1
    Otherwise -> 0
    """

    vector = []

    for word in vocabulary:
        if word in items:
            vector.append(1)
        else:
            vector.append(0)

    return vector


# ---------------------------------------------------------
# 3. ENCODE STATE
# ---------------------------------------------------------

def encode_state(state):
    """
    Encodes an application state into a numerical vector.
    """

    vector = []

    for feature in FEATURES:

        if feature in state:
            vector.append(1)
        else:
            vector.append(0)

    return np.array(vector, dtype=float)


# ---------------------------------------------------------
# 4. ENCODE GOAL
# ---------------------------------------------------------

def encode_goal(goal):
    """
    Encodes a goal specification into a numerical vector.
    """

    vector = []

    for feature in FEATURES:

        if feature in goal:
            vector.append(1)
        else:
            vector.append(0)

    return np.array(vector, dtype=float)


# ---------------------------------------------------------
# 5. ENCODE CAPABILITY
# ---------------------------------------------------------

def encode_capability(capability):
    """
    Converts a capability into a numerical vector.

    The vector contains:

    1. Capability type
    2. Inputs
    3. Outputs
    4. Preconditions
    5. Effects
    6. Resources
    7. Cost
    8. Reliability
    9. Availability
    """

    vector = []

    # -----------------------------------------------------
    # Capability type
    # -----------------------------------------------------

    capability_type = capability["type"]

    for t in CAPABILITY_TYPES:

        if t == capability_type:
            vector.append(1)
        else:
            vector.append(0)

    # -----------------------------------------------------
    # Inputs
    # -----------------------------------------------------

    for item in [
        "cart_id",
        "order_id",
        "payment_id",
        "notification_id",
        "sales_data"
    ]:

        if item in capability["inputs"]:
            vector.append(1)
        else:
            vector.append(0)

    # -----------------------------------------------------
    # Outputs
    # -----------------------------------------------------

    for item in [
        "order_id",
        "payment_id",
        "notification_id",
        "report"
    ]:

        if item in capability["outputs"]:
            vector.append(1)
        else:
            vector.append(0)

    # -----------------------------------------------------
    # Preconditions
    # -----------------------------------------------------

    for feature in FEATURES[:12]:

        if feature in capability["preconditions"]:
            vector.append(1)
        else:
            vector.append(0)

    # -----------------------------------------------------
    # Effects
    # -----------------------------------------------------

    for feature in FEATURES[:12]:

        if feature in capability["effects"]:
            vector.append(1)
        else:
            vector.append(0)

    # -----------------------------------------------------
    # Resources
    # -----------------------------------------------------

    resources = [
        "Database",
        "Authentication token",
        "Payment gateway",
        "Network",
        "External service",
        "User interface",
        "CPU"
    ]

    for resource in resources:

        if resource in capability["resources"]:
            vector.append(1)
        else:
            vector.append(0)

    # -----------------------------------------------------
    # Operational attributes
    # -----------------------------------------------------

    vector.append(capability["cost"])
    vector.append(capability["reliability"])
    vector.append(capability["availability"])

    return np.array(vector, dtype=float)


# ---------------------------------------------------------
# 6. COSINE SIMILARITY
# ---------------------------------------------------------

def similarity(vector1, vector2):
    """
    Calculates cosine similarity between two vectors.
    """

    denominator = (
        np.linalg.norm(vector1) *
        np.linalg.norm(vector2)
    )

    if denominator == 0:
        return 0.0

    return np.dot(vector1, vector2) / denominator


# ---------------------------------------------------------
# 7. PRECONDITION-EFFECT COMPATIBILITY
# ---------------------------------------------------------

def compatibility(capability1, capability2):
    """
    Checks whether capability1 can be followed by capability2.

    Compatibility is based on whether the effects of
    capability1 satisfy the preconditions of capability2.
    """

    effects = set(capability1["effects"])
    preconditions = set(capability2["preconditions"])

    # If capability 2 has no preconditions,
    # it can be executed after capability 1.
    if len(preconditions) == 0:
        return 1.0

    matched = effects.intersection(preconditions)

    score = len(matched) / len(preconditions)

    return score


# ---------------------------------------------------------
# 8. INPUT-OUTPUT COMPATIBILITY
# ---------------------------------------------------------

def input_output_compatibility(capability1, capability2):
    """
    Checks whether outputs of capability1 can satisfy
    inputs of capability2.
    """

    outputs = set(capability1["outputs"])
    inputs = set(capability2["inputs"])

    if len(inputs) == 0:
        return 1.0

    matched = outputs.intersection(inputs)

    return len(matched) / len(inputs)


# ---------------------------------------------------------
# 9. COMPOSE CAPABILITIES
# ---------------------------------------------------------

def compose(capabilities):
    """
    Creates a composite capability from multiple
    atomic capabilities.
    """

    if len(capabilities) == 0:
        return None

    composite = {
        "name": "CompositeCapability",

        "type": "COMPOSITE",

        "inputs": [],

        "outputs": [],

        "preconditions": [],

        "effects": [],

        "constraints": [],

        "resources": [],

        "cost": 0.0,

        "reliability": 1.0,

        "availability": 1
    }

    # -----------------------------------------------------
    # Combine all capabilities
    # -----------------------------------------------------

    for capability in capabilities:

        # Inputs
        composite["inputs"].extend(
            capability["inputs"]
        )

        # Outputs
        composite["outputs"].extend(
            capability["outputs"]
        )

        # Preconditions
        composite["preconditions"].extend(
            capability["preconditions"]
        )

        # Effects
        composite["effects"].extend(
            capability["effects"]
        )

        # Constraints
        composite["constraints"].extend(
            capability["constraints"]
        )

        # Resources
        composite["resources"].extend(
            capability["resources"]
        )

        # Cost
        composite["cost"] += capability["cost"]

        # Reliability
        composite["reliability"] *= capability["reliability"]

        # Availability
        composite["availability"] *= capability["availability"]

    # Remove duplicates
    composite["inputs"] = list(
        set(composite["inputs"])
    )

    composite["outputs"] = list(
        set(composite["outputs"])
    )

    composite["preconditions"] = list(
        set(composite["preconditions"])
    )

    composite["effects"] = list(
        set(composite["effects"])
    )

    composite["constraints"] = list(
        set(composite["constraints"])
    )

    composite["resources"] = list(
        set(composite["resources"])
    )

    return composite