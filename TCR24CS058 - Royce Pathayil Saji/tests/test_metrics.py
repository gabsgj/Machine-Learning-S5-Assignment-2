from __future__ import annotations

import numpy as np
import pytest

from src.models import (
    Capability,
    CapabilityType,
    Constraint,
    Goal,
    IOField,
    OperationalCost,
    Predicate,
    Resource,
)
from src.encoder import encode_capability, encode_goal
from src.metrics import (
    BLOCK_WEIGHTS,
    cosine_similarity,
    effect_precondition_alignment,
    goal_relevance,
    output_input_alignment,
    similarity,
    validate_compatibility,
    vector_compatibility,
)


def test_cosine_similarity_edge_cases():
    # Identical
    a = np.array([1.0, 2.0, 3.0])
    assert abs(cosine_similarity(a, a) - 1.0) < 1e-6

    # Opposite
    b = -a
    assert abs(cosine_similarity(a, b) - (-1.0)) < 1e-6

    # Orthogonal
    c1 = np.array([1.0, 0.0])
    c2 = np.array([0.0, 1.0])
    assert abs(cosine_similarity(c1, c2) - 0.0) < 1e-6

    # Both zero
    z1 = np.zeros(5)
    z2 = np.zeros(5)
    assert cosine_similarity(z1, z2) == 1.0

    # One zero
    assert cosine_similarity(z1, a) == 0.0
    assert cosine_similarity(a, z1) == 0.0


def test_similarity_weights_sum_to_one():
    assert abs(sum(BLOCK_WEIGHTS.values()) - 1.0) < 1e-9


def test_similarity_is_symmetric():
    c1 = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
    )
    c2 = Capability(
        id="C2",
        name="MakePayment",
        T=CapabilityType.API,
        I=[IOField(name="order_id", type="UUID")],
        O=[IOField(name="payment_id", type="UUID")],
        P=[Predicate(name="Order.exists", operator="=", value=True)],
        E=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
    )

    sim_1_2 = similarity(c1, c2)
    sim_2_1 = similarity(c2, c1)
    assert abs(sim_1_2 - sim_2_1) < 1e-9

    # Identical capability similarity should be 1.0
    assert abs(similarity(c1, c1) - 1.0) < 1e-6

    # Different capabilities have lower similarity
    assert sim_1_2 < 1.0


def test_compatibility_create_order_to_make_payment_passes():
    create_order = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
        Rel=0.99,
        A=1.0,
    )
    make_payment = Capability(
        id="C2",
        name="MakePayment",
        T=CapabilityType.API,
        I=[IOField(name="order_id", type="UUID", required=True)],
        O=[IOField(name="payment_id", type="UUID")],
        P=[Predicate(name="Order.exists", operator="=", value=True)],
        E=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
        Rel=0.97,
        A=1.0,
    )

    score = vector_compatibility(create_order, make_payment)
    assert score.effect_precondition == 1.0
    assert score.output_input == 1.0
    assert score.vector_score == 1.0
    assert score.execution_score == 1.0

    result = validate_compatibility(create_order, make_payment)
    assert result.compatible is True
    assert len(result.reasons) == 0


def test_compatibility_create_order_to_cancel_cart_contradiction():
    create_order = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
    )
    cancel_cart = Capability(
        id="C3",
        name="CancelCart",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="cancelled_cart_id", type="UUID")],
        P=[Predicate(name="Order.exists", operator="=", value=False)],
        E=[Predicate(name="Cart.status", operator="=", value="CANCELLED")],
    )

    score = vector_compatibility(create_order, cancel_cart)
    # Effect Order.exists=true vs Precondition Order.exists=false aligns to -1.0
    assert score.effect_precondition == -1.0
    assert score.vector_score < 0.70

    result = validate_compatibility(create_order, cancel_cart)
    assert result.compatible is False
    assert any("contradicted" in r for r in result.reasons)


def test_compatibility_is_directional():
    create_order = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
    )
    make_payment = Capability(
        id="C2",
        name="MakePayment",
        T=CapabilityType.API,
        I=[IOField(name="order_id", type="UUID")],
        O=[IOField(name="payment_id", type="UUID")],
        P=[Predicate(name="Order.exists", operator="=", value=True)],
        E=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
    )

    fwd = vector_compatibility(create_order, make_payment)
    rev = vector_compatibility(make_payment, create_order)

    assert fwd.execution_score == 1.0
    # Reverse MakePayment -> CreateOrder: MakePayment has no cart_id output and no Cart.exists effect
    assert rev.execution_score == 0.0
    assert rev.execution_score < fwd.execution_score


def test_input_mismatch_fails_validation():
    producer = Capability(
        id="P",
        name="Producer",
        T=CapabilityType.API,
        O=[IOField(name="order_id", type="UUID")],
    )
    consumer = Capability(
        id="C",
        name="Consumer",
        T=CapabilityType.API,
        I=[IOField(name="secret_token", type="STRING", required=True)],
    )

    score = vector_compatibility(producer, consumer)
    assert score.output_input == 0.0

    result = validate_compatibility(producer, consumer)
    assert result.compatible is False
    assert any("is not produced" in r for r in result.reasons)


def test_goal_relevance_ranking():
    goal = Goal(
        id="G",
        conditions=[
            Predicate("Order.exists", "=", True),
            Predicate("Payment.status", "=", "SUCCESS"),
            Predicate("Notification.sent", "=", True),
        ],
    )

    c_order = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        E=[Predicate("Order.exists", "=", True)],
    )
    c_payment = Capability(
        id="C2",
        name="MakePayment",
        T=CapabilityType.API,
        E=[Predicate("Payment.status", "=", "SUCCESS")],
    )
    c_notify = Capability(
        id="C3",
        name="SendNotification",
        T=CapabilityType.EVENT,
        E=[Predicate("Notification.sent", "=", True)],
    )
    c_unrelated = Capability(
        id="C4",
        name="ArchiveOrder",
        T=CapabilityType.DATABASE,
        E=[Predicate("Order.archived", "=", True)],
    )
    c_contradictory = Capability(
        id="C5",
        name="CancelOrder",
        T=CapabilityType.API,
        E=[Predicate("Order.exists", "=", False)],
    )

    rel_order = goal_relevance(c_order, goal)
    rel_payment = goal_relevance(c_payment, goal)
    rel_notify = goal_relevance(c_notify, goal)
    rel_unrelated = goal_relevance(c_unrelated, goal)
    rel_contradictory = goal_relevance(c_contradictory, goal)

    # Useful capabilities must have positive relevance
    assert rel_order > 0.0
    assert rel_payment > 0.0
    assert rel_notify > 0.0

    # Unrelated capability has 0 relevance
    assert rel_unrelated == 0.0

    # Contradictory capability has 0 relevance
    assert rel_contradictory == 0.0

    # Useful capabilities rank strictly higher than unrelated/contradictory
    assert rel_order > rel_unrelated
    assert rel_payment > rel_unrelated


def test_zero_vector_edge_cases():
    c_empty_pre = Capability(id="E1", name="NoPre", T=CapabilityType.FUNCTION, P=[])
    c_empty_in = Capability(id="E2", name="NoIn", T=CapabilityType.FUNCTION, I=[])
    c_with_effects = Capability(
        id="E3",
        name="WithEffects",
        T=CapabilityType.FUNCTION,
        E=[Predicate("Order.exists", "=", True)],
    )

    # Empty consumer preconditions yields 1.0 alignment
    assert effect_precondition_alignment(c_with_effects, c_empty_pre) == 1.0

    # Empty consumer inputs yields 1.0 alignment
    assert output_input_alignment(c_with_effects, c_empty_in) == 1.0

    # Empty goal yields 0.0 relevance
    empty_goal = Goal(id="G_empty", conditions=[])
    assert goal_relevance(c_with_effects, empty_goal) == 0.0


def test_availability_gating():
    c_avail = Capability(
        id="C1",
        name="Available",
        T=CapabilityType.API,
        O=[IOField(name="order_id", type="UUID")],
        E=[Predicate("Order.exists", "=", True)],
        A=1.0,
    )
    c_unavail = Capability(
        id="C2",
        name="Unavailable",
        T=CapabilityType.API,
        I=[IOField(name="order_id", type="UUID")],
        P=[Predicate("Order.exists", operator="=", value=True)],
        A=0.0,
    )

    score = vector_compatibility(c_avail, c_unavail)
    assert score.vector_score == 1.0
    assert score.availability_factor == 0.0
    assert score.execution_score == 0.0

    result = validate_compatibility(c_avail, c_unavail)
    assert result.compatible is False
    assert any("unavailable" in r.lower() for r in result.reasons)
