"""
PCCST503 Assignment 2
Problem-specific vector embedding for capability composition.

The representation is deliberately structured rather than text-only.
It encodes formal inputs, outputs, preconditions, effects, resources,
execution mechanism, functional identity and operational attributes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Union
import numpy as np


# ---------------------------------------------------------------------
# Formal application entities
# ---------------------------------------------------------------------

@dataclass
class State:
    values: Dict[str, object]


@dataclass
class Goal:
    conditions: Dict[str, object]


@dataclass
class Capability:
    name: str
    cap_type: str
    inputs: List[str]
    outputs: List[str]
    preconditions: Dict[str, object]
    effects: Dict[str, object]
    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    time_cost: float = 0.0
    resource_cost: float = 0.0
    money_cost: float = 0.0
    risk: float = 0.0
    reliability: float = 1.0
    availability: float = 1.0
    mechanism: str = "FUNCTION"


# ---------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------

VOCAB = [
    # State / predicate tokens
    "user_authenticated", "customer_exists", "cart_exists",
    "cart_nonempty", "inventory_available", "order_exists",
    "order_created", "payment_success", "payment_started",
    "notification_sent", "cart_cancelled", "order_cancelled",
    "profile_updated",

    # Data / I/O
    "cart_id", "order_id", "payment_id", "message", "customer_id",

    # Resources
    "database", "network", "payment_gateway",
    "authentication_token", "filesystem", "email_service",

    # Capability type / mechanism
    "api", "database_type", "gui", "event", "function",
    "file", "computation", "message", "service",

    # Functional tokens
    "create", "payment", "cancel", "notify", "update",
    "order", "cart", "profile",

    # Generic symbolic values
    "true", "false", "customer", "admin"
]

INDEX = {token: i for i, token in enumerate(VOCAB)}


def _normalise_token(value: object) -> str:
    return str(value).strip().lower().replace(".", "_").replace("-", "_").replace(" ", "_")


def _one_hot(tokens: Sequence[str]) -> np.ndarray:
    vector = np.zeros(len(VOCAB), dtype=float)
    for token in tokens:
        token = _normalise_token(token)
        if token in INDEX:
            vector[INDEX[token]] += 1.0
    return vector


def _dict_tokens(data: Dict[str, object]) -> List[str]:
    tokens = []
    for key, value in data.items():
        tokens.append(_normalise_token(key))
        tokens.append(_normalise_token(value))
    return tokens


def _list_tokens(values: Sequence[str]) -> List[str]:
    return [_normalise_token(v) for v in values]


def encode_state(state: State) -> np.ndarray:
    """Encode a formal application state."""
    return _one_hot(_dict_tokens(state.values))


def encode_goal(goal: Goal) -> np.ndarray:
    """Encode a formal goal specification."""
    return _one_hot(_dict_tokens(goal.conditions))


def _functional_tokens(capability: Capability) -> List[str]:
    """Derive lightweight function tokens from the capability name."""
    name = _normalise_token(capability.name)
    tokens = [name]

    for word in ("create", "payment", "cancel", "notify", "update",
                 "order", "cart", "profile"):
        if word in name:
            tokens.append(word)

    return tokens


def encode_capability(capability: Capability) -> np.ndarray:
    """
    Encode a capability into a fixed-length vector.

    Vector groups:
        1. function/identity
        2. inputs
        3. outputs
        4. preconditions
        5. effects
        6. constraints
        7. resources
        8. mechanism/type
        9. operational attributes

    The final five operational values are:
        normalised time cost
        normalised resource cost
        normalised money cost
        risk
        reliability
        availability

    The operational values are appended directly because they are numeric
    quantities rather than symbolic predicates.
    """
    symbolic = []

    symbolic += _functional_tokens(capability)
    symbolic += _list_tokens(capability.inputs)
    symbolic += _list_tokens(capability.outputs)
    symbolic += _dict_tokens(capability.preconditions)
    symbolic += _dict_tokens(capability.effects)
    symbolic += _list_tokens(capability.constraints)
    symbolic += _list_tokens(capability.resources)
    symbolic += [_normalise_token(capability.cap_type)]
    symbolic += [_normalise_token(capability.mechanism)]

    base = _one_hot(symbolic)

    operational = np.array([
        capability.time_cost,
        capability.resource_cost,
        capability.money_cost,
        capability.risk,
        capability.reliability,
        capability.availability,
    ], dtype=float)

    # Operational attributes are scaled so that costs do not dominate
    # the symbolic representation. In the demonstration dataset the
    # values are already small.
    operational[:3] = operational[:3] / 10.0

    return np.concatenate([base, operational])


def encode(entity: Union[State, Goal, Capability]) -> np.ndarray:
    """Generic encoder required by the assignment interface."""
    if isinstance(entity, State):
        return encode_state(entity)
    if isinstance(entity, Goal):
        return encode_goal(entity)
    if isinstance(entity, Capability):
        return encode_capability(entity)
    raise TypeError("Unsupported entity type")


# ---------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------

def cosine_similarity(x: np.ndarray, y: np.ndarray) -> float:
    """Return cosine similarity in [-1, 1]."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    denominator = np.linalg.norm(x) * np.linalg.norm(y)

    if denominator == 0:
        return 0.0

    return float(np.dot(x, y) / denominator)


def similarity(x: Union[np.ndarray, Capability],
               y: Union[np.ndarray, Capability]) -> float:
    """Compare two encoded vectors or capabilities."""
    if isinstance(x, Capability):
        x = encode_capability(x)
    if isinstance(y, Capability):
        y = encode_capability(y)
    return cosine_similarity(x, y)


# ---------------------------------------------------------------------
# Compatibility
# ---------------------------------------------------------------------

def _condition_matches(effect_value: object, required_value: object) -> bool:
    return _normalise_token(effect_value) == _normalise_token(required_value)


def precondition_effect_score(first: Capability,
                              second: Capability) -> float:
    """
    Fraction of second's preconditions satisfied by first's effects.

    This is the central functional compatibility signal.
    """
    if not second.preconditions:
        return 1.0

    satisfied = 0
    for key, required in second.preconditions.items():
        if key in first.effects and _condition_matches(first.effects[key], required):
            satisfied += 1

    return satisfied / len(second.preconditions)


def input_output_score(first: Capability,
                       second: Capability) -> float:
    """Fraction of second's inputs supplied by first's outputs."""
    if not second.inputs:
        return 1.0

    produced = set(_list_tokens(first.outputs))
    required = set(_list_tokens(second.inputs))

    if not required:
        return 1.0

    return len(produced.intersection(required)) / len(required)


def resource_score(first: Capability,
                   second: Capability) -> float:
    """
    A lightweight resource compatibility score.

    Resource overlap is treated as a positive signal, but not as a
    requirement for composition.
    """
    if not second.resources:
        return 1.0

    first_resources = set(_list_tokens(first.resources))
    second_resources = set(_list_tokens(second.resources))

    if not second_resources:
        return 1.0

    overlap = len(first_resources.intersection(second_resources))
    return overlap / len(second_resources)


def compatibility(first: Capability,
                   second: Capability) -> float:
    """
    Functional composition compatibility in [0, 1].

    Preconditions/effects receive the strongest weight because the
    assignment defines composition through state transition compatibility.
    Input/output compatibility is the second major signal.
    """
    pe = precondition_effect_score(first, second)
    io = input_output_score(first, second)
    rs = resource_score(first, second)

    score = 0.60 * pe + 0.30 * io + 0.10 * rs

    # Availability and reliability are operational feasibility factors.
    score *= first.availability * second.availability
    score *= (0.5 + 0.5 * first.reliability)
    score *= (0.5 + 0.5 * second.reliability)

    return float(np.clip(score, 0.0, 1.0))


# ---------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------

def compose(capabilities: Sequence[Capability]) -> Capability:
    """
    Construct a composite capability from an ordered sequence.

    The function checks adjacent compatibility before composing.
    Effects are accumulated in execution order. Outputs are the union
    of component outputs, while inputs are inputs not already produced
    by earlier capabilities.
    """
    capabilities = list(capabilities)

    if not capabilities:
        raise ValueError("At least one capability is required")

    for first, second in zip(capabilities, capabilities[1:]):
        if precondition_effect_score(first, second) < 1.0:
            raise ValueError(
                f"Incompatible composition: {first.name} -> {second.name}"
            )

    name = "Composite(" + " -> ".join(c.name for c in capabilities) + ")"

    inputs = []
    produced_so_far = set()

    for cap in capabilities:
        for item in cap.inputs:
            if item not in produced_so_far and item not in inputs:
                inputs.append(item)
        produced_so_far.update(cap.outputs)

    outputs = []
    for cap in capabilities:
        for item in cap.outputs:
            if item not in outputs:
                outputs.append(item)

    preconditions = dict(capabilities[0].preconditions)
    effects = {}
    constraints = []
    resources = []

    for cap in capabilities:
        effects.update(cap.effects)
        constraints.extend(cap.constraints)
        for resource in cap.resources:
            if resource not in resources:
                resources.append(resource)

    return Capability(
        name=name,
        cap_type="COMPOSITE",
        inputs=inputs,
        outputs=outputs,
        preconditions=preconditions,
        effects=effects,
        constraints=constraints,
        resources=resources,
        time_cost=sum(c.time_cost for c in capabilities),
        resource_cost=sum(c.resource_cost for c in capabilities),
        money_cost=sum(c.money_cost for c in capabilities),
        risk=min(1.0, sum(c.risk for c in capabilities)),
        reliability=float(np.prod([c.reliability for c in capabilities])),
        availability=float(np.prod([c.availability for c in capabilities])),
        mechanism="COMPOSITION",
    )


# ---------------------------------------------------------------------
# Goal relevance
# ---------------------------------------------------------------------

def goal_relevance(capability: Capability, goal: Goal) -> float:
    """
    Fraction of goal conditions directly produced by the capability.
    """
    if not goal.conditions:
        return 0.0

    matches = 0
    for key, required in goal.conditions.items():
        if key in capability.effects and _condition_matches(capability.effects[key], required):
            matches += 1

    return matches / len(goal.conditions)


# ---------------------------------------------------------------------
# Example application
# ---------------------------------------------------------------------

def example_application():
    initial_state = State({
        "User.authenticated": True,
        "User.role": "CUSTOMER",
        "Cart.exists": True,
        "Cart.item_count": 3,
        "Order.exists": False,
        "Payment.status": "NOT_STARTED",
        "Inventory.available": True,
        "Notification.sent": False,
    })

    goal = Goal({
        "Order.exists": True,
        "Payment.status": "SUCCESS",
        "Notification.sent": True,
    })

    create_order = Capability(
        name="CreateOrder",
        cap_type="API",
        inputs=["cart_id"],
        outputs=["order_id"],
        preconditions={
            "Cart.exists": True,
            "Cart.item_count": 3,
            "Inventory.available": True,
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED",
        },
        constraints=["quantity > 0"],
        resources=["database", "network"],
        time_cost=0.10,
        resource_cost=1.0,
        money_cost=0.01,
        risk=0.05,
        reliability=0.99,
        availability=0.99,
        mechanism="POST /orders",
    )

    make_payment = Capability(
        name="MakePayment",
        cap_type="API",
        inputs=["order_id"],
        outputs=["payment_id"],
        preconditions={
            "Order.exists": True,
        },
        effects={
            "Payment.status": "SUCCESS",
        },
        constraints=["payment_amount <= transaction_limit"],
        resources=["payment_gateway", "network"],
        time_cost=0.30,
        resource_cost=2.0,
        money_cost=0.20,
        risk=0.10,
        reliability=0.98,
        availability=0.98,
        mechanism="POST /payments",
    )

    send_notification = Capability(
        name="SendNotification",
        cap_type="SERVICE",
        inputs=["order_id"],
        outputs=["message"],
        preconditions={
            "Payment.status": "SUCCESS",
        },
        effects={
            "Notification.sent": True,
        },
        resources=["network", "email_service"],
        time_cost=0.05,
        resource_cost=0.5,
        money_cost=0.02,
        risk=0.02,
        reliability=0.995,
        availability=0.99,
        mechanism="EMAIL_SERVICE",
    )

    cancel_cart = Capability(
        name="CancelCart",
        cap_type="API",
        inputs=["cart_id"],
        outputs=["cart_id"],
        preconditions={
            "Order.exists": False,
        },
        effects={
            "Cart.cancelled": True,
        },
        resources=["database"],
        time_cost=0.08,
        resource_cost=1.0,
        money_cost=0.00,
        risk=0.04,
        reliability=0.99,
        availability=0.99,
        mechanism="POST /cart/cancel",
    )

    update_profile = Capability(
        name="UpdateProfile",
        cap_type="DATABASE",
        inputs=["customer_id"],
        outputs=["customer_id"],
        preconditions={
            "User.authenticated": True,
        },
        effects={
            "Profile.updated": True,
        },
        resources=["database"],
        time_cost=0.20,
        resource_cost=1.0,
        money_cost=0.00,
        risk=0.03,
        reliability=0.99,
        availability=0.99,
        mechanism="UPDATE customer_profile",
    )

    # Alternative implementations: same functional effect, different mechanisms.
    create_order_db = Capability(
        name="CreateOrderDatabase",
        cap_type="DATABASE",
        inputs=["cart_id"],
        outputs=["order_id"],
        preconditions={
            "Cart.exists": True,
            "Cart.item_count": 3,
            "Inventory.available": True,
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED",
        },
        resources=["database"],
        time_cost=0.07,
        resource_cost=1.0,
        money_cost=0.00,
        risk=0.03,
        reliability=0.995,
        availability=0.99,
        mechanism="INSERT orders",
    )

    create_order_gui = Capability(
        name="CreateOrderGUI",
        cap_type="GUI",
        inputs=["cart_id"],
        outputs=["order_id"],
        preconditions={
            "Cart.exists": True,
            "Cart.item_count": 3,
            "Inventory.available": True,
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED",
        },
        resources=["network"],
        time_cost=0.50,
        resource_cost=1.0,
        money_cost=0.00,
        risk=0.08,
        reliability=0.95,
        availability=0.98,
        mechanism="CLICK submit_button",
    )

    return {
        "initial_state": initial_state,
        "goal": goal,
        "CreateOrder": create_order,
        "MakePayment": make_payment,
        "SendNotification": send_notification,
        "CancelCart": cancel_cart,
        "UpdateProfile": update_profile,
        "CreateOrderDatabase": create_order_db,
        "CreateOrderGUI": create_order_gui,
    }


if __name__ == "__main__":
    app = example_application()

    create = app["CreateOrder"]
    payment = app["MakePayment"]
    notify = app["SendNotification"]

    print("CreateOrder vector dimension:", len(encode_capability(create)))
    print("CreateOrder -> MakePayment compatibility:",
          round(compatibility(create, payment), 4))
    print("CreateOrder -> CancelCart compatibility:",
          round(compatibility(create, app["CancelCart"]), 4))

    composite = compose([create, payment, notify])
    print("Composite:", composite.name)
    print("Composite reliability:", round(composite.reliability, 4))
    print("Goal relevance:", round(goal_relevance(composite, app["goal"]), 4))
