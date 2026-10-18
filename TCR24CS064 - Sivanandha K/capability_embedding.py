import numpy as np


# ---------------------------------------------------------
# Feature vocabulary
# ---------------------------------------------------------

FEATURES = [
    # Capability types
    "type_API",
    "type_DATABASE",
    "type_GUI",
    "type_EVENT",
    "type_FUNCTION",
    "type_FILE",
    "type_COMPUTATION",
    "type_MESSAGE",
    "type_SERVICE",

    # Inputs
    "input_cart_id",
    "input_order_id",
    "input_payment_id",
    "input_quantity",
    "input_customer_id",

    # Outputs
    "output_order_id",
    "output_payment_id",
    "output_notification",
    "output_order_status",
    "output_payment_status",

    # Preconditions
    "precondition_authenticated",
    "precondition_cart_exists",
    "precondition_order_exists",
    "precondition_order_not_exists",
    "precondition_payment_pending",
    "precondition_cart_items",
    "precondition_payment_success",

    # Effects
    "effect_order_exists",
    "effect_order_created",
    "effect_payment_success",
    "effect_notification_sent",
    "effect_cart_cancelled",

    # Resources
    "resource_database",
    "resource_network",
    "resource_payment_gateway",
    "resource_authentication",
    "resource_filesystem",

    # Execution mechanisms
    "mechanism_POST",
    "mechanism_INSERT",
    "mechanism_CLICK",
    "mechanism_EVENT",

    # Operational features
    "cost",
    "risk",
    "reliability",
    "availability"
]


FEATURE_INDEX = {
    feature: index
    for index, feature in enumerate(FEATURES)
}


# ---------------------------------------------------------
# Capability class
# ---------------------------------------------------------

class Capability:

    def __init__(
        self,
        name,
        capability_type,
        inputs,
        outputs,
        preconditions,
        effects,
        resources,
        mechanism,
        cost,
        risk,
        reliability,
        availability
    ):

        self.name = name
        self.capability_type = capability_type
        self.inputs = inputs
        self.outputs = outputs
        self.preconditions = preconditions
        self.effects = effects
        self.resources = resources
        self.mechanism = mechanism

        self.cost = cost
        self.risk = risk
        self.reliability = reliability
        self.availability = availability


# ---------------------------------------------------------
# Helper function
# ---------------------------------------------------------

def set_feature(vector, feature, value=1.0):

    if feature in FEATURE_INDEX:
        vector[FEATURE_INDEX[feature]] = value


# ---------------------------------------------------------
# Encode capability
# ---------------------------------------------------------

def encode_capability(capability):

    vector = np.zeros(len(FEATURES))

    # Capability type
    set_feature(
        vector,
        "type_" + capability.capability_type
    )

    # Inputs
    for item in capability.inputs:
        set_feature(vector, "input_" + item)

    # Outputs
    for item in capability.outputs:
        set_feature(vector, "output_" + item)

    # Preconditions
    for item in capability.preconditions:
        set_feature(vector, "precondition_" + item)

    # Effects
    for item in capability.effects:
        set_feature(vector, "effect_" + item)

    # Resources
    for item in capability.resources:
        set_feature(vector, "resource_" + item)

    # Execution mechanism
    if capability.mechanism:
        set_feature(
            vector,
            "mechanism_" + capability.mechanism
        )

    # Operational attributes
    set_feature(vector, "cost", capability.cost)
    set_feature(vector, "risk", capability.risk)
    set_feature(vector, "reliability", capability.reliability)
    set_feature(vector, "availability", capability.availability)

    return vector


# ---------------------------------------------------------
# Encode state
# ---------------------------------------------------------

def encode_state(state):

    vector = np.zeros(len(FEATURES))

    for key, value in state.items():

        feature_name = "effect_" + key

        if value is True:
            set_feature(vector, feature_name, 1.0)

    return vector


# ---------------------------------------------------------
# Encode goal
# ---------------------------------------------------------

def encode_goal(goal):

    vector = np.zeros(len(FEATURES))

    for key, value in goal.items():

        feature_name = "effect_" + key

        if value is True:
            set_feature(vector, feature_name, 1.0)

    return vector


# ---------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------

def similarity(vector_a, vector_b):

    denominator = (
        np.linalg.norm(vector_a) *
        np.linalg.norm(vector_b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(vector_a, vector_b) / denominator
    )


# ---------------------------------------------------------
# Functional compatibility
# ---------------------------------------------------------

def compatibility(capability_a, capability_b):

    # Outputs and effects produced by capability A
    produced_outputs = set(capability_a.outputs)
    produced_effects = set(capability_a.effects)

    # Inputs and preconditions required by capability B
    required_inputs = set(capability_b.inputs)
    required_preconditions = set(capability_b.preconditions)

    # Check input-output compatibility
    inputs_satisfied = required_inputs.issubset(
        produced_outputs
    )

    # Check precondition-effect compatibility
    preconditions_satisfied = required_preconditions.issubset(
        produced_effects
    )

    # Both conditions must be satisfied
    if inputs_satisfied and preconditions_satisfied:
        return 1.0

    return 0.0


# ---------------------------------------------------------
# Compose capabilities
# ---------------------------------------------------------

def compose(capabilities):

    if len(capabilities) == 0:
        raise ValueError("At least one capability is required.")

    first = capabilities[0]

    composite_name = "CompositeCapability"

    all_inputs = []
    all_outputs = []
    all_preconditions = []
    all_effects = []
    all_resources = []

    total_cost = 0.0
    total_risk = 0.0
    total_reliability = 1.0
    total_availability = 1.0

    for capability in capabilities:

        for item in capability.inputs:
            if item not in all_inputs:
                all_inputs.append(item)

        for item in capability.outputs:
            if item not in all_outputs:
                all_outputs.append(item)

        for item in capability.preconditions:
            if item not in all_preconditions:
                all_preconditions.append(item)

        for item in capability.effects:
            if item not in all_effects:
                all_effects.append(item)

        for item in capability.resources:
            if item not in all_resources:
                all_resources.append(item)

        total_cost += capability.cost
        total_risk += capability.risk

        total_reliability *= capability.reliability
        total_availability *= capability.availability

    total_risk = min(total_risk, 1.0)

    return Capability(
        composite_name,
        first.capability_type,
        all_inputs,
        all_outputs,
        all_preconditions,
        all_effects,
        all_resources,
        first.mechanism,
        total_cost,
        total_risk,
        total_reliability,
        total_availability
    )
